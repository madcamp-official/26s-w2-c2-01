from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.stock import StockWithSector


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
