"""
import_us_stocks.py로 벌크 삽입했던 미국 상장 전체 종목(약 1.8만 건) 중,
seed_data.py의 큐레이션 종목도 아니고 실제 누구의 관심종목으로도 쓰인 적 없는
행을 삭제한다.

브리핑 화면의 "섹터" 탭이 카탈로그 전체를 훑어 그룹핑하다 보니 미분류 종목
1.8만여 건이 "섹터 미지정" 한 덩어리로 잡혀 화면을 뒤덮는 문제가 있었다 —
"섹터" 탭을 관심종목 기준으로 바꾼 것과 함께, 애초에 화면에 노출될 일 없는
이 데이터를 지워서 DB도 정리한다.

사용법: python -m app.seed.cleanup_bulk_stocks
"""

from sqlalchemy import delete, func, select

from app.db.session import SessionLocal
from app.models.stock import Stock
from app.models.watchlist import Watchlist
from app.seed.seed_data import STOCKS as SEED_STOCKS


def run() -> None:
    db = SessionLocal()
    try:
        keep_tickers = {ticker for ticker, *_ in SEED_STOCKS}
        keep_tickers |= set(db.scalars(select(Watchlist.ticker).distinct()).all())

        before = db.scalar(select(func.count()).select_from(Stock))
        print(f"유지할 종목 {len(keep_tickers)}건, 삭제 전 전체 {before}건")

        db.execute(delete(Stock).where(Stock.ticker.notin_(keep_tickers)))
        db.commit()

        after = db.scalar(select(func.count()).select_from(Stock))
        print(f"삭제 후 전체 {after}건. 완료.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
