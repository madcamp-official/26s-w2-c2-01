from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.stock import get_stock, list_stocks
from app.db.session import get_db
from app.models.sector import Sector
from app.schemas.stock import SectorRead, StockWithSector
from app.services.popular_stocks import get_popular_tickers
from app.services.sector_classifier import classify_and_save_many
from app.services.volatility_cache import TODAY_RESULTS_FILE, read_json

router = APIRouter(tags=["stocks"])


@router.get("/stocks", response_model=list[StockWithSector])
def search_stocks(
    search: str | None = None,
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """검색어가 없으면 거래량 상위 종목, 있으면 전체 종목 DB 검색 결과를 반환한다."""
    query = search.strip() if search else None
    if query:
        rows = list_stocks(db, query, limit=limit)
        classify_and_save_many(db, rows)
        return rows

    # ETF/임시 티커 등 stocks(보통주) DB에 없는 항목이 섞일 수 있어 후보를 넉넉히 받는다.
    popular = get_popular_tickers(50)
    rows = list_stocks(db, limit=limit, tickers=popular)
    # Yahoo가 잠시 실패하거나 아직 전체 종목 import 중이어도 화면은 비워두지 않는다.
    if not rows:
        rows = list_stocks(db, limit=limit)
    classify_and_save_many(db, rows)
    return rows


@router.get("/stocks/volatility/today")
def read_today_volatility():
    """Serve cached results; API requests never trigger bulk Yahoo downloads."""
    payload = read_json(TODAY_RESULTS_FILE)
    if payload is None or not isinstance(payload.get("universe_size"), int):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Volatility scan is not ready for the full stock universe. Run the daily and premarket scan phases first.",
        )
    return payload


@router.get("/stocks/{ticker}", response_model=StockWithSector)
def read_stock(ticker: str, db: Session = Depends(get_db)):
    stock = get_stock(db, ticker)
    if not stock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="종목을 찾을 수 없습니다")
    return stock


@router.get("/sectors", response_model=list[SectorRead])
def list_sectors(db: Session = Depends(get_db)):
    return list(db.scalars(select(Sector).order_by(Sector.id)).all())
