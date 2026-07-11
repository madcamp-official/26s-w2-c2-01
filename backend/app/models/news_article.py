from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str | None] = mapped_column(
        String(10), ForeignKey("stocks.ticker", ondelete="CASCADE"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(10), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(server_default=func.now())
