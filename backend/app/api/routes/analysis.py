from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.analysis import AnalysisCategory, AnalysisPreset
from app.schemas.analysis import AnalysisCategoryRead, AnalysisPresetRead

router = APIRouter(tags=["analysis"])


@router.get("/analysis-categories", response_model=list[AnalysisCategoryRead])
def list_categories(db: Session = Depends(get_db)):
    return list(db.scalars(select(AnalysisCategory).order_by(AnalysisCategory.type, AnalysisCategory.code)).all())


@router.get("/analysis-presets", response_model=list[AnalysisPresetRead])
def list_presets(db: Session = Depends(get_db)):
    return list(db.scalars(select(AnalysisPreset).order_by(AnalysisPreset.id)).all())
