from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://trade_chaser:trade_chaser@localhost:5432/trade_chaser"

    SECRET_KEY: str = "change-this-to-a-random-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7일

    CORS_ORIGINS: str = "http://localhost:5173"

    FINNHUB_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # 브리핑 자동 갱신 스케줄러 (뉴스 재수집 + 브리핑 재생성)
    # 등간격이 아니라 미국 장(나스닥·뉴욕) 스케줄에 맞춘 하루 4번 고정 시각(KST):
    # 장시작 22시 · 장중 02시 · 장마감 05시 · 휴장 중 14시.
    # (서머타임 기준 — 09:30~16:00 ET = 22:30~05:00 KST를 정시로 반올림함.
    #  겨울철(EST)엔 미장이 1시간씩 밀리니 그 기간엔 23,3,6,14 정도로 조정 필요.)
    ENABLE_SCHEDULER: bool = True
    REFRESH_HOURS_KST: str = "2,5,14,22"
    # 위 스케줄의 최대 간격(05시->14시, 9시간)에 맞춘 캐시 신선도 기준.
    # 이보다 짧게 잡으면 다음 정기 갱신 전에 사용자가 브리핑을 열 때마다
    # on-demand로 Claude를 다시 호출하게 되어 불필요한 토큰 소모가 생긴다.
    REFRESH_INTERVAL_HOURS: int = 9

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
