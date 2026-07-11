"""
초기 시드 데이터 투입 스크립트.
DB스키마.md 4절 / 분석카테고리.md 기준. 이미 데이터가 있으면 건너뛴다 (idempotent).

사용법: python -m app.seed.seed_data
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.analysis import AnalysisCategory, AnalysisPreset
from app.models.sector import Sector
from app.models.stock import Stock

SECTORS = [
    ("반도체·AI", "Semiconductors & AI"),
    ("빅테크", "Big Tech"),
    ("전기차", "EV"),
    ("금융", "Financials"),
]

# (ticker, name_ko, name_en, exchange, sector_name_ko)
STOCKS = [
    ("NVDA", "엔비디아", "NVIDIA Corp.", "NASDAQ", "반도체·AI"),
    ("AVGO", "브로드컴", "Broadcom Inc.", "NASDAQ", "반도체·AI"),
    ("AMD", "AMD", "Advanced Micro Devices", "NASDAQ", "반도체·AI"),
    ("AAPL", "애플", "Apple Inc.", "NASDAQ", "빅테크"),
    ("MSFT", "마이크로소프트", "Microsoft Corp.", "NASDAQ", "빅테크"),
    ("AMZN", "아마존", "Amazon.com Inc.", "NASDAQ", "빅테크"),
    ("GOOGL", "알파벳", "Alphabet Inc.", "NASDAQ", "빅테크"),
    ("NFLX", "넷플릭스", "Netflix Inc.", "NASDAQ", "빅테크"),
    ("META", "메타", "Meta Platforms Inc.", "NASDAQ", "빅테크"),
    ("TSLA", "테슬라", "Tesla Inc.", "NASDAQ", "전기차"),
]

# (code, name_ko, name_en, type, description)
ANALYSIS_CATEGORIES = [
    ("IXIC", "나스닥 종합", "Nasdaq Composite", "index", "기술주 중심"),
    ("SPX", "S&P 500", "S&P 500", "index", "미국 대형주 대표"),
    ("DJI", "다우존스 산업평균", "Dow Jones Industrial Average", "index", "전통 대형주 30"),
    ("RUT", "러셀 2000", "Russell 2000", "index", "중소형주"),
    ("SOX", "필라델피아 반도체지수", "PHLX Semiconductor", "index", "반도체 업황 바로미터"),
    ("VIX", "변동성 지수", "Volatility Index", "index", "시장 불안 심리"),
    ("DXY", "달러 인덱스", "US Dollar Index", "index", "달러 강·약 (환율 영향)"),
    ("FFR", "미 연준 기준금리", "Fed Funds Rate", "indicator", "통화정책의 핵심"),
    ("US10Y", "미 국채 10년물 금리", "US 10Y Treasury", "indicator", "성장주 밸류에이션에 직결"),
    ("CPI", "소비자물가지수", "CPI", "indicator", "인플레이션"),
    ("PCE", "개인소비지출 물가", "PCE Price Index", "indicator", "연준이 보는 물가"),
    ("NFP", "비농업 고용/실업률", "Nonfarm Payrolls", "indicator", "고용 = 금리 방향"),
    ("PMI", "ISM 제조·서비스 PMI", "ISM PMI", "indicator", "경기 확장/수축"),
    ("GDP", "실질 GDP 성장률", "Real GDP Growth", "indicator", "경기 체력"),
    ("FOMC", "FOMC 회의·발언", "FOMC Meeting", "indicator", "금리 결정 이벤트"),
    ("SEMI", "반도체·AI 하드웨어", "Semiconductors/AI", "sector", None),
    ("BIGTECH", "빅테크", "Big Tech", "sector", None),
    ("EV", "전기차·2차전지", "EV/Battery", "sector", None),
    ("FIN", "금융", "Financials", "sector", None),
    ("HEALTH", "헬스케어·바이오", "Healthcare/Biotech", "sector", None),
    ("ENERGY", "에너지", "Energy", "sector", None),
    ("CONSUMER", "소비재", "Consumer", "sector", None),
    ("AI_DC", "AI·데이터센터", "AI/Datacenter", "theme", None),
    ("DIVIDEND", "배당·인컴", "Dividend/Income", "theme", None),
    ("EARNINGS", "실적·밸류에이션", "Earnings/Valuation", "theme", None),
    ("GEOPOL", "지정학·원자재", "Geopolitics/Commodities", "theme", None),
    ("FX", "환율", "FX", "theme", None),
]

# (code, name_ko, persona_text, is_default)
ANALYSIS_PRESETS = [
    ("MACRO", "냉정한 거시 분석", "감정을 배제하고 금리·거시·수급 중심으로 분석한다.", False),
    ("VALUE", "장기 가치투자", "펀더멘털·밸류에이션·현금흐름 중심, 단기 노이즈는 무시한다.", True),
    ("MOMENTUM", "단기 모멘텀", "수급·모멘텀·촉매 이벤트와 단기 변동성에 주목한다.", False),
    ("FACT", "팩트 브리핑", "해석을 최소화하고 사실·수치·원문 인용만 제시한다.", False),
    ("BEGINNER", "입문자용 쉬운 설명", "용어를 풀어주고 비유로 배경부터 친절히 설명한다.", False),
]


def seed_sectors(db: Session) -> dict[str, Sector]:
    existing = {s.name_ko: s for s in db.scalars(select(Sector)).all()}
    for name_ko, name_en in SECTORS:
        if name_ko not in existing:
            sector = Sector(name_ko=name_ko, name_en=name_en)
            db.add(sector)
            existing[name_ko] = sector
    db.commit()
    return {s.name_ko: s for s in db.scalars(select(Sector)).all()}


def seed_stocks(db: Session, sectors: dict[str, Sector]) -> None:
    existing_tickers = {s.ticker for s in db.scalars(select(Stock)).all()}
    for ticker, name_ko, name_en, exchange, sector_name in STOCKS:
        if ticker in existing_tickers:
            continue
        db.add(
            Stock(
                ticker=ticker,
                name_ko=name_ko,
                name_en=name_en,
                exchange=exchange,
                sector_id=sectors[sector_name].id,
            )
        )
    db.commit()


def seed_analysis_categories(db: Session) -> None:
    existing_codes = {c.code for c in db.scalars(select(AnalysisCategory)).all()}
    for code, name_ko, name_en, type_, description in ANALYSIS_CATEGORIES:
        if code in existing_codes:
            continue
        db.add(
            AnalysisCategory(code=code, name_ko=name_ko, name_en=name_en, type=type_, description=description)
        )
    db.commit()


def seed_analysis_presets(db: Session) -> None:
    existing_codes = {p.code for p in db.scalars(select(AnalysisPreset)).all()}
    for code, name_ko, persona_text, is_default in ANALYSIS_PRESETS:
        if code in existing_codes:
            continue
        db.add(AnalysisPreset(code=code, name_ko=name_ko, persona_text=persona_text, is_default=is_default))
    db.commit()


def run() -> None:
    db = SessionLocal()
    try:
        sectors = seed_sectors(db)
        seed_stocks(db, sectors)
        seed_analysis_categories(db)
        seed_analysis_presets(db)
        print("시드 데이터 투입 완료")
    finally:
        db.close()


if __name__ == "__main__":
    run()
