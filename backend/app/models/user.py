from datetime import datetime

from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("investor_type IN ('stable','balanced','aggressive')", name="ck_users_investor_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    investor_type: Mapped[str] = mapped_column(String(20), nullable=False, default="balanced")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    #: 모든 수동 브리핑 새로고침의 사용자별 30분 쿨다운을 추적한다.
    #: null이면 아직 한 번도 사용하지 않은 상태다.
    last_manual_refresh_at: Mapped[datetime | None] = mapped_column(nullable=True)
