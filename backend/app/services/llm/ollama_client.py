"""
자체 ML 서버(Ollama, Gemma2)를 이용한 BriefingLLMClient 구현.

claude_client.py와 시스템 프롬프트를 그대로 재사용한다 — 모델만 바뀌었을 뿐
"사실만 근거와 함께 추출/렌더링한다"는 규칙 자체는 동일하게 지켜야 하기 때문.
Ollama의 /api/chat에 Pydantic 스키마(JSON Schema)를 format으로 넘겨 구조화
출력을 강제한다(Ollama 0.5+에서 지원).

Gemma2(9B)는 JSON 스키마 강제 디코딩 중 가끔 문자열 필드 안에 다른 필드
구조(예: "... (source_url: null)", "],")를 흘려보내는 걸 실측으로 확인했다
(2026-07-14, CLSK 브리핑 negative_factors에서 발견). Pydantic은 타입만
맞으면(문자열이면) 통과시키므로 이런 깨진 내용을 걸러내지 못한다 — 그래서
파싱 후 별도로 내용을 검사해 깨진 게 보이면 실패로 취급하고 재시도한다.
"""

from __future__ import annotations

import re

import httpx

from app.schemas.llm import BriefingRender, FactsExtraction, MarketOverviewRender
from app.services.llm.base import BriefingLLMClient
from app.services.llm.claude_client import (
    FACTS_SYSTEM_PROMPT,
    MARKET_SYSTEM_PROMPT,
    RENDER_SYSTEM_PROMPT,
)

# 순수 구두점/괄호 파편("],", "},", "]" 등)이거나, 다른 필드명이 문자열 안에
# 그대로 새어나온 경우(예: "(source_url: null)")를 깨진 출력으로 간주한다.
_PUNCTUATION_ONLY = re.compile(r"^[\]\}\[\{,:;\s\"'\.]+$")
_LEAKED_FIELD_NAME = re.compile(r"\bsource_url\b")
# positive_factors/negative_factors/watch_issues/today_actions는 설명 문장이어야
# 하는데, reasons에 들어가야 할 URL 하나만(괄호로 감싼 형태 포함) 새어나오는
# 경우도 같은 계열의 깨진 출력이다 — 실측: "(https://finnhub.io/...)" 단독 항목.
_BARE_URL_ONLY = re.compile(r"^\(?https?://\S+\)?$")


def _find_malformed_strings(value: object) -> list[str]:
    """파싱된 결과를 재귀적으로 훑어 깨진 문자열 조각을 찾는다."""
    found: list[str] = []
    if isinstance(value, str):
        stripped = value.strip()
        if stripped and (
            _PUNCTUATION_ONLY.match(stripped)
            or _LEAKED_FIELD_NAME.search(stripped)
            or _BARE_URL_ONLY.match(stripped)
        ):
            found.append(value)
    elif isinstance(value, dict):
        for v in value.values():
            found.extend(_find_malformed_strings(v))
    elif isinstance(value, list):
        for v in value:
            found.extend(_find_malformed_strings(v))
    return found


class OllamaBriefingLLMClient(BriefingLLMClient):
    def __init__(self, *, base_url: str, model: str = "gemma2:9b", timeout: float = 120.0) -> None:
        self.model_name = model
        self._client = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout)

    def _chat(self, *, system_prompt: str, user_prompt: str, schema: type):
        """구조화 출력을 요청하고, 실패하면 1회만 재시도한다 (claude_client.py와 동일한 정책)."""
        last_error: Exception | None = None
        for _ in range(2):  # 최초 시도 + 1회 재시도
            try:
                resp = self._client.post(
                    "/api/chat",
                    json={
                        "model": self.model_name,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "format": schema.model_json_schema(),
                        "options": {"temperature": 0},
                        "stream": False,
                    },
                )
                resp.raise_for_status()
                content = resp.json()["message"]["content"]
                parsed = schema.model_validate_json(content)
                garbage = _find_malformed_strings(parsed.model_dump())
                if garbage:
                    raise RuntimeError(f"깨진 출력 감지: {garbage[:2]!r}")
                return parsed
            except Exception as exc:  # noqa: BLE001 - API/파싱/검증 실패 시 재시도, 최종 실패는 위로 전파
                last_error = exc
        raise RuntimeError(f"Ollama 구조화 출력 생성 실패(재시도 포함): {last_error}") from last_error

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
        return self._chat(system_prompt=FACTS_SYSTEM_PROMPT, user_prompt=user_prompt, schema=FactsExtraction)

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
        return self._chat(system_prompt=RENDER_SYSTEM_PROMPT, user_prompt=user_prompt, schema=BriefingRender)

    def render_market_overview(self, *, facts: FactsExtraction) -> MarketOverviewRender:
        user_prompt = f"[사실 데이터 facts JSON]\n{facts.model_dump_json()}"
        return self._chat(system_prompt=MARKET_SYSTEM_PROMPT, user_prompt=user_prompt, schema=MarketOverviewRender)
