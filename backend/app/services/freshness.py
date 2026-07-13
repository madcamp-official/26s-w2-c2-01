"""
캐시 신선도 판단 공통 유틸. 종목 브리핑(briefing_pipeline)과 전체 시황
(market_overview_pipeline)이 같은 "REFRESH_INTERVAL_HOURS 이내면 재사용" 규칙을
공유하므로 여기 하나로 모았다.
"""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session


def is_fresh(db: Session, generated_at: datetime, hours: int) -> bool:
    """
    generated_at이 hours 시간 이내인지 판단한다.
    앱 서버가 어느 타임존에서 돌든 결과가 일관되도록, 비교 기준(now)을
    파이썬이 아니라 DB 서버에서 직접 가져와 generated_at(같은 DB가 찍은 값)과 비교한다.
    """
    server_now = db.scalar(select(func.now())).replace(tzinfo=None)
    return server_now - generated_at < timedelta(hours=hours)
