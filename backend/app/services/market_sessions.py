"""KST 기준으로 하루의 미국 장 브리핑 세션을 계산한다."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

BriefingSession = Literal["market_open", "intraday", "market_close", "after_hours"]
KST = ZoneInfo("Asia/Seoul")


@dataclass(frozen=True)
class SessionDefinition:
    key: BriefingSession
    label: str
    hour: int
    day_offset: int = 0


# 브리핑 날짜 D는 D-1 22:00 장시작부터 D 22:00 직전까지다.
SESSION_DEFINITIONS = (
    SessionDefinition("market_open", "장시작", 22, -1),
    SessionDefinition("intraday", "장중", 2),
    SessionDefinition("market_close", "장마감", 5),
    SessionDefinition("after_hours", "시간외", 14),
)


def now_kst() -> datetime:
    return datetime.now(KST)


def current_briefing_date(now: datetime | None = None) -> date:
    current = (now or now_kst()).astimezone(KST)
    return current.date() + timedelta(days=1) if current.hour >= 22 else current.date()


def scheduled_at(briefing_date: date, definition: SessionDefinition) -> datetime:
    session_date = briefing_date + timedelta(days=definition.day_offset)
    return datetime.combine(session_date, time(definition.hour), tzinfo=KST)


def available_sessions(briefing_date: date | None = None, now: datetime | None = None) -> list[SessionDefinition]:
    current = (now or now_kst()).astimezone(KST)
    target_date = briefing_date or current_briefing_date(current)
    return [item for item in SESSION_DEFINITIONS if scheduled_at(target_date, item) <= current]


def current_session(briefing_date: date | None = None, now: datetime | None = None) -> BriefingSession:
    sessions = available_sessions(briefing_date, now)
    return (sessions[-1] if sessions else SESSION_DEFINITIONS[0]).key


def session_rank(value: str) -> int:
    return next((index for index, item in enumerate(SESSION_DEFINITIONS) if item.key == value), -1)
