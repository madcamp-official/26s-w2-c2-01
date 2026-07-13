from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analysis, auth, briefings, sector_watchlists, stocks, users, watchlists
from app.core.config import settings
from app.jobs.scheduler import run_refresh_cycle

# 단일 uvicorn 프로세스(--workers 지정 안 함) 기준으로 설계됨.
# 워커를 여러 개 띄우면 이 스케줄러도 워커 수만큼 중복 실행되니 주의.
scheduler = BackgroundScheduler(timezone="Asia/Seoul")


@asynccontextmanager
async def lifespan(app: FastAPI):
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
