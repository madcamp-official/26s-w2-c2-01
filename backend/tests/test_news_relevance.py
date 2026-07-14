from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import MagicMock, patch

from app.batch.collect_news import collect_for_ticker
from app.core.finnhub_client import FinnhubArticle
from app.models.news_article import NewsArticle
from app.services.news_document import format_news_article
from app.services.news_relevance import (
    score_article_relevance,
    select_persisted_relevant_articles,
    select_relevant_articles,
)


def article(
    headline: str,
    *,
    summary: str = "",
    related: str = "AAPL",
    source: str = "Yahoo",
) -> FinnhubArticle:
    return FinnhubArticle(
        headline=headline,
        url=f"https://example.com/{headline}",
        source=source,
        summary=summary,
        ts=1_720_000_000,
        related=related,
    )


class NewsRelevanceTest(TestCase):
    def test_company_suffix_with_period_is_removed_for_alias_matching(self) -> None:
        direct = article("Nvidia announces a new AI accelerator", related="")

        score = score_article_relevance(
            direct, ticker="NVDA", company_names=["NVIDIA Corp."]
        )

        self.assertGreaterEqual(score, 6)

    def test_direct_company_mention_outranks_related_tag_only(self) -> None:
        direct = article("Apple raises its iPhone shipment forecast")
        indirect = article("American Express remains a top holding")

        direct_score = score_article_relevance(direct, ticker="AAPL", company_names=["APPLE INC"])
        indirect_score = score_article_relevance(indirect, ticker="AAPL", company_names=["APPLE INC"])

        self.assertGreater(direct_score, indirect_score)
        self.assertGreaterEqual(direct_score, 4)

    def test_generic_mover_headline_is_penalized(self) -> None:
        specific = article("Applied Materials expands chip equipment production", related="AMAT")
        generic = article("What's going on in today's pre-market session: market movers", related="AMAT")

        self.assertGreater(
            score_article_relevance(specific, ticker="AMAT", company_names=["APPLIED MATERIALS INC"]),
            score_article_relevance(generic, ticker="AMAT", company_names=["APPLIED MATERIALS INC"]),
        )

    def test_selection_backfills_only_to_requested_minimum(self) -> None:
        rows = [
            article("Apple announces a product update"),
            article("Unrelated market story one"),
            article("Unrelated market story two"),
            article("Unrelated market story three"),
        ]

        selected = select_relevant_articles(
            rows,
            ticker="AAPL",
            company_names=["APPLE INC"],
            limit=8,
            min_score=4,
            min_articles=3,
        )

        self.assertEqual(len(selected), 3)
        self.assertEqual(selected[0].headline, "Apple announces a product update")

    def test_llm_document_contains_kst_publication_time(self) -> None:
        row = NewsArticle(
            ticker="AAPL",
            title="Apple update",
            url="https://example.com/apple",
            source="Reuters",
            summary="Summary",
            published_at=datetime(2026, 7, 14, 1, 30, tzinfo=timezone.utc),
        )

        document = format_news_article(row, include_ticker=True)

        self.assertIn("게시 시각: 2026-07-14 10:30 KST", document)
        self.assertIn("[AAPL]", document)

    def test_persisted_filter_removes_unrelated_nvda_articles(self) -> None:
        rows = [
            NewsArticle(
                ticker="NVDA",
                title="SpaceX receives a new valuation",
                url="https://example.com/spacex",
                source="Yahoo",
                summary="Space company update",
                published_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
            ),
            NewsArticle(
                ticker="NVDA",
                title="Nvidia changes its Asia AI chip strategy",
                url="https://example.com/nvidia",
                source="Reuters",
                summary="Nvidia updated its customer plan.",
                published_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
            ),
        ]

        selected = select_persisted_relevant_articles(
            rows,
            company_names_by_ticker={"NVDA": ["NVIDIA Corp."]},
            min_score=4,
            limit=10,
        )

        self.assertEqual([row.title for row in selected], ["Nvidia changes its Asia AI chip strategy"])

    def test_stock_filter_rejects_incidental_summary_only_mention(self) -> None:
        row = NewsArticle(
            ticker="NVDA",
            title="SoftBank CEO discusses global AI investment",
            url="https://example.com/softbank",
            source="Yahoo",
            summary="AI valuations have risen at companies like Nvidia.",
            published_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
        )

        selected = select_persisted_relevant_articles(
            [row],
            company_names_by_ticker={"NVDA": ["NVIDIA Corp."]},
            min_score=4,
            limit=10,
        )

        self.assertEqual(selected, [])

    def test_sector_filter_can_keep_summary_only_ecosystem_article(self) -> None:
        row = NewsArticle(
            ticker="NVDA",
            title="Super Micro launches Vera Rubin infrastructure blueprint",
            url="https://example.com/smci",
            source="Yahoo",
            summary="The system is built around the NVIDIA Vera Rubin platform.",
            published_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
        )

        selected = select_persisted_relevant_articles(
            [row],
            company_names_by_ticker={"NVDA": ["NVIDIA Corp."]},
            min_score=3,
            limit=10,
        )

        self.assertEqual(selected, [row])

    @patch("app.batch.collect_news.create_news_article")
    @patch("app.batch.collect_news.existing_urls", return_value=set())
    @patch("app.batch.collect_news.fetch_company_news")
    @patch("app.batch.collect_news.settings.ENABLE_NEWS_RELEVANCE_FILTER", False)
    def test_filter_flag_false_restores_latest_first_collection(
        self, fetch, _existing, create
    ) -> None:
        fetch.return_value = [
            article("Newest unrelated article"),
            article("Second unrelated article"),
            article("Third unrelated article"),
        ]

        inserted, _ = collect_for_ticker(
            MagicMock(), "AAPL", datetime(2026, 7, 13).date(), datetime(2026, 7, 14).date(), 2
        )

        self.assertEqual(inserted, 2)
        self.assertEqual(create.call_count, 2)
        self.assertEqual(create.call_args_list[0].kwargs["title"], "Newest unrelated article")

    @patch("app.batch.collect_news.create_news_article")
    @patch("app.batch.collect_news.existing_urls")
    @patch("app.batch.collect_news.fetch_company_news")
    def test_existing_relevant_articles_prevent_repeated_low_score_backfill(
        self, fetch, existing, create
    ) -> None:
        relevant = [
            article("Apple product update"),
            article("AAPL earnings update"),
            article("Apple supplier update"),
        ]
        unrelated = [article("Unrelated story one"), article("Unrelated story two")]
        fetch.return_value = relevant + unrelated
        existing.return_value = {row.url for row in relevant}
        stock = MagicMock(name_en="APPLE INC", name_ko=None)
        db = MagicMock()
        db.get.return_value = stock

        inserted, _ = collect_for_ticker(
            db, "AAPL", datetime(2026, 7, 13).date(), datetime(2026, 7, 14).date(), 8
        )

        self.assertEqual(inserted, 0)
        create.assert_not_called()
