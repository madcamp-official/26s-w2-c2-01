"""
실제 LLM을 호출하지 않고 그럴듯한 더미 구조화 데이터를 만들어내는 스텁 구현.
실제 API(Claude 등)가 정해지기 전까지 파이프라인 전체(추출→렌더링→저장)를
end-to-end로 돌려보고 프론트와 통합 테스트하는 용도.
"""

from app.schemas.llm import BriefingRender, FactItem, FactsExtraction, MarketOverviewRender
from app.services.llm.base import BriefingLLMClient


class StubBriefingLLMClient(BriefingLLMClient):
    model_name = "stub-v1"

    def extract_facts(
        self,
        *,
        source_type: str,
        tickers: list[str],
        document_text: str,
    ) -> FactsExtraction:
        has_text = bool(document_text and document_text.strip())
        claim = (
            "입력 문서 내 관련 뉴스 발췌 (스텁 - 실제 LLM 미연동)"
            if has_text
            else "수집된 뉴스가 없어 참고할 근거가 없습니다 (스텁)"
        )
        return FactsExtraction(
            entities=tickers,
            key_issues=[f"{t} 관련 이슈 (스텁 더미 데이터)" for t in tickers],
            facts=[FactItem(claim=claim, evidence=document_text[:200] if has_text else "", source_url=None)],
            figures=[],
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
        tickers = facts.entities or ["종목"]
        ticker_label = ", ".join(tickers)
        return BriefingRender(
            one_line_summary="핵심 이슈와 변동 요인을 종합적으로 확인할 필요가 있습니다.",
            summary=(
                f"[스텁 브리핑] {ticker_label} 관련 실제 LLM 호출 없이 생성된 더미 요약입니다. "
                f"성향: {preset_persona[:30] if preset_persona else '기본'}..."
            ),
            sentiment="neutral",
            positive_factors=[],
            negative_factors=[],
            watch_issues=[f"{ticker_label} 관련 뉴스 직접 확인 필요 (LLM 파이프라인 미연동)"],
            # 실제 출처가 없는 더미 항목은 근거 목록에 넣지 않는다.
            reasons=[],
            today_actions=["LLM API 연동 후 실제 브리핑으로 교체 예정"],
        )

    def render_market_overview(self, *, facts: FactsExtraction) -> MarketOverviewRender:
        return MarketOverviewRender(
            one_line_summary="시장 핵심 이슈와 주요 변동 요인을 종합적으로 확인해야 합니다.",
            summary="[스텁 시황] 실제 LLM 호출 없이 생성된 더미 전체 시황 요약입니다.",
            sentiment="neutral",
            positive_factors=[],
            negative_factors=[],
            watch_issues=["LLM API 연동 후 실제 시황 브리핑으로 교체 예정"],
            reasons=[],
            today_actions=["실제 시장 뉴스 연결 상태 확인"],
            indices=[],
            sector_moves=[],
        )
