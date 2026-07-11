"""
LLM 파이프라인 인터페이스. 어떤 LLM API를 쓸지 아직 정하지 않았으므로,
파이프라인(briefing_pipeline.py)은 이 추상 인터페이스에만 의존한다.
API가 정해지면 이 인터페이스를 구현하는 새 클라이언트 클래스를 하나
추가하고 factory.py 에서 그걸 반환하도록 바꾸면 된다. (예: claude_client.py)
"""

from abc import ABC, abstractmethod

from app.schemas.llm import BriefingRender, FactsExtraction


class BriefingLLMClient(ABC):
    #: daily_briefings.model 컬럼에 기록될 이름 (예: "claude-opus-4-8", "stub-v1")
    model_name: str

    @abstractmethod
    def extract_facts(
        self,
        *,
        source_type: str,
        tickers: list[str],
        document_text: str,
    ) -> FactsExtraction:
        """1단계 · 팩트 추출. 프롬프트템플릿.md '1단계' 섹션 참고."""
        raise NotImplementedError

    @abstractmethod
    def render_briefing(
        self,
        *,
        facts: FactsExtraction,
        categories: list[str],
        preset_persona: str,
        depth: str,
        language: str,
    ) -> BriefingRender:
        """2단계 · 성향 렌더링. 프롬프트템플릿.md '2단계' 섹션 참고."""
        raise NotImplementedError
