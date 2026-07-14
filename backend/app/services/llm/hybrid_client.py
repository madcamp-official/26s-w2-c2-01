"""
1단계(팩트 추출)와 2단계(해석·렌더링)를 서로 다른 LLM으로 분리해서 쓰는 조합.

두 단계 다 같은 모델(Claude 단독)을 쓰는 것보다 비용을 낮추는 게 목적
(2026-07-14 비용 문의 후 도입). facts_client/render_client는 둘 다
BriefingLLMClient 전체 인터페이스(extract_facts/render_briefing/
render_market_overview)를 구현한 객체를 받는다 — factory.py가 실제
조합(Gemini+Claude, Gemini+Ollama 등)을 결정한다.

facts_client 호출이 실패하면(무료 티어 rate limit, 일시 장애 등) 그 즉시
render_client의 extract_facts로 폴백한다 — 브리핑 생성 자체가 죽는 것보다
그 요청만 비용이 원래대로 돌아가는 게 낫다는 판단.
"""

from app.schemas.llm import BriefingRender, FactsExtraction, MarketOverviewRender
from app.services.llm.base import BriefingLLMClient


class HybridBriefingLLMClient(BriefingLLMClient):
    def __init__(self, *, facts_client: BriefingLLMClient, render_client: BriefingLLMClient) -> None:
        self._facts = facts_client
        self._render = render_client
        self.model_name = f"{facts_client.model_name}+{render_client.model_name}"

    def extract_facts(
        self,
        *,
        source_type: str,
        tickers: list[str],
        document_text: str,
    ) -> FactsExtraction:
        try:
            return self._facts.extract_facts(
                source_type=source_type, tickers=tickers, document_text=document_text
            )
        except Exception as exc:  # noqa: BLE001 - 1단계 클라이언트 장애 시 2단계 클라이언트로 폴백
            print(f"1단계(팩트 추출) 실패, 2단계 클라이언트로 폴백: {exc}")
            return self._render.extract_facts(
                source_type=source_type, tickers=tickers, document_text=document_text
            )

    def render_briefing(
        self,
        *,
        facts: FactsExtraction,
        categories: list[str],
        preset_persona: str,
        depth: str,
        language: str,
    ) -> BriefingRender:
        return self._render.render_briefing(
            facts=facts, categories=categories, preset_persona=preset_persona,
            depth=depth, language=language,
        )

    def render_market_overview(self, *, facts: FactsExtraction) -> MarketOverviewRender:
        return self._render.render_market_overview(facts=facts)
