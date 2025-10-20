from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    ENABLE_WORKER: bool = True

    FETCH_INTERVAL_SECONDS: float = 3.0
    THRESHOLD_PERCENT: float = 0.3
    COOLDOWN_SECONDS: float = 45.0
    HYSTERESIS_DELTA_PCT: float = 0.15

    SYMBOLS: str = "BTC/USDT,USDT/IRT"

    TELEGRAM_TOKEN: str | None = None
    TELEGRAM_CHAT_ID: str | None = None
    
    BALE_TOKEN: str | None = None
    BALE_CHAT_ID: str | None = None

    NOBITEX_BASE_URL: str = "https://api.nobitex.ir"
    NOBITEX_API_KEY: str | None = None
    WALLEX_BASE_URL: str = "https://api.wallex.ir/v1"
    WALLEX_API_KEY: str | None = None

    HTTP_TIMEOUT_SECONDS: float = 5.0
    RETRY_MAX_TRIES: int = 5
    RETRY_BASE_DELAY: float = 0.2
    RETRY_MAX_DELAY: float = 3.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def symbols_list(self) -> List[str]:
        return [s.strip().upper() for s in self.SYMBOLS.split(",") if s.strip()]

settings = Settings()
