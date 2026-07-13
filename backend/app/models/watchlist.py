from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.sector import Sector  # noqa: F401
from app.models.stock import Stock  # noqa: F401


class Watchlist(Base):
    __tablename__ = "watchlists"
    __table_args__ = (UniqueConstraint("user_id", "ticker", name="uq_watchlists_user_ticker"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    ticker: Mapped[str] = mapped_column(
        String(10), ForeignKey("stocks.ticker", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    stock: Mapped["Stock"] = relationship(lazy="joined")


class SectorWatchlist(Base):
    """관심 섹터 (users N:M sectors) — watchlists(관심 종목)와 동일한 패턴."""

    __tablename__ = "sector_watchlists"
    __table_args__ = (UniqueConstraint("user_id", "sector_id", name="uq_sector_watchlists_user_sector"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    sector_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sectors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    sector: Mapped["Sector"] = relationship(lazy="joined")
