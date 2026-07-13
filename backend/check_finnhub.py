"""
Finnhub API 데이터 확인용 스크립트.

DB에 저장하지 않고, Finnhub에서 받아온 원본 시세·뉴스를 그대로 출력해
값이 정상인지 눈으로 검증하는 용도.

사용법 (backend 폴더에서, venv 켠 상태):
    python check_finnhub.py                # 기본 AAPL NVDA TSLA 확인
    python check_finnhub.py AAPL           # 특정 종목만
    python check_finnhub.py AAPL MSFT AMD  # 여러 종목
"""

import sys
from datetime import date, timedelta

from app.core.config import settings
from app.services.finnhub_client import FinnhubClient, FinnhubError

# Windows 콘솔 인코딩 안전장치 (한글/특수문자 출력 시 깨짐 방지)
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

TICKERS = [t.upper() for t in sys.argv[1:]] or ["AAPL", "NVDA", "TSLA"]


def main() -> None:
    if not settings.FINNHUB_API_KEY:
        print("❌ FINNHUB_API_KEY가 .env에 설정되어 있지 않습니다.")
        print("   https://finnhub.io 에서 무료 키를 발급받아 backend/.env 의")
        print("   FINNHUB_API_KEY=... 에 넣은 뒤 다시 실행하세요.")
        sys.exit(1)

    print(f"확인 대상 종목: {', '.join(TICKERS)}")
    since = date.today() - timedelta(days=3)
    until = date.today()

    with FinnhubClient() as client:
        for t in TICKERS:
            print("=" * 64)
            print(f"[{t}]")

            # 1) 시세(quote)
            try:
                q = client.get_quote(t)
                print("  ── 시세(quote) ──")
                print(f"    현재가(c)   : {q.get('c')}")
                print(f"    전일종가(pc): {q.get('pc')}")
                print(f"    등락률(dp)  : {q.get('dp')} %")
                print(f"    고가(h)/저가(l): {q.get('h')} / {q.get('l')}")
            except FinnhubError as e:
                print(f"  ⚠️ 시세 조회 실패: {e}")

            # 2) 뉴스(company-news)
            try:
                news = client.get_company_news(t, from_date=since, to_date=until)
                print(f"  ── 최근 3일 뉴스: {len(news)}건 ──")
                for n in news[:5]:
                    headline = (n.get("headline") or "")[:72]
                    print(f"    • {headline}")
                    print(f"      출처: {n.get('source')}  |  {n.get('url')}")
                if not news:
                    print("    (해당 기간 뉴스 없음 — 주말/휴장이면 정상)")
            except FinnhubError as e:
                print(f"  ⚠️ 뉴스 조회 실패: {e}")

    print("=" * 64)
    print("완료. 위 현재가를 실제 주가(구글에 'AAPL stock' 검색)와,")
    print("뉴스 URL을 클릭해 실제 기사인지 비교하면 정상 여부를 확인할 수 있습니다.")


if __name__ == "__main__":
    main()
