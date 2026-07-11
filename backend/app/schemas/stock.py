from pydantic import BaseModel, ConfigDict


class SectorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name_ko: str
    name_en: str


class StockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticker: str
    name_ko: str | None
    name_en: str
    exchange: str | None
    sector_id: int | None


class StockWithSector(StockRead):
    sector: SectorRead | None = None
