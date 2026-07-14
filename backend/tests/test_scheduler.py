from unittest import TestCase
from unittest.mock import patch

from app.jobs.scheduler import run_refresh_cycle


class SchedulerTest(TestCase):
    @patch("app.jobs.scheduler.generate_sector_briefings.run")
    @patch("app.jobs.scheduler.generate_briefings.run")
    @patch("app.jobs.scheduler.generate_market_overview")
    @patch("app.jobs.scheduler.SessionLocal")
    @patch("app.jobs.scheduler.collect_news_run")
    def test_refresh_cycle_updates_all_briefings(
        self, collect_news, session_local, generate_overview, generate_stocks, generate_sectors
    ) -> None:
        run_refresh_cycle()

        collect_news.assert_called_once_with()
        generate_overview.assert_called_once()
        generate_sectors.assert_called_once_with()
        generate_stocks.assert_called_once_with()
        session_local.return_value.close.assert_called_once_with()
