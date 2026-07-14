"""
종목 → 섹터 자동 분류.

Finnhub /stock/profile2 의 finnhubIndustry 값(GICS 계열 업종 분류, 예:
"Semiconductors"/"Banking"/"Retail")을 우리 섹터 이름으로 매핑한다.

핵심 설계 원칙 — "빅테크"는 폐기했다:
GICS(S&P·MSCI의 업계 표준 분류) 기준으로 AAPL은 Technology, GOOGL은
Communication Services, AMZN은 Consumer Discretionary로 서로 다른 섹터다
(실측으로 stockanalysis.com에서 확인). "빅테크"는 어느 공식 분류 체계에도
없는 비공식 개념이라, 종목별 예외 처리 없이는 자동 분류가 불가능했다.
그래서 이 매핑은 "회사별 예외"가 아니라 "업종 라벨별 규칙"만 사용한다 —
어떤 회사든 똑같은 업종 라벨을 받으면 똑같은 섹터로 분류된다.

INDUSTRY_TO_SECTOR에 없는 업종은 억지로 아무 섹터에나 끼워맞추지 않고
분류 실패(None)로 남긴다 — "확실하지 않으면 추측하지 않는다"는 이 프로젝트의
환각 방지 원칙을 섹터 분류에도 그대로 적용한 것.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sector import Sector
from app.models.stock import Stock
from app.services.finnhub_client import FinnhubClient, FinnhubError

# Finnhub finnhubIndustry 값(실측 확보) -> 우리 섹터 name_ko
# 회사별이 아니라 "업종 라벨"별 규칙이라 예외 없이 모든 종목에 동일하게 적용된다.
INDUSTRY_TO_SECTOR: dict[str, str] = {
    # 반도체·AI
    "Semiconductors": "반도체·AI",
    # 테크·소프트웨어
    "Technology": "테크·소프트웨어",
    "Software": "테크·소프트웨어",
    "Internet": "테크·소프트웨어",
    # 미디어·인터넷
    "Media": "미디어·인터넷",
    "Internet Content & Information": "미디어·인터넷",
    "Entertainment": "미디어·인터넷",
    # 소비재·유통
    "Retail": "소비재·유통",
    "Consumer products": "소비재·유통",
    "Beverages": "소비재·유통",
    "Food Products": "소비재·유통",
    "Hotels, Restaurants & Leisure": "소비재·유통",
    "Textiles, Apparel & Luxury Goods": "소비재·유통",
    # 자동차
    "Automobiles": "자동차",
    "Auto Manufacturers": "자동차",
    # 금융
    "Banking": "금융",
    "Financial Services": "금융",
    "Insurance": "금융",
    # 헬스케어
    "Pharmaceuticals": "헬스케어",
    "Biotechnology": "헬스케어",
    "Health Care": "헬스케어",
    "Life Sciences Tools & Services": "헬스케어",
    "Medical Devices": "헬스케어",
    # 에너지
    "Energy": "에너지",
    "Oil & Gas": "에너지",
    # 산업재
    "Aerospace & Defense": "산업재",
    "Machinery": "산업재",
    "Airlines": "산업재",
    "Electrical Equipment": "산업재",
    "Logistics & Transportation": "산업재",
    "Industrial Conglomerates": "산업재",
    # 통신
    "Telecommunication": "통신",
    "Telecommunications": "통신",
    "Communications": "통신",
    # 부동산
    "Real Estate": "부동산",
    # 소재
    "Chemicals": "소재",
    "Metals & Mining": "소재",
    # 유틸리티
    "Utilities": "유틸리티",
}


def classify_stock_sector(db: Session, ticker: str) -> int | None:
    """
    Finnhub에서 업종을 조회해 섹터 id를 반환한다. API 호출 자체가 실패하면 None,
    업종이 비었거나 새 라벨이면 '기타'로 분류한다.
    """
    try:
        with FinnhubClient() as client:
            profile = client.get_company_profile(ticker)
    except FinnhubError:
        return None

    industry = profile.get("finnhubIndustry")
    # Finnhub가 N/A/빈 값을 주는 SPAC·신규 종목도 UI에서 미지정으로 남기지 않는다.
    sector_name = INDUSTRY_TO_SECTOR.get(industry, "기타")

    sector = db.scalar(select(Sector).where(Sector.name_ko == sector_name))
    return sector.id if sector else None


def classify_and_save(db: Session, stock: Stock, *, commit: bool = True) -> bool:
    """stock.sector_id가 비어 있으면 분류를 시도해 채운다. 실패해도 조용히 넘어간다."""
    if stock.sector_id is not None:
        return False
    sector_id = classify_stock_sector(db, stock.ticker)
    if sector_id is not None:
        stock.sector_id = sector_id
        if commit:
            db.commit()
        return True
    return False


def classify_and_save_many(db: Session, stocks: list[Stock]) -> int:
    """미분류 종목 여러 개를 Finnhub로 채우고 DB commit은 한 번만 수행한다."""
    changed = sum(classify_and_save(db, stock, commit=False) for stock in stocks)
    if changed:
        db.commit()
    return changed
