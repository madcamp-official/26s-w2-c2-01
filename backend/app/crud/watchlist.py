from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.stock import Stock
from app.models.watchlist import Watchlist


def list_watchlist(db: Session, user_id: int) -> list[Watchlist]:
    stmt = select(Watchlist).where(Watchlist.user_id == user_id).order_by(Watchlist.created_at)
    return list(db.scalars(stmt).all())


def get_watchlist_item(db: Session, user_id: int, ticker: str) -> Watchlist | None:
    stmt = select(Watchlist).where(Watchlist.user_id == user_id, Watchlist.ticker == ticker)
    return db.scalar(stmt)


def add_to_watchlist(db: Session, user_id: int, ticker: str) -> Watchlist:
    item = Watchlist(user_id=user_id, ticker=ticker)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def remove_from_watchlist(db: Session, item: Watchlist) -> None:
    db.delete(item)
    db.commit()


def ranking(db: Session, limit: int = 10):
    stmt = (
        select(Stock.ticker, Stock.name_ko, Stock.name_en, func.count(Watchlist.id).label("fans"))
        .join(Watchlist, Watchlist.ticker == Stock.ticker)
        .group_by(Stock.ticker, Stock.name_ko, Stock.name_en)
        .order_by(func.count(Watchlist.id).desc())
        .limit(limit)
    )
    return db.execute(stmt).all()
