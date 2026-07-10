from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud.stock import get_stock
from app.crud.watchlist import (
    add_to_watchlist,
    get_watchlist_item,
    list_watchlist,
    ranking,
    remove_from_watchlist,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.watchlist import WatchlistCreate, WatchlistRankingItem, WatchlistRead

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("", response_model=list[WatchlistRead])
def read_watchlist(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_watchlist(db, current_user.id)


@router.post("", response_model=WatchlistRead, status_code=status.HTTP_201_CREATED)
def create_watchlist_item(
    data: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticker = data.ticker.upper()
    if not get_stock(db, ticker):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="종목을 찾을 수 없습니다")
    if get_watchlist_item(db, current_user.id, ticker):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 등록된 관심 종목입니다")
    return add_to_watchlist(db, current_user.id, ticker)


@router.delete("/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watchlist_item(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = get_watchlist_item(db, current_user.id, ticker.upper())
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="관심 종목이 아닙니다")
    remove_from_watchlist(db, item)


@router.get("/ranking/top", response_model=list[WatchlistRankingItem])
def watchlist_ranking(limit: int = 10, db: Session = Depends(get_db)):
    rows = ranking(db, limit)
    return [
        WatchlistRankingItem(ticker=r.ticker, name_ko=r.name_ko, name_en=r.name_en, fans=r.fans) for r in rows
    ]
