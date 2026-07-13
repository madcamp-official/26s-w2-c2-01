from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sector import Sector


def list_sectors(db: Session) -> list[Sector]:
    return list(db.scalars(select(Sector).order_by(Sector.name_ko)).all())


def get_sector(db: Session, sector_id: int) -> Sector | None:
    return db.get(Sector, sector_id)
