"""
섹터와 분석 설정 등 기준 데이터 투입 스크립트.
DB스키마.md 4절 / 분석카테고리.md 기준. 이미 데이터가 있으면 건너뛴다 (idempotent).

섹터 체계는 app/services/sector_classifier.py의 INDUSTRY_TO_SECTOR와 1:1로 맞춘
GICS 계열 분류다 — "빅테크"는 공식 분류 체계에 없는 비공식 개념이라 폐기했다
종목 데이터는 이 파일에 하드코딩하지 않고 import_us_stocks.py에서 가져온다.

사용법: python -m app.seed.seed_data
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.analysis import AnalysisCategory, AnalysisPreset
from app.models.sector import Sector
from app.models.stock import Stock

# (name_ko, name_en) — sector_classifier.py의 INDUSTRY_TO_SECTOR 매핑값과 이름을 맞춰야 한다.
SECTORS = [
    ("반도체·AI", "Semiconductors & AI"),
    ("테크·소프트웨어", "Technology & Software"),
    ("미디어·인터넷", "Media & Internet"),
    ("소비재·유통", "Consumer & Retail"),
    ("자동차", "Automobiles"),
    ("금융", "Financials"),
    ("헬스케어", "Health Care"),
    ("에너지", "Energy"),
    ("산업재", "Industrials"),
    ("통신", "Telecommunications"),
    ("부동산", "Real Estate"),
    ("소재", "Materials"),
    ("유틸리티", "Utilities"),
]

# 더 이상 안 쓰는 옛 섹터 이름 — 참조하는 종목이 없으면 정리 대상.
DEPRECATED_SECTOR_NAMES = ["빅테크", "전기차"]

# 옛 섹터와 함께 폐기된 analysis_categories 코드 (sector 타입, "빅테크"/"전기차" 대응).
DEPRECATED_CATEGORY_CODES = ["BIGTECH", "EV"]

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
    ("TECH", "테크·소프트웨어", "Technology & Software", "sector", None),
    ("MEDIA", "미디어·인터넷", "Media & Internet", "sector", None),
    ("CONSUMER", "소비재·유통", "Consumer & Retail", "sector", None),
    ("AUTO", "자동차", "Automobiles", "sector", None),
    ("FIN", "금융", "Financials", "sector", None),
    ("HEALTH", "헬스케어·바이오", "Healthcare/Biotech", "sector", None),
    ("ENERGY", "에너지", "Energy", "sector", None),
    ("INDUST", "산업재", "Industrials", "sector", None),
    ("TELECOM", "통신", "Telecommunications", "sector", None),
    ("REALESTATE", "부동산", "Real Estate", "sector", None),
    ("MATERIALS", "소재", "Materials", "sector", None),
    ("UTIL", "유틸리티", "Utilities", "sector", None),
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


def cleanup_deprecated_sectors(db: Session) -> None:
    """더 이상 참조하는 종목이 없는 옛 섹터를 정리한다."""
    for name_ko in DEPRECATED_SECTOR_NAMES:
        sector = db.scalar(select(Sector).where(Sector.name_ko == name_ko))
        if not sector:
            continue
        still_used = db.scalar(select(Stock).where(Stock.sector_id == sector.id))
        if still_used is None:
            db.delete(sector)
            print(f"옛 섹터 정리: {name_ko}")
    db.commit()


def cleanup_deprecated_categories(db: Session) -> None:
    """옛 섹터("빅테크"/"전기차")와 함께 폐기된 analysis_categories 코드를 정리한다."""
    for code in DEPRECATED_CATEGORY_CODES:
        cat = db.scalar(select(AnalysisCategory).where(AnalysisCategory.code == code))
        if cat:
            db.delete(cat)
            print(f"옛 카테고리 정리: {code}")
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
        seed_sectors(db)
        cleanup_deprecated_sectors(db)
        seed_analysis_categories(db)
        cleanup_deprecated_categories(db)
        seed_analysis_presets(db)
        print("기준 데이터 투입 완료")
    finally:
        db.close()


if __name__ == "__main__":
    run()
