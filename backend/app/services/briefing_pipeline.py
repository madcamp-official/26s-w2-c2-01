"""
종목별 일일 브리핑 생성 오케스트레이션 (기획서.md 6-1절 2단계 파이프라인).

news_articles 를 모아 1단계(팩트 추출) → 2단계(성향 렌더링)를 거쳐
daily_briefings 에 저장한다. UNIQUE(ticker, briefing_date) 가 캐시 키라
이미 오늘자 브리핑이 있으면 LLM을 다시 호출하지 않고 그대로 반환한다
(기획서.md 7-1절 "on-demand 보완").
"""

from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis import AnalysisPreset
from app.models.briefing import DailyBriefing
from app.models.news_article import NewsArticle
from app.models.stock import Stock
from app.services.llm import get_llm_client


def _build_document_text(articles: list[NewsArticle]) -> str:
    if not articles:
        return ""
    lines = []
    for a in articles:
        lines.append(f"- {a.title} ({a.source or '출처 미상'})\n  {a.summary or ''}\n  URL: {a.url}")
    return "\n".join(lines)


def _get_default_preset(db: Session) -> AnalysisPreset | None:
    return db.scalar(select(AnalysisPreset).where(AnalysisPreset.is_default.is_(True))) or db.scalar(
        select(AnalysisPreset).limit(1)
    )


def generate_daily_briefing(
    db: Session,
    ticker: str,
    briefing_date: date | None = None,
    news_lookback_days: int = 2,
) -> DailyBriefing:
    briefing_date = briefing_date or date.today()

    cached = db.scalar(
        select(DailyBriefing).where(DailyBriefing.ticker == ticker, DailyBriefing.briefing_date == briefing_date)
    )
    if cached:
        return cached

    stock = db.get(Stock, ticker)
    if not stock:
        raise ValueError(f"등록되지 않은 종목입니다: {ticker}")

    since = datetime.combine(briefing_date - timedelta(days=news_lookback_days), datetime.min.time())
    articles = list(
        db.scalars(
            select(NewsArticle)
            .where(NewsArticle.ticker == ticker, NewsArticle.published_at >= since)
            .order_by(NewsArticle.published_at.desc())
            .limit(10)
        ).all()
    )

    llm = get_llm_client()

    facts = llm.extract_facts(
        source_type="news",
        tickers=[ticker],
        document_text=_build_document_text(articles),
    )

    preset = _get_default_preset(db)
    render = llm.render_briefing(
        facts=facts,
        categories=[],  # TODO: 종목 섹터 기반 기본 카테고리 매핑 (커스터마이즈 렌즈 기능에서 확정)
        preset_persona=preset.persona_text if preset else "",
        depth="standard",
        language="ko",
    )

    briefing = DailyBriefing(
        ticker=ticker,
        briefing_date=briefing_date,
        sentiment=render.sentiment,
        summary=render.summary,
        positive_factors=render.positive_factors,
        negative_factors=render.negative_factors,
        watch_issues=render.watch_issues,
        reasons=[r.model_dump() for r in render.reasons],
        today_actions=render.today_actions,
        model=llm.model_name,
    )
    db.add(briefing)
    db.commit()
    db.refresh(briefing)
    return briefing
