from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analysis, auth, briefings, stocks, users, watchlists
from app.core.config import settings

app = FastAPI(title="Trade Chaser API", version="0.1.0")

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
app.include_router(briefings.router)
app.include_router(analysis.router)


@app.get("/health")
def health():
    return {"status": "ok"}
