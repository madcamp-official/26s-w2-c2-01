"""
섹터별 일일 브리핑 생성 오케스트레이션. briefing_pipeline.py(종목별)와 완전히 같은
2단계 파이프라인·같은 캐싱/신선도 전략을 쓰되, 입력 뉴스만 다르다: 특정 티커 하나가
아니라 이 섹터에 속한 stocks.sector_id = X 종목들의 news_articles를 모아 하나의
문서로 합친다. 별도로 Finnhub를 다시 호출하지 않는다 — collect_news.py가 이미
관심 섹터 소속 종목까지 대상에 포함하도록 확장되어 있어(app/batch/collect_news.py
target_tickers), 여기서는 그렇게 이미 모인 news_articles를 읽기만 한다.

render_briefing()은 ticker 하나에 종속된 인터페이스가 아니라 facts(다중 티커 가능)만
보고 렌더링하므로 종목용 LLM 클라이언트 메서드를 그대로 재사용한다 — 새 프롬프트/
스키마가 필요 없다.
"""

from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.analysis import AnalysisPreset
from app.models.briefing import SectorBriefing
from app.models.news_article import NewsArticle
from app.models.sector import Sector
from app.models.stock import Stock
from app.schemas.llm import BriefingRender
from app.services.briefing_sanitizer import sanitize_briefing_render
from app.services.freshness import is_fresh
from app.services.llm import get_llm_client
from app.services.market_sessions import BriefingSession, current_briefing_date, current_session
from app.services.news_document import format_news_article
from app.services.news_relevance import select_persisted_relevant_articles


def _build_document_text(articles: list[NewsArticle]) -> str:
    if not articles:
        return ""
    return "\n".join(format_news_article(article, include_ticker=True) for article in articles)


def _get_default_preset(db: Session) -> AnalysisPreset | None:
    return db.scalar(select(AnalysisPreset).where(AnalysisPreset.is_default.is_(True))) or db.scalar(
        select(AnalysisPreset).limit(1)
    )


def _apply_render(briefing: SectorBriefing, render: BriefingRender, model_name: str) -> None:
    render = sanitize_briefing_render(render)
    briefing.sentiment = render.sentiment
    briefing.summary = render.summary
    briefing.one_line_summary = render.one_line_summary
    briefing.positive_factors = render.positive_factors
    briefing.negative_factors = render.negative_factors
    briefing.watch_issues = render.watch_issues
    briefing.reasons = [r.model_dump() for r in render.reasons]
    briefing.today_actions = render.today_actions
    briefing.model = model_name


def generate_sector_briefing(
    db: Session,
    sector_id: int,
    briefing_date: date | None = None,
    news_lookback_days: int = 2,
    force: bool = False,
    briefing_session: BriefingSession | None = None,
) -> SectorBriefing:
    briefing_date = briefing_date or current_briefing_date()
    briefing_session = briefing_session or current_session(briefing_date)

    cached = db.scalar(
        select(SectorBriefing).where(
            SectorBriefing.sector_id == sector_id,
            SectorBriefing.briefing_date == briefing_date,
            SectorBriefing.briefing_session == briefing_session,
        )
    )
    if (
        cached
        and cached.one_line_summary
        and not force
        and is_fresh(db, cached.generated_at, settings.REFRESH_INTERVAL_HOURS)
    ):
        return cached

    sector = db.get(Sector, sector_id)
    if not sector:
        raise ValueError(f"등록되지 않은 섹터입니다: {sector_id}")

    sector_stocks = list(db.scalars(select(Stock).where(Stock.sector_id == sector_id)).all())
    tickers = [stock.ticker for stock in sector_stocks]

    since = datetime.combine(briefing_date - timedelta(days=news_lookback_days), datetime.min.time())
    articles = list(
        db.scalars(
            select(NewsArticle)
            .where(NewsArticle.ticker.in_(tickers), NewsArticle.published_at >= since)
            .order_by(NewsArticle.published_at.desc())
            .limit(100)
        ).all()
    ) if tickers else []
    if settings.ENABLE_NEWS_RELEVANCE_FILTER:
        articles = select_persisted_relevant_articles(
            articles,
            company_names_by_ticker={
                stock.ticker: [stock.name_en, stock.name_ko] for stock in sector_stocks
            },
            # Sector analysis keeps summary-only ecosystem/supply-chain coverage,
            # while individual stock briefings use the stricter configured score.
            min_score=max(3, settings.NEWS_RELEVANCE_MIN_SCORE - 1),
            limit=10,
            per_ticker_limit=2,
        )
    else:
        articles = articles[:10]

    llm = get_llm_client()

    facts = llm.extract_facts(
        source_type="news",
        tickers=tickers,
        document_text=_build_document_text(articles),
    )

    preset = _get_default_preset(db)
    render = llm.render_briefing(
        facts=facts,
        categories=[],
        preset_persona=preset.persona_text if preset else "",
        depth="standard",
        language="ko",
    )

    if cached:
        _apply_render(cached, render, llm.model_name)
        db.commit()
        db.refresh(cached)
        return cached

    briefing = SectorBriefing(
        sector_id=sector_id, briefing_date=briefing_date, briefing_session=briefing_session
    )
    _apply_render(briefing, render, llm.model_name)
    db.add(briefing)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(SectorBriefing).where(
                SectorBriefing.sector_id == sector_id,
                SectorBriefing.briefing_date == briefing_date,
                SectorBriefing.briefing_session == briefing_session,
            )
        )
        if existing:
            return existing
        raise
    db.refresh(briefing)
    return briefing
