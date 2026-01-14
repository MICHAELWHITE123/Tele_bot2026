import os


class Config:
    """Application configuration loaded from environment variables."""

    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    GOOGLE_SERVICE_ACCOUNT_JSON: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    RAILWAY_ENV: str = os.getenv("RAILWAY_ENV", "development")

    @classmethod
    def is_production(cls) -> bool:
        return cls.RAILWAY_ENV == "production"


config = Config()
