from datetime import datetime, timezone
from unittest import TestCase

from app.services.cnbc_rss_client import parse_cnbc_rss


class CnbcRssTest(TestCase):
    def test_parse_filters_old_items_and_cleans_html(self) -> None:
        content = """<?xml version="1.0"?>
        <rss><channel>
          <item>
            <title>Stocks &amp; bonds rise</title>
            <description><![CDATA[<p>Markets <b>advanced</b>.</p>]]></description>
            <link>https://example.com/fresh</link>
            <pubDate>Tue, 14 Jul 2026 14:00:00 GMT</pubDate>
          </item>
          <item>
            <title>Old story</title>
            <description>Old</description>
            <link>https://example.com/old</link>
            <pubDate>Sun, 12 Jul 2026 14:00:00 GMT</pubDate>
          </item>
        </channel></rss>"""

        result = parse_cnbc_rss(
            content,
            category="top",
            now=datetime(2026, 7, 14, 15, tzinfo=timezone.utc),
            lookback_hours=24,
            limit=5,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["headline"], "Stocks & bonds rise")
        self.assertEqual(result[0]["summary"], "Markets advanced .")
        self.assertEqual(result[0]["source"], "CNBC")

    def test_parse_requires_url_and_publication_time(self) -> None:
        content = """<rss><channel><item>
          <title>Incomplete story</title><description>Missing metadata</description>
        </item></channel></rss>"""

        result = parse_cnbc_rss(
            content,
            category="top",
            now=datetime(2026, 7, 14, tzinfo=timezone.utc),
            lookback_hours=24,
            limit=5,
        )

        self.assertEqual(result, [])

    def test_top_feed_removes_non_market_story(self) -> None:
        content = """<rss><channel><item>
          <title>Celebrity wins a court case</title>
          <description>Details from a newly filed court document.</description>
          <link>https://example.com/court</link>
          <pubDate>Tue, 14 Jul 2026 14:00:00 GMT</pubDate>
        </item></channel></rss>"""

        result = parse_cnbc_rss(
            content,
            category="top",
            now=datetime(2026, 7, 14, 15, tzinfo=timezone.utc),
            lookback_hours=24,
            limit=5,
        )

        self.assertEqual(result, [])
