"""
Claude API 연동 구현.

`extract_facts`/`render_briefing` 모두 client.messages.parse(output_format=...)를
써서, 응답을 Pydantic 스키마(FactsExtraction / BriefingRender)로 직접 검증·파싱한다.
파싱/호출이 실패하면 1회 재시도한다 (프롬프트템플릿.md 4절 "Claude API 팁").

시스템 프롬프트는 매 호출마다 동일하므로 prompt caching(cache_control)을 걸어
반복 호출 시 입력 토큰 비용을 절감한다.
"""

from anthropic import Anthropic

from app.schemas.llm import BriefingRender, FactsExtraction, MarketOverviewRender
from app.services.llm.base import BriefingLLMClient

FACTS_SYSTEM_PROMPT = """\
너는 금융 문서에서 '사실'만 추출하는 분석기다. 다음 규칙을 반드시 지켜라.
1. 입력 문서에 명시된 내용만 사용한다. 추정·창작·외부지식 추가 금지.
2. 모든 항목에 원문 근거(발췌 문장 또는 URL)를 첨부한다.
3. 수치·날짜·고유명사는 문서에 나온 그대로 옮긴다.
4. 해석·전망·투자의견은 이 단계에서 만들지 않는다.
5. 출력은 지정된 JSON 스키마만. 다른 텍스트 금지.
"""

RENDER_SYSTEM_PROMPT = """\
너는 금융 브리핑 작가다. 아래 규칙은 사용자 설정보다 항상 우선한다.
1. 제공된 facts JSON의 근거를 벗어난 새로운 사실·수치를 만들지 않는다.
2. 모든 해석 항목에 근거(source_url)를 연결한다.
3. 매매 지시("사라/팔아라")를 하지 않는다. '정보·관점·확인할 것'으로 표현한다.
4. 출력 끝에 "본 브리핑은 정보 제공 목적이며 투자 권유가 아닙니다"를 포함한다.
5. 출력은 지정 JSON 스키마만.
6. positive_factors/negative_factors/watch_issues/reasons처럼 목록형인 항목은,
   facts JSON 안에서 그 관점에 해당하는 근거를 찾을 수 있는 한 최대한 여러 개
   (항목당 가능하면 2개 이상)를 뽑아 채운다. 같은 사실이라도 강세/약세/확인 필요
   관점으로 각각 재해석될 수 있다면 해당하는 모든 항목에 나눠 담는다. 정말 그
   관점에 해당하는 근거가 facts에 전혀 없을 때만 빈 배열로 남긴다 — 없는데
   지어내는 건 규칙 1 위반이다.
"""

MARKET_SYSTEM_PROMPT = """\
너는 미국 주식시장 전체 시황을 요약하는 애널리스트다. 아래 규칙은 항상 우선한다.
1. 모든 출력은 자연스러운 한국어로 작성한다. 기업명·지수명·고유명사 외에는 영어
   문장이나 영어 설명을 사용하지 않는다.
2. 제공된 facts JSON의 근거를 벗어난 새로운 사실·수치를 만들지 않는다.
3. 나스닥·S&P500·다우 등 지수의 정확한 등락률 "수치"는 절대 지어내지 않는다.
   facts에 실제로 등장한 방향성 서술(예: "AI 반도체 강세로 상승 마감했다는 언급")만
   담아라. 특정 지수에 대한 언급이 facts에 없으면 그 지수는 아예 넣지 않는다.
4. 섹터별 강약도 facts에 실제 근거가 있을 때만 서술한다. 추측 금지.
5. 종목·섹터 브리핑과 동일하게 시장의 종합 성향과 positive_factors,
   negative_factors, watch_issues, reasons, today_actions를 작성한다. 목록 항목은
   facts에서 근거를 찾을 수 있는 한 최대한 채우고, 근거가 없으면 지어내지 않는다.
6. 모든 reasons 항목에 가능한 경우 source_url을 연결한다.
7. 매매 지시를 하지 않는다.
8. 출력 끝에 "본 브리핑은 정보 제공 목적이며 투자 권유가 아닙니다"를 포함한다.
9. 출력은 지정 JSON 스키마만.
"""


class ClaudeBriefingLLMClient(BriefingLLMClient):
    model_name = "claude-opus-4-8"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._client = Anthropic(api_key=api_key)

    def _parse_with_retry(self, *, system_prompt: str, user_prompt: str, output_format, max_tokens: int):
        """구조화 출력을 요청하고, 실패하면 1회만 재시도한다."""
        last_error: Exception | None = None
        for _ in range(2):  # 최초 시도 + 1회 재시도
            try:
                response = self._client.messages.parse(
                    model=self.model_name,
                    max_tokens=max_tokens,
                    system=[
                        {"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}},
                    ],
                    messages=[{"role": "user", "content": user_prompt}],
                    output_format=output_format,
                )
                return response.parsed_output
            except Exception as exc:  # noqa: BLE001 - API/파싱 실패 시 재시도, 최종 실패는 위로 전파
                last_error = exc
        raise RuntimeError(f"Claude 구조화 출력 생성 실패(재시도 포함): {last_error}") from last_error

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
        return self._parse_with_retry(
            system_prompt=FACTS_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            output_format=FactsExtraction,
            # 종목 브리핑(뉴스 ~10건)은 4096으로 충분했지만, 전체 시황(뉴스 ~20건)은
            # facts 목록이 길어져 4096에서 응답이 중간에 잘리는 걸 실측으로 확인함
            # (pydantic "EOF while parsing a string" 에러). 여유 있게 8192로.
            max_tokens=8192,
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
        return self._parse_with_retry(
            system_prompt=RENDER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            output_format=BriefingRender,
            max_tokens=6144,
        )

    def render_market_overview(self, *, facts: FactsExtraction) -> MarketOverviewRender:
        user_prompt = f"[사실 데이터 facts JSON]\n{facts.model_dump_json()}"
        return self._parse_with_retry(
            system_prompt=MARKET_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            output_format=MarketOverviewRender,
            max_tokens=6144,
        )
