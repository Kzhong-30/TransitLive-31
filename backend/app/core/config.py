from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Stock Market Data Service"
    APP_VERSION: str = "1.0.0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    PUSH_INTERVAL: float = 1.0

    class Config:
        env_file = ".env"


settings = Settings()
