from app.core.config import settings
from app.services.llm.base import BriefingLLMClient
from app.services.llm.claude_client import ClaudeBriefingLLMClient
from app.services.llm.stub_client import StubBriefingLLMClient


def get_llm_client() -> BriefingLLMClient:
    """
    파이프라인이 사용할 LLM 클라이언트를 반환.

    ANTHROPIC_API_KEY가 설정돼 있으면 실제 Claude를, 없으면(빈 문자열)
    스텁을 반환한다 — 키가 아직 없어도 앱 전체가 죽지 않고 더미 데이터로
    계속 동작한다.
    """
    if settings.ANTHROPIC_API_KEY:
        return ClaudeBriefingLLMClient(api_key=settings.ANTHROPIC_API_KEY)
    return StubBriefingLLMClient()
