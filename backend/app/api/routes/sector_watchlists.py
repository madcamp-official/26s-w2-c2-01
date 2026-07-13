from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud.sector import get_sector
from app.crud.sector_watchlist import (
    add_to_sector_watchlist,
    get_sector_watchlist_item,
    list_sector_watchlist,
    remove_from_sector_watchlist,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.watchlist import SectorWatchlistCreate, SectorWatchlistRead

router = APIRouter(prefix="/sector-watchlist", tags=["sector-watchlist"])


@router.get("", response_model=list[SectorWatchlistRead])
def read_sector_watchlist(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_sector_watchlist(db, current_user.id)


@router.post("", response_model=SectorWatchlistRead, status_code=status.HTTP_201_CREATED)
def create_sector_watchlist_item(
    data: SectorWatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sector = get_sector(db, data.sector_id)
    if not sector:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="섹터를 찾을 수 없습니다")
    if get_sector_watchlist_item(db, current_user.id, data.sector_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 등록된 관심 섹터입니다")
    return add_to_sector_watchlist(db, current_user.id, data.sector_id)


@router.delete("/{sector_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sector_watchlist_item(
    sector_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = get_sector_watchlist_item(db, current_user.id, sector_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="관심 섹터가 아닙니다")
    remove_from_sector_watchlist(db, item)
