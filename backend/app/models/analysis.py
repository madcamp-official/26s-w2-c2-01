from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class AnalysisCategory(Base):
    __tablename__ = "analysis_categories"
    __table_args__ = (
        CheckConstraint("type IN ('index','indicator','sector','theme')", name="ck_analysis_categories_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name_ko: Mapped[str] = mapped_column(String(50), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(80), nullable=True)
    type: Mapped[str] = mapped_column(String(12), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class AnalysisPreset(Base):
    __tablename__ = "analysis_presets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name_ko: Mapped[str] = mapped_column(String(50), nullable=False)
    persona_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)


class UserPreference(Base):
    __tablename__ = "user_preferences"
    __table_args__ = (
        CheckConstraint("depth IN ('brief','standard','deep')", name="ck_user_preferences_depth"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    default_preset_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_presets.id"), nullable=True)
    default_categories: Mapped[list] = mapped_column(JSONB, default=list)
    depth: Mapped[str] = mapped_column(String(10), default="standard")
    language: Mapped[str] = mapped_column(String(5), default="ko")


class DocumentAnalysis(Base):
    __tablename__ = "document_analyses"
    __table_args__ = (
        CheckConstraint("source_type IN ('news','report','paste')", name="ck_document_analyses_source_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_type: Mapped[str] = mapped_column(String(10), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    tickers: Mapped[list] = mapped_column(JSONB, default=list)
    facts: Mapped[dict] = mapped_column(JSONB, nullable=False)
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class AnalysisRender(Base):
    __tablename__ = "analysis_renders"
    __table_args__ = (
        UniqueConstraint(
            "document_analysis_id", "preset_id", "category_codes", "depth", "language",
            name="uq_analysis_renders_combo",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_analysis_id: Mapped[int] = mapped_column(
        ForeignKey("document_analyses.id", ondelete="CASCADE"), nullable=False
    )
    preset_id: Mapped[int] = mapped_column(ForeignKey("analysis_presets.id"), nullable=False)
    category_codes: Mapped[list] = mapped_column(JSONB, default=list)
    depth: Mapped[str | None] = mapped_column(String(10), nullable=True)
    language: Mapped[str | None] = mapped_column(String(5), nullable=True)
    result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(server_default=func.now())
