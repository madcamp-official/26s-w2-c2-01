from unittest import TestCase
from types import SimpleNamespace

from app.schemas.llm import BriefingRender, MarketOverviewRender
from app.services.llm.errors import LLMQuotaExceededError
from app.services.llm.gemini_client import GeminiBriefingLLMClient
from app.services.llm.output_validation import validate_one_line_summary, validate_render_output


class OneLineSummaryTest(TestCase):
    def test_briefing_summary_must_be_between_30_and_40_characters(self) -> None:
        for value in ("가" * 28 + ".", "가" * 40 + "."):
            with self.subTest(length=len(value)), self.assertRaises(ValueError):
                validate_one_line_summary(value)

    def test_briefing_summary_accepts_both_length_boundaries(self) -> None:
        for value in ("가" * 29 + ".", "가" * 39 + "."):
            with self.subTest(length=len(value)):
                self.assertEqual(validate_one_line_summary(value), value)

    def test_briefing_summary_must_be_a_complete_single_line_sentence(self) -> None:
        for value in ("가" * 35, "가" * 20 + "\n" + "나" * 14 + "."):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_one_line_summary(value)

    def test_provider_schemas_do_not_contain_unsupported_string_lengths(self) -> None:
        for schema in (BriefingRender, MarketOverviewRender):
            field_schema = schema.model_json_schema()["properties"]["one_line_summary"]
            with self.subTest(schema=schema.__name__):
                self.assertNotIn("minLength", field_schema)
                self.assertNotIn("maxLength", field_schema)

    def test_market_overview_rejects_short_summary(self) -> None:
        render = MarketOverviewRender(
            summary="시장이 상승했습니다.",
            one_line_summary="핵심 이슈와 변동 요인을 종합적으로 확인할 필요가 있습니다.",
            sentiment="neutral",
        )
        with self.assertRaisesRegex(ValueError, "at least 300 characters"):
            validate_render_output(render)

    def test_market_overview_rejects_english_user_visible_text(self) -> None:
        render = MarketOverviewRender(
            summary="한국어 시황 요약입니다. " * 25,
            one_line_summary="핵심 이슈와 변동 요인을 종합적으로 확인할 필요가 있습니다.",
            sentiment="neutral",
            positive_factors=["Technology stocks rallied."],
        )
        with self.assertRaisesRegex(ValueError, "positive_factors must be written in Korean"):
            validate_render_output(render)

    def test_gemini_retries_with_correction_when_summary_is_invalid(self) -> None:
        invalid = BriefingRender(
            summary="상세 요약",
            one_line_summary="짧은 요약입니다.",
            sentiment="neutral",
        )
        valid = BriefingRender(
            summary="상세 요약",
            one_line_summary="핵심 이슈와 변동 요인을 종합적으로 확인할 필요가 있습니다.",
            sentiment="neutral",
        )

        class FakeModels:
            def __init__(self) -> None:
                self.calls = []

            def generate_content(self, **kwargs):
                self.calls.append(kwargs)
                parsed = invalid if len(self.calls) == 1 else valid
                return SimpleNamespace(parsed=parsed, text="")

        client = GeminiBriefingLLMClient.__new__(GeminiBriefingLLMClient)
        client._client = SimpleNamespace(models=FakeModels())

        result = client._generate(
            system_prompt="system",
            user_prompt="original prompt",
            schema=BriefingRender,
        )

        self.assertEqual(result.one_line_summary, valid.one_line_summary)
        self.assertEqual(len(client._client.models.calls), 2)
        self.assertIn("한 줄 요약 재작성", client._client.models.calls[1]["contents"])

    def test_gemini_quota_error_is_not_retried(self) -> None:
        class QuotaError(Exception):
            status_code = 429

        class FakeModels:
            def __init__(self) -> None:
                self.calls = 0

            def generate_content(self, **kwargs):
                del kwargs
                self.calls += 1
                raise QuotaError("RESOURCE_EXHAUSTED")

        client = GeminiBriefingLLMClient.__new__(GeminiBriefingLLMClient)
        client._client = SimpleNamespace(models=FakeModels())

        with self.assertRaises(LLMQuotaExceededError):
            client._generate(
                system_prompt="system",
                user_prompt="original prompt",
                schema=BriefingRender,
            )

        self.assertEqual(client._client.models.calls, 1)
