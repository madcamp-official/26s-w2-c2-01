from datetime import date, datetime

from sqlalchemy import BigInteger, Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"
    __table_args__ = (UniqueConstraint("ticker", "trade_date", name="uq_price_snapshots_ticker_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(
        String(10), ForeignKey("stocks.ticker", ondelete="CASCADE"), nullable=False, index=True
    )
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    close: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    change_pct: Mapped[float | None] = mapped_column(Numeric(7, 3), nullable=True)
    volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(server_default=func.now())
