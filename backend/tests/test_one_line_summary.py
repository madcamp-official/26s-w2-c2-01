from unittest import TestCase

from app.schemas.llm import BriefingRender
from app.services.briefing_sanitizer import sanitize_briefing_render


class OneLineSummaryTest(TestCase):
    def test_sanitizer_removes_urls_and_line_breaks(self) -> None:
        render = BriefingRender(
            summary="상세 요약",
            one_line_summary="핵심 이슈\nhttps://example.com/source",
            sentiment="neutral",
        )

        cleaned = sanitize_briefing_render(render)

        self.assertEqual(cleaned.one_line_summary, "핵심 이슈")

    def test_sanitizer_limits_mobile_summary_to_80_characters(self) -> None:
        render = BriefingRender(
            summary="상세 요약",
            one_line_summary="가" * 100,
            sentiment="neutral",
        )

        cleaned = sanitize_briefing_render(render)

        self.assertEqual(cleaned.one_line_summary, "가" * 80)
