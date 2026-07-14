from app.core.config import settings
from app.services.llm.base import BriefingLLMClient
from app.services.llm.claude_client import ClaudeBriefingLLMClient
from app.services.llm.gemini_client import GeminiBriefingLLMClient
from app.services.llm.hybrid_client import HybridBriefingLLMClient
from app.services.llm.ollama_client import OllamaBriefingLLMClient
from app.services.llm.stub_client import StubBriefingLLMClient


def get_llm_client() -> BriefingLLMClient:
    """
    파이프라인이 사용할 LLM 클라이언트를 반환. 우선순위:

    1. GEMINI_API_KEY + OLLAMA_BASE_URL: 하이브리드(팩트 추출=자체 ML 서버의
       Ollama/Gemma2, 렌더링=Gemini) — Claude 호출이 아예 없어진다. 1단계는
       "사실만 기계적으로 뽑는" 단순 작업이라 로컬 모델로 충분하고, 2단계(감성
       판단·서술)는 더 어려운 추론이라 관리형 API가 유리하다는 판단
       (2026-07-14, Gemma2 단독 렌더링이 JSON 스키마 강제 디코딩 때문에
       너무 느려서 1·2단계 담당을 스왑함).
    2. ANTHROPIC_API_KEY + GEMINI_API_KEY: 하이브리드(팩트 추출=Gemini, 렌더링=Claude).
    3. OLLAMA_BASE_URL만: 1·2단계 둘 다 Ollama/Gemma2.
    4. ANTHROPIC_API_KEY만: Claude 단독.
    5. GEMINI_API_KEY만: Gemini 단독.
    6. 아무 키도 없으면: 스텁 — 앱 전체가 죽지 않고 더미 데이터로 계속 동작한다.
    """
    if settings.GEMINI_API_KEY and settings.OLLAMA_BASE_URL:
        return HybridBriefingLLMClient(
            facts_client=OllamaBriefingLLMClient(
                base_url=settings.OLLAMA_BASE_URL, model=settings.OLLAMA_MODEL
            ),
            render_client=GeminiBriefingLLMClient(api_key=settings.GEMINI_API_KEY),
        )
    if settings.ANTHROPIC_API_KEY and settings.GEMINI_API_KEY:
        return HybridBriefingLLMClient(
            facts_client=GeminiBriefingLLMClient(api_key=settings.GEMINI_API_KEY),
            render_client=ClaudeBriefingLLMClient(api_key=settings.ANTHROPIC_API_KEY),
        )
    if settings.OLLAMA_BASE_URL:
        return OllamaBriefingLLMClient(base_url=settings.OLLAMA_BASE_URL, model=settings.OLLAMA_MODEL)
    if settings.ANTHROPIC_API_KEY:
        return ClaudeBriefingLLMClient(api_key=settings.ANTHROPIC_API_KEY)
    if settings.GEMINI_API_KEY:
        return GeminiBriefingLLMClient(api_key=settings.GEMINI_API_KEY)
    return StubBriefingLLMClient()
