from unittest import TestCase
from unittest.mock import patch

from app.jobs.scheduler import run_watchlist_refresh_cycle


class SchedulerTest(TestCase):
    @patch("app.jobs.scheduler.generate_briefings.run")
    @patch("app.jobs.scheduler.collect_news_run")
    def test_watchlist_daily_refresh_forces_one_generation(self, collect_news, generate) -> None:
        run_watchlist_refresh_cycle()

        collect_news.assert_called_once_with()
        generate.assert_called_once_with(force=True)
