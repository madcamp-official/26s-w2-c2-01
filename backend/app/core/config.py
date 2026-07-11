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

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
