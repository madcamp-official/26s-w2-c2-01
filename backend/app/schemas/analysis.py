from pydantic import BaseModel, ConfigDict


class AnalysisCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name_ko: str
    name_en: str | None
    type: str
    description: str | None


class AnalysisPresetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name_ko: str
    persona_text: str
    is_default: bool
