"""
전체 시황(종목 무관) 생성 오케스트레이션. briefing_pipeline.py와 같은 구조를
따르되, 대상이 특정 종목이 아니라 시장 전체다.

Finnhub 무료 티어는 지수 시세(나스닥 등)를 안 주므로("Market data subscription
required" 에러), 일반 시장 뉴스(get_general_news)만으로 정성적 요약을 만든다 —
지수 등락률 "수치"는 절대 지어내지 않는다(claude_client.py MARKET_SYSTEM_PROMPT).

market_overviews.UNIQUE(briefing_date)가 "하루에 한 행"을 보장하고, 그 행이
REFRESH_INTERVAL_HOURS보다 오래되면 같은 행을 갱신한다 — briefing_pipeline.py와
동일한 신선도 전략(app/services/freshness.py 공유).
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.briefing import MarketOverview
from app.schemas.llm import MarketOverviewRender
from app.services.finnhub_client import FinnhubClient, FinnhubError
from app.services.freshness import is_fresh
from app.services.llm import get_llm_client


def _build_market_document_text(articles: list[dict], limit: int = 20) -> str:
    """Finnhub 일반 뉴스(dict 목록)를 한 문서로 뭉친다. 상위 limit건만 사용(토큰 비용 통제)."""
    if not articles:
        return ""
    lines = []
    for a in articles[:limit]:
        headline = a.get("headline") or ""
        source = a.get("source") or "출처 미상"
        summary = a.get("summary") or ""
        url = a.get("url") or ""
        lines.append(f"- {headline} ({source})\n  {summary}\n  URL: {url}")
    return "\n".join(lines)


def _fetch_general_news() -> list[dict]:
    """Finnhub 호출 실패(키 없음/네트워크 오류)해도 파이프라인 전체가 죽지 않도록 빈 목록으로 대체."""
    try:
        with FinnhubClient() as client:
            return client.get_general_news()
    except FinnhubError:
        return []


def _apply_render(overview: MarketOverview, render: MarketOverviewRender, model_name: str) -> None:
    overview.summary = render.summary
    overview.indices = render.indices
    overview.sector_moves = render.sector_moves
    overview.model = model_name


def generate_market_overview(db: Session, briefing_date: date | None = None, force: bool = False) -> MarketOverview:
    briefing_date = briefing_date or date.today()

    cached = db.scalar(select(MarketOverview).where(MarketOverview.briefing_date == briefing_date))
    if cached and not force and is_fresh(db, cached.generated_at, settings.REFRESH_INTERVAL_HOURS):
        return cached

    news = _fetch_general_news()
    llm = get_llm_client()

    facts = llm.extract_facts(
        source_type="market_news",
        tickers=[],
        document_text=_build_market_document_text(news),
    )
    render = llm.render_market_overview(facts=facts)

    if cached:
        _apply_render(cached, render, llm.model_name)
        db.commit()
        db.refresh(cached)
        return cached

    overview = MarketOverview(briefing_date=briefing_date)
    _apply_render(overview, render, llm.model_name)
    db.add(overview)
    try:
        db.commit()
    except IntegrityError:
        # 같은 briefing_date를 동시에 처음 생성하려던 다른 트랜잭션이 먼저 커밋한 경우.
        db.rollback()
        existing = db.scalar(select(MarketOverview).where(MarketOverview.briefing_date == briefing_date))
        if existing:
            return existing
        raise
    db.refresh(overview)
    return overview
