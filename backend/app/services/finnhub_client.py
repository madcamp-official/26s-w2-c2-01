"""
Finnhub REST API 클라이언트 (무료 티어 기준).
https://finnhub.io/docs/api

기획서.md 7-2절: 종가·뉴스 데이터 소스. 무료 티어라 실시간 호가가 아닌
지연/종가 성격의 데이터만 사용한다.
"""

from datetime import date, datetime, timezone

import httpx

from app.core.config import settings

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


class FinnhubError(RuntimeError):
    pass


class FinnhubClient:
    def __init__(self, api_key: str | None = None, timeout: float = 10.0) -> None:
        self.api_key = api_key or settings.FINNHUB_API_KEY
        if not self.api_key:
            raise FinnhubError(
                "FINNHUB_API_KEY가 설정되지 않았습니다. .env 에 키를 채운 뒤 다시 실행하세요."
            )
        # /stock/symbol 은 302로 정적 JSON 파일 위치를 알려주는 방식이라
        # follow_redirects 없이는 실패한다(실측 확인됨).
        self._client = httpx.Client(base_url=FINNHUB_BASE_URL, timeout=timeout, follow_redirects=True)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "FinnhubClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def _get(self, path: str, params: dict) -> dict | list:
        params = {**params, "token": self.api_key}
        resp = self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    def get_quote(self, ticker: str) -> dict:
        """
        현재가/전일종가/등락률. 무료 티어에서도 제공됨.
        응답 예: {"c": 210.5, "d": 1.2, "dp": 0.57, "h":..., "l":..., "o":..., "pc": 209.3, "t": 1720000000}
        """
        data = self._get("/quote", {"symbol": ticker})
        if not isinstance(data, dict) or data.get("c") in (None, 0):
            raise FinnhubError(f"{ticker} quote 응답이 비어있습니다: {data}")
        return data

    def get_company_news(self, ticker: str, from_date: date, to_date: date) -> list[dict]:
        """
        종목별 뉴스 목록. 응답 예:
        [{"category":..., "datetime": 1720000000, "headline":..., "id":...,
          "related":..., "source":..., "summary":..., "url":...}, ...]
        """
        data = self._get(
            "/company-news",
            {
                "symbol": ticker,
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
            },
        )
        return data if isinstance(data, list) else []

    def get_general_news(self, category: str = "general") -> list[dict]:
        """
        특정 종목에 매이지 않은 시장 전반 뉴스. 무료 티어에서 제공됨.
        (참고: 지수 시세(get_quote로 ^IXIC 등 조회)는 무료 티어에서 막혀 있어
        "Market data subscription required" 에러가 난다 — 그래서 전체 시황은
        이 뉴스만으로, 수치가 아니라 정성적 서술로 구성한다.)
        응답 형식은 get_company_news와 동일.
        """
        data = self._get("/news", {"category": category})
        return data if isinstance(data, list) else []

    def get_us_symbols(self) -> list[dict]:
        """
        미국 상장 전체 종목 목록(3만여 건). 응답 예:
        [{"symbol": "AAPL", "description": "APPLE INC", "type": "Common Stock",
          "currency": "USD", "mic": "XNAS", ...}, ...]
        무료지만 302 리다이렉트로 정적 파일을 받아오는 방식이라 시간이 좀 걸린다.
        """
        data = self._get("/stock/symbol", {"exchange": "US"})
        return data if isinstance(data, list) else []

    def get_company_profile(self, ticker: str) -> dict:
        """
        회사 프로필. 업종 분류는 finnhubIndustry 필드(예: "Semiconductors",
        "Banking", "Retail")로 온다. 무료 티어에서 제공됨.
        """
        data = self._get("/stock/profile2", {"symbol": ticker})
        return data if isinstance(data, dict) else {}


def unix_to_datetime(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc)
