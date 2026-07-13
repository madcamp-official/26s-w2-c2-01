"""
1단계(팩트 추출)는 Gemini(무료 티어), 2단계(해석·렌더링)는 Claude를 쓰는 조합.
Claude 단독 대비 종목/섹터/시황 브리핑 1건당 Claude 호출을 2회 -> 1회로 줄여
토큰 비용을 대략 절반으로 낮추는 게 목적 (2026-07-14 비용 문의 후 도입).

Gemini 호출이 실패하면(무료 티어 rate limit, 일시 장애 등) 그 즉시 Claude의
extract_facts로 폴백한다 — 브리핑 생성 자체가 죽는 것보다 그날만 비용이 원래대로
돌아가는 게 낫다는 판단.
"""

from app.schemas.llm import BriefingRender, FactsExtraction, MarketOverviewRender
from app.services.llm.base import BriefingLLMClient
from app.services.llm.claude_client import ClaudeBriefingLLMClient
from app.services.llm.gemini_client import GeminiFactsExtractor


class HybridBriefingLLMClient(BriefingLLMClient):
    def __init__(self, *, anthropic_api_key: str, gemini_api_key: str) -> None:
        self._claude = ClaudeBriefingLLMClient(api_key=anthropic_api_key)
        self._gemini_facts = GeminiFactsExtractor(api_key=gemini_api_key)
        self.model_name = f"{self._gemini_facts.model_name}+{self._claude.model_name}"

    def extract_facts(
        self,
        *,
        source_type: str,
        tickers: list[str],
        document_text: str,
    ) -> FactsExtraction:
        try:
            return self._gemini_facts.extract_facts(
                source_type=source_type, tickers=tickers, document_text=document_text
            )
        except Exception as exc:  # noqa: BLE001 - Gemini 장애 시 Claude로 폴백
            print(f"Gemini 팩트 추출 실패, Claude로 폴백: {exc}")
            return self._claude.extract_facts(
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
        return self._claude.render_briefing(
            facts=facts, categories=categories, preset_persona=preset_persona,
            depth=depth, language=language,
        )

    def render_market_overview(self, *, facts: FactsExtraction) -> MarketOverviewRender:
        return self._claude.render_market_overview(facts=facts)
