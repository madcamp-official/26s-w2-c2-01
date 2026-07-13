from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.stock import SectorRead, StockWithSector


class WatchlistCreate(BaseModel):
    ticker: str


class WatchlistRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    created_at: datetime
    stock: StockWithSector | None = None


class WatchlistRankingItem(BaseModel):
    ticker: str
    name_ko: str | None
    name_en: str
    fans: int


class SectorWatchlistCreate(BaseModel):
    sector_id: int


class SectorWatchlistRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sector_id: int
    created_at: datetime
    sector: SectorRead | None = None
