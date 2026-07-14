from unittest import TestCase

from app.services.llm.claude_client import RENDER_SYSTEM_PROMPT


class LlmPromptTest(TestCase):
    def test_briefing_render_requires_korean_for_all_user_visible_fields(self) -> None:
        self.assertIn("모두 자연스러운 한국어로 작성한다", RENDER_SYSTEM_PROMPT)
        self.assertIn("영어 문장이나 영어 설명을 사용하지 않는다", RENDER_SYSTEM_PROMPT)
        for field in (
            "summary",
            "one_line_summary",
            "positive_factors",
            "negative_factors",
            "watch_issues",
            "reasons",
            "today_actions",
            "disclaimer",
        ):
            self.assertIn(field, RENDER_SYSTEM_PROMPT)

        self.assertIn("source_url 필드에만", RENDER_SYSTEM_PROMPT)
        self.assertIn("source_url이 없는 내용은 reasons 항목으로 만들지 않는다", RENDER_SYSTEM_PROMPT)
