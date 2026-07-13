from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.stock import Stock
from app.models.watchlist import SectorWatchlist


def list_sector_watchlist(db: Session, user_id: int) -> list[SectorWatchlist]:
    stmt = select(SectorWatchlist).where(SectorWatchlist.user_id == user_id).order_by(SectorWatchlist.created_at)
    return list(db.scalars(stmt).all())


def get_sector_watchlist_item(db: Session, user_id: int, sector_id: int) -> SectorWatchlist | None:
    stmt = select(SectorWatchlist).where(SectorWatchlist.user_id == user_id, SectorWatchlist.sector_id == sector_id)
    return db.scalar(stmt)


def add_to_sector_watchlist(db: Session, user_id: int, sector_id: int) -> SectorWatchlist:
    item = SectorWatchlist(user_id=user_id, sector_id=sector_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def remove_from_sector_watchlist(db: Session, item: SectorWatchlist) -> None:
    db.delete(item)
    db.commit()


def distinct_followed_sector_ids(db: Session) -> list[int]:
    """전역(모든 유저) 관심 섹터 id 목록 — 뉴스 수집·정기 브리핑 갱신 대상 산정용."""
    stmt = select(SectorWatchlist.sector_id).distinct()
    return list(db.scalars(stmt).all())


def distinct_followed_sector_tickers(db: Session) -> list[str]:
    """관심 섹터에 속한 종목 티커 목록 — collect_news.py의 수집 대상 확장용.
    관심종목으로 직접 추가하지 않았어도, 관심 섹터에 속한 종목이면 뉴스를 수집한다."""
    stmt = (
        select(Stock.ticker)
        .join(SectorWatchlist, SectorWatchlist.sector_id == Stock.sector_id)
        .distinct()
    )
    return list(db.scalars(stmt).all())
