"""
LLM 파이프라인 입출력 스키마. 프롬프트템플릿.md 의 1단계/2단계 출력 구조를
daily_briefings 테이블 컬럼(DB스키마.md 2-7)에 맞춰 정리한 것.
"""

from typing import Literal

from pydantic import BaseModel


class FactItem(BaseModel):
    claim: str
    evidence: str
    source_url: str | None = None


class FigureItem(BaseModel):
    name: str
    value: str
    source_url: str | None = None


class FactsExtraction(BaseModel):
    """1단계 · 팩트 추출 결과 (중립·사실만, 캐싱 대상)."""

    entities: list[str] = []
    key_issues: list[str] = []
    facts: list[FactItem] = []
    figures: list[FigureItem] = []


class ReasonItem(BaseModel):
    """daily_briefings.reasons 컬럼 원소 — 근거 있는 서술 강제용."""

    factor: str
    impact: Literal["긍정", "부정", "중립"]
    explain: str
    source_url: str | None = None


class MarketMoveItem(BaseModel):
    """Gemini 구조화 출력과 호환되는 지수·섹터 동향 항목."""

    name: str
    description: str


class BriefingRender(BaseModel):
    """2단계 · 성향 렌더링 결과. daily_briefings 테이블에 그대로 저장된다."""

    summary: str
    one_line_summary: str
    sentiment: Literal["positive", "neutral", "negative"]
    positive_factors: list[str] = []
    negative_factors: list[str] = []
    watch_issues: list[str] = []
    reasons: list[ReasonItem] = []
    today_actions: list[str] = []
    disclaimer: str = "본 브리핑은 정보 제공 목적이며 투자 권유가 아닙니다."

class MarketOverviewRender(BaseModel):
    """
    전체 시황 렌더링 결과. market_overviews 테이블에 저장된다.

    Finnhub 무료 티어는 지수 시세(나스닥 등)를 안 주므로, indices/sector_moves는
    "뉴스에 실제로 언급된 방향성 서술"만 담는다 — 정확한 등락률 수치를 지어내지
    않는다(환각 방지). 언급이 없는 지수/섹터는 아예 키를 안 넣어도 된다.
    """

    summary: str
    one_line_summary: str
    sentiment: Literal["positive", "neutral", "negative"]
    positive_factors: list[str] = []
    negative_factors: list[str] = []
    watch_issues: list[str] = []
    reasons: list[ReasonItem] = []
    today_actions: list[str] = []
    # Gemini Developer API의 response_schema는 자유형 dict(additionalProperties)를
    # 지원하지 않으므로 고정 스키마 목록으로 받고, 저장 시 dict로 변환한다.
    indices: list[MarketMoveItem] = []
    sector_moves: list[MarketMoveItem] = []
    disclaimer: str = "본 브리핑은 정보 제공 목적이며 투자 권유가 아닙니다."
