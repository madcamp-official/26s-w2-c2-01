from app.core.config import settings
from app.services.llm.base import BriefingLLMClient
from app.services.llm.claude_client import ClaudeBriefingLLMClient
from app.services.llm.hybrid_client import HybridBriefingLLMClient
from app.services.llm.stub_client import StubBriefingLLMClient


def get_llm_client() -> BriefingLLMClient:
    """
    파이프라인이 사용할 LLM 클라이언트를 반환.

    ANTHROPIC_API_KEY + GEMINI_API_KEY가 둘 다 설정돼 있으면 하이브리드
    (팩트 추출=Gemini, 렌더링=Claude)를, ANTHROPIC_API_KEY만 있으면 Claude 단독을,
    둘 다 없으면(빈 문자열) 스텁을 반환한다 — 키가 아직 없어도 앱 전체가 죽지 않고
    더미 데이터로 계속 동작한다.
    """
    if settings.ANTHROPIC_API_KEY and settings.GEMINI_API_KEY:
        return HybridBriefingLLMClient(
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            gemini_api_key=settings.GEMINI_API_KEY,
        )
    if settings.ANTHROPIC_API_KEY:
        return ClaudeBriefingLLMClient(api_key=settings.ANTHROPIC_API_KEY)
    return StubBriefingLLMClient()
