from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.stock import get_stock, list_stocks
from app.db.session import get_db
from app.models.sector import Sector
from app.schemas.stock import SectorRead, StockWithSector

router = APIRouter(tags=["stocks"])


@router.get("/stocks", response_model=list[StockWithSector])
def search_stocks(search: str | None = None, db: Session = Depends(get_db)):
    return list_stocks(db, search)


@router.get("/stocks/{ticker}", response_model=StockWithSector)
def read_stock(ticker: str, db: Session = Depends(get_db)):
    stock = get_stock(db, ticker)
    if not stock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="종목을 찾을 수 없습니다")
    return stock


@router.get("/sectors", response_model=list[SectorRead])
def list_sectors(db: Session = Depends(get_db)):
    return list(db.scalars(select(Sector).order_by(Sector.id)).all())
