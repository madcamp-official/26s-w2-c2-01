from unittest import TestCase
from unittest.mock import patch

from app.services.llm.factory import get_llm_client


class LlmFactoryTest(TestCase):
    @patch("app.services.llm.factory.settings.OLLAMA_BASE_URL", "")
    @patch("app.services.llm.factory.settings.ANTHROPIC_API_KEY", "")
    @patch("app.services.llm.factory.settings.GEMINI_API_KEY", "test-key")
    @patch("app.services.llm.factory.settings.GEMINI_MODEL", "gemini-3.1-flash-lite")
    def test_configured_gemini_model_is_used(self) -> None:
        client = get_llm_client()

        self.assertEqual(client.model_name, "gemini-3.1-flash-lite")
