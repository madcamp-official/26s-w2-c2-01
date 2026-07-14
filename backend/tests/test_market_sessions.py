from datetime import date, datetime
from unittest import TestCase
from zoneinfo import ZoneInfo

from app.services.market_sessions import available_sessions, current_briefing_date, current_session


KST = ZoneInfo("Asia/Seoul")


class MarketSessionsTest(TestCase):
    def test_briefing_day_rolls_over_at_market_open_update(self) -> None:
        self.assertEqual(
            current_briefing_date(datetime(2026, 7, 14, 21, 59, tzinfo=KST)),
            date(2026, 7, 14),
        )
        self.assertEqual(
            current_briefing_date(datetime(2026, 7, 14, 22, 0, tzinfo=KST)),
            date(2026, 7, 15),
        )

    def test_sessions_unlock_in_chronological_order(self) -> None:
        briefing_date = date(2026, 7, 14)
        cases = (
            (datetime(2026, 7, 13, 22, 0, tzinfo=KST), ["market_open"]),
            (datetime(2026, 7, 14, 2, 0, tzinfo=KST), ["market_open", "intraday"]),
            (datetime(2026, 7, 14, 5, 0, tzinfo=KST), ["market_open", "intraday", "market_close"]),
            (datetime(2026, 7, 14, 14, 0, tzinfo=KST), ["market_open", "intraday", "market_close", "after_hours"]),
        )
        for now, expected in cases:
            with self.subTest(now=now):
                self.assertEqual(
                    [item.key for item in available_sessions(briefing_date, now)], expected
                )
                self.assertEqual(current_session(briefing_date, now), expected[-1])
