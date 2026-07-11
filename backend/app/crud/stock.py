from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.stock import Stock


def list_stocks(db: Session, search: str | None = None) -> list[Stock]:
    stmt = select(Stock)
    if search:
        like = f"%{search.upper()}%"
        stmt = stmt.where(or_(Stock.ticker.ilike(like), Stock.name_ko.ilike(like), Stock.name_en.ilike(like)))
    stmt = stmt.order_by(Stock.ticker)
    return list(db.scalars(stmt).all())


def get_stock(db: Session, ticker: str) -> Stock | None:
    return db.get(Stock, ticker.upper())
