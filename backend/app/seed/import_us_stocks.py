"""
Finnhub /stock/symbol 로 미국 상장 보통주 전체(약 1.8만 건)를 stocks 표에 벌크로
채워 넣는다. sector_id는 일부러 비워둔다(NULL) — 실제로 누군가 관심종목에
추가하는 순간에만 섹터를 분류한다(app/services/sector_classifier.py의
classify_and_save, app/api/routes/watchlists.py에서 호출).

즉 이 스크립트가 하는 일은 "검색 가능한 종목 목록을 넓히는 것"뿐이고, 여기서
채운 종목들은 아무도 관심등록하지 않는 한 Claude·Finnhub 추가 호출을 전혀
유발하지 않는다 — 그냥 텍스트로 존재할 뿐이다.

ETF·ADR·리츠·워런트 등은 제외하고 type == "Common Stock"만 들여온다.
이미 있는 티커(seed_data.py로 심어둔 10개 등)는 건너뛴다(idempotent).

사용법: python -m app.seed.import_us_stocks
"""

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.stock import Stock
from app.services.finnhub_client import FinnhubClient, FinnhubError

MIC_TO_EXCHANGE = {
    "XNAS": "NASDAQ",
    "XNYS": "NYSE",
    "ARCX": "NYSE Arca",
    "BATS": "CBOE BZX",
    "XASE": "NYSE American",
}


def run() -> None:
    db = SessionLocal()
    try:
        try:
            with FinnhubClient() as client:
                symbols = client.get_us_symbols()
        except FinnhubError as e:
            print(f"Finnhub 호출 실패: {e}")
            return

        common_stocks = [s for s in symbols if s.get("type") == "Common Stock"]
        print(f"미국 상장 전체 {len(symbols)}건 중 보통주 {len(common_stocks)}건")

        existing_tickers = {t for t in db.scalars(select(Stock.ticker)).all()}
        print(f"이미 DB에 있는 종목 {len(existing_tickers)}건 (건너뜀)")

        new_stocks = []
        for item in common_stocks:
            ticker = (item.get("symbol") or "").upper()
            if not ticker or ticker in existing_tickers:
                continue
            existing_tickers.add(ticker)  # 이번 배치 안에서의 중복도 방지
            new_stocks.append(
                Stock(
                    ticker=ticker,
                    name_ko=None,
                    name_en=item.get("description") or ticker,
                    exchange=MIC_TO_EXCHANGE.get(item.get("mic"), item.get("mic") or "US"),
                    sector_id=None,  # 지연 분류 — 관심종목 등록 시점에 채워짐
                )
            )

        print(f"새로 추가할 종목: {len(new_stocks)}건")
        db.add_all(new_stocks)
        db.commit()
        print("완료.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
