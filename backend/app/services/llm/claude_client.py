"""
Claude API 연동 스켈레톤 — 아직 미구현.

LLM API 종류/모델을 확정하면 이 파일만 채우면 된다:
1. requirements.txt 에 anthropic 패키지 추가
2. .env 의 ANTHROPIC_API_KEY 채우기
3. 아래 두 메서드에 실제 API 호출 구현
4. factory.py 에서 ANTHROPIC_API_KEY 존재 시 이 클래스를 반환하도록 주석 해제

시스템/유저 프롬프트 문구는 프롬프트템플릿.md 1단계·2단계 섹션 그대로 쓰면 된다.
"""

from app.schemas.llm import BriefingRender, FactsExtraction
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
"""


class ClaudeBriefingLLMClient(BriefingLLMClient):
    model_name = "claude-opus-4-8"  # TODO: 최종 모델 확정되면 교체

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        # TODO: anthropic.Anthropic(api_key=api_key) 클라이언트 초기화

    def extract_facts(
        self,
        *,
        source_type: str,
        tickers: list[str],
        document_text: str,
    ) -> FactsExtraction:
        # TODO:
        #   user_prompt = f"[문서 종류] {source_type}\n[관련 종목] {tickers}\n[문서 원문]\n{document_text}"
        #   응답을 anthropic 메시지 API로 호출 (FACTS_SYSTEM_PROMPT 사용)
        #   반환된 JSON 텍스트를 FactsExtraction.model_validate_json() 으로 파싱
        #   파싱 실패 시 1회 재시도 (프롬프트템플릿.md 4절 "Claude API 팁")
        raise NotImplementedError("Claude API 연동 전입니다 — LLM API 종류 확정 후 구현 예정")

    def render_briefing(
        self,
        *,
        facts: FactsExtraction,
        categories: list[str],
        preset_persona: str,
        depth: str,
        language: str,
    ) -> BriefingRender:
        # TODO:
        #   user_prompt 조립 (프롬프트템플릿.md 2단계 "User (렌즈 슬롯)" 형식)
        #   RENDER_SYSTEM_PROMPT 로 호출 후 BriefingRender.model_validate_json() 파싱
        raise NotImplementedError("Claude API 연동 전입니다 — LLM API 종류 확정 후 구현 예정")
