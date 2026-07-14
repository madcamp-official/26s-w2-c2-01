from unittest import TestCase

from pydantic import ValidationError

from app.schemas.llm import BriefingRender
from app.services.briefing_sanitizer import sanitize_briefing_render


class OneLineSummaryTest(TestCase):
    def test_sanitizer_removes_urls_and_line_breaks(self) -> None:
        render = BriefingRender(
            summary="상세 요약",
            one_line_summary="핵심\n이슈 http://x.co",
            sentiment="neutral",
        )

        cleaned = sanitize_briefing_render(render)

        self.assertEqual(cleaned.one_line_summary, "핵심 이슈")

    def test_schema_rejects_summary_over_30_characters_instead_of_truncating(self) -> None:
        with self.assertRaises(ValidationError):
            BriefingRender(
                summary="상세 요약",
                one_line_summary="가" * 31,
                sentiment="neutral",
            )

    def test_schema_accepts_summary_at_30_character_boundary(self) -> None:
        render = BriefingRender(
            summary="상세 요약",
            one_line_summary="가" * 30,
            sentiment="neutral",
        )

        self.assertEqual(render.one_line_summary, "가" * 30)
