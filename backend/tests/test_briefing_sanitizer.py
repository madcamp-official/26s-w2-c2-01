from unittest import TestCase

from app.schemas.llm import BriefingRender, ReasonItem
from app.services.briefing_sanitizer import sanitize_briefing_render


class BriefingSanitizerTest(TestCase):
    def test_urls_are_removed_from_visible_text_but_kept_as_citation(self) -> None:
        render = BriefingRender(
            summary="요약 https://example.com/raw",
            sentiment="neutral",
            positive_factors=["[실적 개선](https://example.com/markdown)"],
            reasons=[
                ReasonItem(
                    factor="근거 https://example.com/inside",
                    impact="긍정",
                    explain="설명 https://example.com/inside",
                    source_url="https://example.com/source",
                )
            ],
        )

        cleaned = sanitize_briefing_render(render)

        self.assertEqual(cleaned.summary, "요약")
        self.assertEqual(cleaned.positive_factors, ["실적 개선"])
        self.assertEqual(cleaned.reasons[0].factor, "근거")
        self.assertEqual(cleaned.reasons[0].source_url, "https://example.com/source")

    def test_reason_without_source_url_is_removed(self) -> None:
        render = BriefingRender(
            summary="요약",
            sentiment="neutral",
            reasons=[
                ReasonItem(factor="출처 없음", impact="중립", explain="설명", source_url=None),
                ReasonItem(
                    factor="출처 있음",
                    impact="중립",
                    explain="설명",
                    source_url="https://example.com/source",
                ),
            ],
        )

        cleaned = sanitize_briefing_render(render)

        self.assertEqual(len(cleaned.reasons), 1)
        self.assertEqual(cleaned.reasons[0].factor, "출처 있음")
