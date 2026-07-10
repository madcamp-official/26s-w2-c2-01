from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.sector import Sector  # noqa: F401


class Stock(Base):
    __tablename__ = "stocks"

    ticker: Mapped[str] = mapped_column(String(10), primary_key=True)
    name_ko: Mapped[str | None] = mapped_column(String(100), nullable=True)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    exchange: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sector_id: Mapped[int | None] = mapped_column(ForeignKey("sectors.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    sector: Mapped["Sector | None"] = relationship(lazy="joined")
