"""
LLM 렌더링 결과에서 RENDER_SYSTEM_PROMPT 규칙을 어긴 흔적을 찾는 공용 검증기.

Ollama(Gemma2)뿐 아니라 Gemini도 구조화 출력 중 이 규칙(URL은 reasons[].source_url
에만, 다른 필드명이 문장에 새어나오면 안 됨)을 가끔 어기는 걸 실측으로 확인했다
(2026-07-14, IBM 브리핑에서 Gemini가 직접 만든 결과에도 발생 — 폴백 로그 없이
model=gemini-flash-latest로 저장됨). Pydantic 스키마 검증은 타입만 보고 내용은
안 보므로, 파싱 후 이 검증을 추가로 거쳐야 한다. Claude/Gemini/Ollama 클라이언트
모두 이 함수를 재사용한다.
"""

from __future__ import annotations

import re

# 순수 구두점/괄호 파편("],", "},", "]" 등)이거나, 다른 필드명이 문자열 안에
# 그대로 새어나온 경우(예: "(source_url: null)")를 깨진 출력으로 간주한다.
_PUNCTUATION_ONLY = re.compile(r"^[\]\}\[\{,:;\s\"'\.]+$")
_LEAKED_FIELD_NAME = re.compile(r"\bsource_url\b")
# RENDER_SYSTEM_PROMPT 규칙: URL은 reasons[].source_url에만 허용되고, 그 외
# 사람이 읽는 문장(summary/factor/explain/positive_factors/... )에는 절대
# 들어가면 안 된다 — 실측: "...했습니다. (source_url: https://...)"처럼 문장
# 뒤에 URL이 그대로 붙어나오는 경우.
_URL_PATTERN = re.compile(r"https?://")

ONE_LINE_SUMMARY_RETRY_INSTRUCTION = """
[한 줄 요약 재작성]
직전 응답의 one_line_summary가 검증에 실패했습니다. 다른 필드의 형식은 유지하면서
one_line_summary를 줄바꿈 없는 완결된 한국어 한 문장으로 다시 작성하세요.
공백과 마지막 문장부호를 포함해 반드시 30자 이상 40자 이하이어야 하며,
마침표·느낌표·물음표 중 하나로 끝내세요. 중간에서 자르거나 말줄임표를 쓰지 마세요.
""".strip()


def validate_one_line_summary(value: str) -> str:
    """Validate business rules after LLM parsing, outside provider JSON Schema."""
    if "\n" in value or "\r" in value:
        raise ValueError("one_line_summary must not contain line breaks")
    normalized = re.sub(r"\s+", " ", value).strip()
    length = len(normalized)
    if not 30 <= length <= 40:
        raise ValueError(f"one_line_summary must be 30-40 characters, got {length}")
    if not normalized.endswith((".", "!", "?")):
        raise ValueError("one_line_summary must end with sentence punctuation")
    return normalized


def validate_render_output(value: object) -> object:
    """Normalize and validate one-line summaries only on render-stage outputs."""
    if hasattr(value, "one_line_summary"):
        value.one_line_summary = validate_one_line_summary(value.one_line_summary)
    return value


def find_malformed_strings(value: object, *, url_allowed: bool = False) -> list[str]:
    """파싱된 결과를 재귀적으로 훑어 깨진 문자열 조각을 찾는다.

    url_allowed는 지금 보는 값이 reasons[].source_url처럼 URL이 정상적으로
    들어가는 자리인지를 나타낸다 — 그 자리가 아니면 URL이 섞인 것 자체가 오류.
    """
    found: list[str] = []
    if isinstance(value, str):
        stripped = value.strip()
        if stripped and (
            _PUNCTUATION_ONLY.match(stripped)
            or _LEAKED_FIELD_NAME.search(stripped)
            or (not url_allowed and _URL_PATTERN.search(stripped))
        ):
            found.append(value)
    elif isinstance(value, dict):
        for key, v in value.items():
            found.extend(find_malformed_strings(v, url_allowed=(key == "source_url")))
    elif isinstance(value, list):
        for v in value:
            found.extend(find_malformed_strings(v, url_allowed=url_allowed))
    return found
