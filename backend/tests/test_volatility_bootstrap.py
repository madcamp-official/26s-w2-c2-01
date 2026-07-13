from unittest import TestCase

from app.jobs.scan_volatility import cache_matches_universe


class VolatilityBootstrapTest(TestCase):
    def test_missing_or_legacy_cache_requires_bootstrap(self) -> None:
        self.assertFalse(cache_matches_universe(None, 4_958))
        self.assertFalse(cache_matches_universe({"all": {}}, 4_958))

    def test_changed_universe_requires_bootstrap(self) -> None:
        self.assertFalse(cache_matches_universe({"universe_size": 10}, 4_958))

    def test_matching_universe_skips_bootstrap(self) -> None:
        self.assertTrue(cache_matches_universe({"universe_size": 4_958}, 4_958))
