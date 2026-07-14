from unittest import TestCase
from unittest.mock import patch

from app.services.market_overview_pipeline import _fetch_market_news


def news(url: str, source: str) -> dict:
    return {"headline": url, "summary": "", "url": url, "source": source}


class MarketOverviewNewsTest(TestCase):
    @patch("app.services.market_overview_pipeline.settings.CNBC_MARKET_NEWS_MIN_ARTICLES", 2)
    @patch("app.services.market_overview_pipeline.settings.CNBC_MARKET_NEWS_LIMIT", 3)
    @patch("app.services.market_overview_pipeline.settings.ENABLE_CNBC_MARKET_RSS", True)
    @patch("app.services.market_overview_pipeline._fetch_general_news")
    @patch("app.services.market_overview_pipeline.fetch_cnbc_market_news")
    def test_cnbc_is_primary_when_enough_articles(self, cnbc, finnhub) -> None:
        cnbc.return_value = [news("c1", "CNBC"), news("c2", "CNBC")]
        finnhub.return_value = [news("f1", "Finnhub")]

        result = _fetch_market_news()

        self.assertEqual([row["url"] for row in result], ["c1", "c2", "f1"])

    @patch("app.services.market_overview_pipeline.settings.CNBC_MARKET_NEWS_MIN_ARTICLES", 3)
    @patch("app.services.market_overview_pipeline.settings.CNBC_MARKET_NEWS_LIMIT", 3)
    @patch("app.services.market_overview_pipeline.settings.ENABLE_CNBC_MARKET_RSS", True)
    @patch("app.services.market_overview_pipeline._fetch_general_news")
    @patch("app.services.market_overview_pipeline.fetch_cnbc_market_news")
    def test_finnhub_supplements_sparse_cnbc_results(self, cnbc, finnhub) -> None:
        cnbc.return_value = [news("shared", "CNBC")]
        finnhub.return_value = [news("shared", "Finnhub"), news("f2", "Finnhub")]

        result = _fetch_market_news()

        self.assertEqual([row["url"] for row in result], ["shared", "f2"])
        self.assertEqual(result[0]["source"], "Finnhub")

    @patch("app.services.market_overview_pipeline.settings.CNBC_MARKET_NEWS_LIMIT", 3)
    @patch("app.services.market_overview_pipeline.settings.ENABLE_CNBC_MARKET_RSS", False)
    @patch("app.services.market_overview_pipeline._fetch_general_news")
    def test_flag_disables_cnbc(self, finnhub) -> None:
        finnhub.return_value = [news("f1", "Finnhub")]

        result = _fetch_market_news()

        self.assertEqual([row["url"] for row in result], ["f1"])
