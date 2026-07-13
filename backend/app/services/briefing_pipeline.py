"""
종목별 일일 브리핑 생성 오케스트레이션 (기획서.md 6-1절 2단계 파이프라인).

news_articles 를 모아 1단계(팩트 추출) → 2단계(성향 렌더링)를 거쳐
daily_briefings 에 저장한다. UNIQUE(ticker, briefing_date) 는 "하루에 한 행"만
보장하고, 그 행이 얼마나 최신인지는 generated_at으로 따로 판단한다:
행이 없거나 REFRESH_INTERVAL_HOURS(기본 9시간)보다 오래됐으면 LLM을 다시 불러
같은 행을 갱신하고, 그보다 최신이면 재호출 없이 그대로 반환한다
(기획서.md 7-1절 "on-demand 보완" + settings.REFRESH_INTERVAL_HOURS 확장).
"""

from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.analysis import AnalysisPreset
from app.models.briefing import DailyBriefing
from app.models.news_article import NewsArticle
from app.models.stock import Stock
from app.schemas.llm import BriefingRender
from app.services.freshness import is_fresh
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


def _apply_render(briefing: DailyBriefing, render: BriefingRender, model_name: str) -> None:
    """LLM 렌더 결과를 DailyBriefing 행에 반영한다. 신규 생성/기존 갱신 양쪽에서 공용으로 쓴다."""
    briefing.sentiment = render.sentiment
    briefing.summary = render.summary
    briefing.positive_factors = render.positive_factors
    briefing.negative_factors = render.negative_factors
    briefing.watch_issues = render.watch_issues
    briefing.reasons = [r.model_dump() for r in render.reasons]
    briefing.today_actions = render.today_actions
    briefing.model = model_name


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
    if cached and is_fresh(db, cached.generated_at, settings.REFRESH_INTERVAL_HOURS):
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

    if cached:
        # 캐시가 있지만 오래됐다(REFRESH_INTERVAL_HOURS 초과) — 새 행을 만들지 않고
        # 같은 행을 갱신한다. generated_at은 모델의 onupdate=func.now()가 자동 갱신.
        _apply_render(cached, render, llm.model_name)
        db.commit()
        db.refresh(cached)
        return cached

    briefing = DailyBriefing(ticker=ticker, briefing_date=briefing_date)
    _apply_render(briefing, render, llm.model_name)
    db.add(briefing)
    try:
        db.commit()
    except IntegrityError:
        # 같은 (ticker, briefing_date)를 동시에 처음 생성하려던 다른 트랜잭션이 먼저
        # 커밋한 경우 UNIQUE(ticker, briefing_date) 위반으로 여기 걸린다.
        # 우리가 만든 결과는 버리고, 먼저 커밋된 결과를 그대로 재사용한다.
        db.rollback()
        existing = db.scalar(
            select(DailyBriefing).where(
                DailyBriefing.ticker == ticker, DailyBriefing.briefing_date == briefing_date
            )
        )
        if existing:
            return existing
        raise  # UNIQUE 위반이 아닌 다른 원인이면 그대로 전파
    db.refresh(briefing)
    return briefing
