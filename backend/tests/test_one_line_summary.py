from unittest import TestCase

from pydantic import ValidationError

from app.schemas.llm import BriefingRender, MarketOverviewRender


class OneLineSummaryTest(TestCase):
    def test_briefing_summary_must_be_between_30_and_40_characters(self) -> None:
        for value in ("가" * 28 + ".", "가" * 40 + "."):
            with self.subTest(length=len(value)), self.assertRaises(ValidationError):
                BriefingRender(
                    summary="상세 요약",
                    one_line_summary=value,
                    sentiment="neutral",
                )

    def test_briefing_summary_accepts_both_length_boundaries(self) -> None:
        for value in ("가" * 29 + ".", "가" * 39 + "."):
            with self.subTest(length=len(value)):
                render = BriefingRender(
                    summary="상세 요약",
                    one_line_summary=value,
                    sentiment="neutral",
                )
                self.assertEqual(render.one_line_summary, value)

    def test_briefing_summary_must_be_a_complete_single_line_sentence(self) -> None:
        for value in ("가" * 35, "가" * 20 + "\n" + "나" * 14 + "."):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                BriefingRender(
                    summary="상세 요약",
                    one_line_summary=value,
                    sentiment="neutral",
                )

    def test_market_overview_uses_the_same_summary_rules(self) -> None:
        value = "가" * 34 + "."
        render = MarketOverviewRender(
            summary="상세 시황 요약",
            one_line_summary=value,
            sentiment="neutral",
        )

        self.assertEqual(render.one_line_summary, value)
