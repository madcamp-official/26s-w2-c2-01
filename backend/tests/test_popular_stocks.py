from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app.services.polygon_client import PolygonNotConfigured
from app.services.popular_stocks import get_popular_tickers
from app.services.volatility_cache import write_json


class PopularStocksTest(TestCase):
    def test_polygon_ranks_by_dollar_volume(self) -> None:
        rows = [
            {"T": "HIGH_VOLUME", "c": 2, "v": 1_000},
            {"T": "HIGH_DOLLAR", "c": 100, "v": 100},
            {"T": "MIDDLE", "c": 10, "v": 500},
        ]
        with TemporaryDirectory() as tmp, patch(
            "app.services.popular_stocks.POPULAR_STOCKS_FILE",
            Path(tmp) / "popular.json",
        ):
            result = get_popular_tickers(2, polygon_fetch=lambda _day: rows)

        self.assertEqual(["HIGH_DOLLAR", "MIDDLE"], result)

    def test_yahoo_is_fallback_when_polygon_is_not_configured(self) -> None:
        def no_polygon(_day):
            raise PolygonNotConfigured("missing key")

        yahoo = {"quotes": [{"symbol": "AAPL", "quoteType": "EQUITY"}, {"symbol": "NVDA"}]}
        with TemporaryDirectory() as tmp, patch(
            "app.services.popular_stocks.POPULAR_STOCKS_FILE",
            Path(tmp) / "popular.json",
        ):
            result = get_popular_tickers(2, polygon_fetch=no_polygon, screen=lambda *_args, **_kwargs: yahoo)

        self.assertEqual(["AAPL", "NVDA"], result)

    def test_fresh_cache_avoids_network_calls(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "popular.json"
            write_json(
                path,
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "tickers": ["MSFT", "META"],
                },
            )
            with patch("app.services.popular_stocks.POPULAR_STOCKS_FILE", path):
                result = get_popular_tickers(
                    2,
                    polygon_fetch=lambda _day: self.fail("Polygon should not be called"),
                    screen=lambda *_args, **_kwargs: self.fail("Yahoo should not be called"),
                )

        self.assertEqual(["MSFT", "META"], result)
