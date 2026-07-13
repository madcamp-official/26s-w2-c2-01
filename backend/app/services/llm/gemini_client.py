"""
Gemini API를 이용한 1단계(팩트 추출) 전용 구현.

Claude 대비 비용 절감이 목적: extract_facts는 '사실만 중립적으로 뽑는' 기계적인
단계라 Gemini 무료 티어로도 충분하다고 판단, render_briefing/render_market_overview
(해석·페르소나 반영 단계)만 Claude에 남기고 이 단계만 대체한다.
실제 조합은 HybridBriefingLLMClient(factory.py)에서 이 클래스 + ClaudeBriefingLLMClient를
합성해 만든다 — 이 클래스 자체는 extract_facts만 구현한다.
"""

from google import genai
from google.genai import types

from app.schemas.llm import FactsExtraction

FACTS_SYSTEM_PROMPT = """\
너는 금융 문서에서 '사실'만 추출하는 분석기다. 다음 규칙을 반드시 지켜라.
1. 입력 문서에 명시된 내용만 사용한다. 추정·창작·외부지식 추가 금지.
2. 모든 항목에 원문 근거(발췌 문장 또는 URL)를 첨부한다.
3. 수치·날짜·고유명사는 문서에 나온 그대로 옮긴다.
4. 해석·전망·투자의견은 이 단계에서 만들지 않는다.
5. 출력은 지정된 JSON 스키마만. 다른 텍스트 금지.
"""


class GeminiFactsExtractor:
    """extract_facts만 담당하는 좁은 컴포넌트. BriefingLLMClient 전체를 구현하지 않는다 —
    render_* 단계는 여전히 Claude가 맡으므로 이 클래스를 단독으로 파이프라인에 꽂지 않는다."""

    model_name = "gemini-2.5-flash"

    def __init__(self, api_key: str) -> None:
        self._client = genai.Client(api_key=api_key)

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
        last_error: Exception | None = None
        for _ in range(2):  # 최초 시도 + 1회 재시도 (claude_client.py와 동일한 정책)
            try:
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=FACTS_SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        response_schema=FactsExtraction,
                    ),
                )
                if response.parsed is None:
                    raise RuntimeError(f"Gemini 응답 파싱 실패: {response.text!r:.500}")
                return response.parsed
            except Exception as exc:  # noqa: BLE001 - 실패 시 재시도, 최종 실패는 위로 전파
                last_error = exc
        raise RuntimeError(f"Gemini 팩트 추출 실패(재시도 포함): {last_error}") from last_error
