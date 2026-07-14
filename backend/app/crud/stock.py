from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.models.stock import Stock


def list_stocks(
    db: Session,
    search: str | None = None,
    *,
    limit: int = 20,
    tickers: list[str] | None = None,
) -> list[Stock]:
    stmt = select(Stock)
    if search:
        normalized = search.upper()
        like = f"%{normalized}%"
        stmt = stmt.where(or_(Stock.ticker.ilike(like), Stock.name_ko.ilike(like), Stock.name_en.ilike(like)))
    if tickers is not None:
        if not tickers:
            return []
        stmt = stmt.where(Stock.ticker.in_(tickers))
    if search:
        stmt = stmt.order_by(
            case(
                (func.upper(Stock.ticker) == normalized, 0),
                (Stock.ticker.ilike(f"{normalized}%"), 1),
                else_=2,
            ),
            Stock.ticker,
        )
    else:
        stmt = stmt.order_by(Stock.ticker)
    # 인기 후보는 SQL 알파벳순으로 자르지 말고 모두 읽은 뒤 공급자 순서대로 limit한다.
    stmt = stmt.limit(len(tickers) if tickers is not None else limit)
    rows = list(db.scalars(stmt).all())
    if tickers is None:
        return rows
    by_ticker = {stock.ticker: stock for stock in rows}
    return [by_ticker[ticker] for ticker in tickers if ticker in by_ticker][:limit]


def get_stock(db: Session, ticker: str) -> Stock | None:
    return db.get(Stock, ticker.upper())
