from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.stock import get_stock, list_stocks
from app.db.session import get_db
from app.models.sector import Sector
from app.schemas.stock import SectorRead, StockWithSector
from app.services.volatility_cache import TODAY_RESULTS_FILE, read_json

router = APIRouter(tags=["stocks"])


@router.get("/stocks", response_model=list[StockWithSector])
def search_stocks(search: str | None = None, db: Session = Depends(get_db)):
    return list_stocks(db, search)


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
