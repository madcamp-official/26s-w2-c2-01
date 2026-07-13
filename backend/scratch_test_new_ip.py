"""
다른 네트워크(다른 공인 IP)에서 yfinance가 지금 막혀 있는지 빠르게 확인하는
독립 실행 스크립트. 프로젝트 venv/DB 없이 아래만 있으면 됨:

    pip install yfinance pandas

실행:
    python scratch_test_new_ip.py
"""

import time

import yfinance as yf

# 실제 대형주 100개(무작위 알파벳 순 아님, 다양한 섹터) — 아까 원래 IP에서
# 17.4초에 성공했던 것과 같은 규모의 테스트.
TICKERS = [
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "AVGO", "BRK.B",
    "JPM", "V", "XOM", "JNJ", "UNH", "PG", "HD", "MA", "KO", "DIS",
    "BAC", "MCD", "CVX", "LLY", "ORCL", "WFC", "CRM", "ABBV", "IBM", "GE",
    "CAT", "BA", "AMD", "NFLX", "COIN", "ADBE", "PEP", "COST", "CSCO", "TMO",
    "ACN", "LIN", "MRK", "ABT", "DHR", "NKE", "TXN", "PM", "NEE", "UNP",
    "RTX", "HON", "QCOM", "LOW", "INTU", "AMGN", "SPGI", "GS", "ISRG", "BKNG",
    "CB", "ELV", "PLD", "SYK", "MDT", "AMAT", "GILD", "ADP", "VRTX", "REGN",
    "LRCX", "MU", "PANW", "ADI", "TJX", "MMC", "CI", "ETN", "SCHW", "SBUX",
    "BSX", "SO", "FISV", "ZTS", "MO", "DUK", "CL", "ITW", "BDX", "AON",
    "SHW", "EQIX", "APD", "CME", "PGR", "NOC", "MCK", "USB", "PNC", "TGT",
]


def main() -> None:
    print(f"테스트 티커 수: {len(TICKERS)}")
    t0 = time.time()
    df = yf.download(
        tickers=TICKERS, period="3mo", interval="1d",
        group_by="ticker", auto_adjust=False, actions=False,
        threads=False, progress=False, timeout=20.0,
    )
    elapsed = time.time() - t0
    print(f"소요 시간: {elapsed:.1f}초")

    # 성공적으로 받아온 티커 수를 세서 rate limit 여부 판단
    if hasattr(df.columns, "get_level_values"):
        got = set(df.columns.get_level_values(0)) & set(TICKERS)
    else:
        got = set(TICKERS) if not df.empty else set()
    print(f"실제 데이터 받아온 티커 수: {len(got)} / {len(TICKERS)}")

    if len(got) >= len(TICKERS) * 0.9:
        print("결과: 정상 — 이 네트워크(IP)는 차단 안 됨")
    elif len(got) == 0:
        print("결과: 완전 차단 — 이 IP도 막혀있거나 rate limit 걸림")
    else:
        print("결과: 부분 실패 — 애매함, 로그에 RateLimitError 있는지 위 출력 확인 필요")


if __name__ == "__main__":
    main()
