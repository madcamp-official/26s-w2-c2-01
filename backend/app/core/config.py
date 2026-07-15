from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 상대경로("​.env")는 프로세스가 어느 작업 디렉터리에서 기동되든 backend/.env를
# 안정적으로 찾도록 이 파일(app/core/config.py) 위치 기준 절대경로로 고정한다 —
# uvicorn --app-dir는 sys.path만 바꿀 뿐 cwd를 바꾸지 않아, 실행 위치에 따라
# .env를 못 찾고 ANTHROPIC_API_KEY 등이 조용히 빈 문자열(스텁 폴백)이 되는 문제가 있었다.
ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://trade_chaser:trade_chaser@localhost:5432/trade_chaser"

    SECRET_KEY: str = "change-this-to-a-random-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7일

    CORS_ORIGINS: str = "http://localhost:5173"

    FINNHUB_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    POLYGON_API_KEY: str = ""
    # 설정돼 있으면 1단계(팩트 추출)를 Gemini 무료 티어로 대체해 Claude 호출을
    # 절반으로 줄인다 (factory.py의 HybridBriefingLLMClient). 없으면 Claude만 사용.
    GEMINI_API_KEY: str = ""
    # Google AI Studio의 정식 모델 ID. 이미지를 다시 빌드하지 않고도
    # .env와 Docker Compose 환경변수로 모델을 교체할 수 있게 별도 설정한다.
    GEMINI_MODEL: str = "gemini-3.1-flash-lite"

    # 설정돼 있으면 2단계(해석·렌더링)를 자체 ML 서버의 Ollama(Gemma2)로 대체해
    # Claude 호출을 아예 없앤다 (factory.py get_llm_client 참고). 예:
    # "http://192.168.0.228:11434" — 컨테이너 안에서 접근 가능한 주소로 설정.
    OLLAMA_BASE_URL: str = ""
    OLLAMA_MODEL: str = "gemma2:9b"

    # 로컬 uvicorn 실행에서도 DB가 시드 10개 수준이면 서버 시작 직후 미국 종목 전체
    # import를 백그라운드로 1회 시도한다. Docker Compose는 command에서 이미 실행하지만,
    # import_us_stocks.py가 idempotent라 중복 실행돼도 기존 티커는 건너뛴다.
    AUTO_IMPORT_US_STOCKS: bool = True
    AUTO_IMPORT_US_STOCKS_THRESHOLD: int = 100

    # Finnhub company-news는 종목과 간접적으로만 관련된 기사도 많이 반환하므로
    # 제목·요약·related·출처를 점수화해 브리핑 입력의 노이즈를 줄인다.
    # 문제가 생기면 False로 바꾸고 프로세스(또는 컨테이너)를 재생성하면 기존 최신순
    # 수집으로 즉시 복귀한다.
    ENABLE_NEWS_RELEVANCE_FILTER: bool = True
    NEWS_RELEVANCE_MIN_SCORE: int = 4
    NEWS_RELEVANCE_MIN_ARTICLES: int = 3

    # CNBC RSS is the primary source for broad-market briefings. Finnhub remains
    # the automatic fallback when the feed is disabled, unavailable, or sparse.
    ENABLE_CNBC_MARKET_RSS: bool = True
    CNBC_MARKET_NEWS_LOOKBACK_HOURS: int = 24
    CNBC_MARKET_NEWS_PER_FEED: int = 10
    CNBC_MARKET_NEWS_LIMIT: int = 40
    CNBC_MARKET_NEWS_MIN_ARTICLES: int = 12

    # 브리핑 자동 갱신 스케줄러 (뉴스 재수집 + 브리핑 재생성)
    # 등간격이 아니라 미국 장(나스닥·뉴욕) 스케줄에 맞춘 하루 4번 고정 시각(KST):
    # 장시작 22시 · 장중 02시 · 장마감 05시 · 휴장 중 14시.
    # (서머타임 기준 — 09:30~16:00 ET = 22:30~05:00 KST를 정시로 반올림함.
    #  겨울철(EST)엔 미장이 1시간씩 밀리니 그 기간엔 23,3,6,14 정도로 조정 필요.)
    ENABLE_SCHEDULER: bool = True
    # Full-universe yfinance scan, independently switchable from news jobs.
    ENABLE_VOLATILITY_SCANNER: bool = True
    REFRESH_HOURS_KST: str = "2,5,14,22"
    # 위 스케줄의 최대 간격(05시->14시, 9시간)에 맞춘 캐시 신선도 기준.
    # 이보다 짧게 잡으면 다음 정기 갱신 전에 사용자가 브리핑을 열 때마다
    # on-demand로 Claude를 다시 호출하게 되어 불필요한 토큰 소모가 생긴다.
    REFRESH_INTERVAL_HOURS: int = 9

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
