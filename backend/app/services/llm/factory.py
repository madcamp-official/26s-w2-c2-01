from app.services.llm.base import BriefingLLMClient
from app.services.llm.stub_client import StubBriefingLLMClient


def get_llm_client() -> BriefingLLMClient:
    """
    파이프라인이 사용할 LLM 클라이언트를 반환.

    LLM API 종류가 아직 정해지지 않아 항상 스텁을 반환한다.
    ClaudeBriefingLLMClient(claude_client.py)의 두 메서드 구현이 끝나면
    아래 주석을 해제해서 ANTHROPIC_API_KEY 유무로 분기하면 된다.

        from app.core.config import settings
        from app.services.llm.claude_client import ClaudeBriefingLLMClient
        if settings.ANTHROPIC_API_KEY:
            return ClaudeBriefingLLMClient(api_key=settings.ANTHROPIC_API_KEY)
    """
    return StubBriefingLLMClient()
