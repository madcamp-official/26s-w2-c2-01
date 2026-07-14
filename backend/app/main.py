from contextlib import asynccontextmanager
from threading import Thread

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analysis, auth, briefings, sector_watchlists, stocks, users, watchlists
from app.core.config import settings
from app.jobs.bootstrap_stocks import run_startup_stock_import_if_needed
from app.jobs.scheduler import run_refresh_cycle
from app.jobs.scan_volatility import run_daily as run_volatility_daily
from app.jobs.scan_volatility import run_premarket as run_volatility_premarket
from app.services.volatility_scanner import VolatilityScanner

# 단일 uvicorn 프로세스(--workers 지정 안 함) 기준으로 설계됨.
# 워커를 여러 개 띄우면 이 스케줄러도 워커 수만큼 중복 실행되니 주의.
scheduler = BackgroundScheduler(timezone="Asia/Seoul")
volatility_scanner = VolatilityScanner()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.AUTO_IMPORT_US_STOCKS:
        Thread(
            target=run_startup_stock_import_if_needed,
            name="startup-stock-import",
            daemon=True,
        ).start()

    if settings.ENABLE_SCHEDULER:
        # 등간격이 아니라 REFRESH_HOURS_KST(장시작·장중·장마감·휴장 중 1회, 하루 4번)에
        # 맞춰 고정 시각에 실행한다.
        scheduler.add_job(
            run_refresh_cycle,
            trigger=CronTrigger(hour=settings.REFRESH_HOURS_KST, minute=0, timezone="Asia/Seoul"),
            id="refresh_cycle",
            replace_existing=True,
            max_instances=1,  # 이전 갱신(뉴스수집+Claude 호출로 몇 분 걸릴 수 있음)이 안 끝났으면 겹쳐 돌지 않음
        )
        if settings.ENABLE_VOLATILITY_SCANNER:
            # US/Eastern keeps the jobs aligned when daylight saving changes.
            # 장 마감 후에는 다음 날 프리마켓 스캔에 쓸 후보만 준비한다.
            scheduler.add_job(
                run_volatility_daily,
                args=[volatility_scanner],
                trigger=CronTrigger(
                    day_of_week="mon-fri", hour=16, minute=30, timezone="America/New_York"
                ),
                id="volatility_daily_scan",
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )
            # 사용자에게 보이는 '오늘의 변동성' 결과는 본장 09:30 ET의 정확히
            # 1시간 전인 08:30 ET에만 갱신한다. 서버 재시작 시에는 다시 만들지 않는다.
            scheduler.add_job(
                run_volatility_premarket,
                args=[volatility_scanner],
                trigger=CronTrigger(
                    day_of_week="mon-fri", hour=8, minute=30, timezone="America/New_York"
                ),
                id="volatility_premarket_scan",
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )
        scheduler.start()
    yield
    if settings.ENABLE_SCHEDULER:
        scheduler.shutdown(wait=False)


app = FastAPI(title="Trade Chaser API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(stocks.router)
app.include_router(watchlists.router)
app.include_router(sector_watchlists.router)
app.include_router(briefings.router)
app.include_router(analysis.router)


@app.get("/health")
def health():
    return {"status": "ok"}
