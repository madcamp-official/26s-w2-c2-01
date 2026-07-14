"""
Gemini API를 이용한 BriefingLLMClient 완전 구현.

원래는 1단계(팩트 추출) 전용이었으나 2단계(해석·렌더링)까지 지원하도록 확장했다.
1단계는 "사실만 기계적으로 뽑는" 단순 작업이라 로컬 Gemma2(Ollama)로 충분하고,
2단계(감성 판단·자연스러운 서술)는 더 어려운 추론이라 관리형 API가 유리하다는
판단으로 factory.py에서 Gemma2(1단계)+Gemini(2단계) 조합에도 이 클래스를 쓴다
(2026-07-14, 렌더링 속도 문제로 1·2단계 담당 스왑).

무료 티어는 분당 5회 제한이라 항목이 많은 새로고침에서 429가 날 수 있다 —
호출부(HybridBriefingLLMClient)가 실패 시 반대쪽 클라이언트로 폴백한다.
"""

from google import genai
from google.genai import types

from app.schemas.llm import BriefingRender, FactsExtraction, MarketOverviewRender
from app.services.llm.base import BriefingLLMClient
from app.services.llm.claude_client import (
    FACTS_SYSTEM_PROMPT,
    MARKET_SYSTEM_PROMPT,
    RENDER_SYSTEM_PROMPT,
)
from app.services.llm.errors import LLMQuotaExceededError
from app.services.llm.output_validation import find_malformed_strings, validate_render_output


class GeminiBriefingLLMClient(BriefingLLMClient):
    # 특정 버전(예: gemini-2.5-flash)을 고정하면 구글이 신규 프로젝트에 대해
    # 조용히 단종시킬 때(실측: 2026-07-14, 404 "no longer available to new
    # users") 매번 폴백만 타게 된다 — latest 별칭으로 그 문제를 피한다.
    model_name = "gemini-flash-latest"

    def __init__(self, api_key: str) -> None:
        self._client = genai.Client(api_key=api_key)

    def _generate(self, *, system_prompt: str, user_prompt: str, schema: type):
        """구조화 출력을 요청하고, 실패하면 1회만 재시도한다 (claude_client.py와 동일한 정책)."""
        last_error: Exception | None = None
        retry_prompt = user_prompt
        for _ in range(2):  # 최초 시도 + 1회 재시도
            try:
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=retry_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        response_schema=schema,
                    ),
                )
                if response.parsed is None:
                    raise RuntimeError(f"Gemini 응답 파싱 실패: {response.text!r:.500}")
                garbage = find_malformed_strings(response.parsed.model_dump())
                if garbage:
                    raise RuntimeError(f"깨진 출력 감지: {garbage[:2]!r}")
                return validate_render_output(response.parsed)
            except Exception as exc:  # noqa: BLE001 - 실패 시 재시도, 최종 실패는 위로 전파
                if (
                    getattr(exc, "status_code", None) == 429
                    or "RESOURCE_EXHAUSTED" in str(exc)
                ):
                    raise LLMQuotaExceededError() from exc
                last_error = exc
        raise RuntimeError(f"Gemini 호출 실패(재시도 포함): {last_error}") from last_error

    def extract_facts(
        self,
        *,
        source_type: str,
        tickers: list[str],
        document_text: str,
    ) -> FactsExtraction:
        user_prompt = (
            f"[문서 종류] {source_type}\n"
            f"[관련 종목] {', '.join(tickers) if tickers else '(미지정)'}\n"
            f"[문서 원문]\n{document_text or '(수집된 뉴스가 없습니다)'}"
        )
        return self._generate(
            system_prompt=FACTS_SYSTEM_PROMPT, user_prompt=user_prompt, schema=FactsExtraction
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
        user_prompt = (
            f"[분석 카테고리 focus] {', '.join(categories) if categories else '(미지정 — 전체 시장 관점)'}\n"
            f"[분석 성향] {preset_persona or '기본 — 균형 잡힌 시각으로 서술'}\n"
            f"[심층도] {depth}\n"
            f"[언어] {language}\n\n"
            f"[사실 데이터 facts JSON]\n{facts.model_dump_json()}"
        )
        return self._generate(
            system_prompt=RENDER_SYSTEM_PROMPT, user_prompt=user_prompt, schema=BriefingRender
        )

    def render_market_overview(self, *, facts: FactsExtraction) -> MarketOverviewRender:
        user_prompt = (
            "[출력 언어] 한국어\n"
            "[작성 지시] 모든 요약과 항목 설명을 한국어로 작성하세요.\n\n"
            f"[사실 데이터 facts JSON]\n{facts.model_dump_json()}"
        )
        return self._generate(
            system_prompt=MARKET_SYSTEM_PROMPT, user_prompt=user_prompt, schema=MarketOverviewRender
        )
