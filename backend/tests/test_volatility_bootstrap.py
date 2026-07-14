from unittest import TestCase
from unittest.mock import MagicMock, patch

from app.jobs.scan_volatility import cache_matches_universe, load_universe


class VolatilityBootstrapTest(TestCase):
    def test_missing_or_legacy_cache_requires_bootstrap(self) -> None:
        self.assertFalse(cache_matches_universe(None, 4_958))
        self.assertFalse(cache_matches_universe({"all": {}}, 4_958))

    def test_changed_universe_requires_bootstrap(self) -> None:
        self.assertFalse(cache_matches_universe({"universe_size": 10}, 4_958))

    def test_matching_universe_skips_bootstrap(self) -> None:
        self.assertTrue(cache_matches_universe({"universe_size": 4_958}, 4_958))

    @patch("app.jobs.scan_volatility.SessionLocal")
    def test_load_universe_is_not_limited_to_popular_tickers(self, session_local) -> None:
        tickers = [f"T{i:04d}" for i in range(100)]
        db = MagicMock()
        db.scalars.return_value.all.return_value = tickers
        session_local.return_value = db

        self.assertEqual(tickers, load_universe())
        db.close.assert_called_once_with()
