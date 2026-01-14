import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    GOOGLE_SERVICE_ACCOUNT_JSON: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    RAILWAY_ENV: str = os.getenv("RAILWAY_ENV", "development")
    RAILWAY_PUBLIC_DOMAIN: str = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
    RAILWAY_STATIC_URL: str = os.getenv("RAILWAY_STATIC_URL", "")

    @classmethod
    def is_production(cls) -> bool:
        return cls.RAILWAY_ENV == "production"
    
    @classmethod
    def get_webapp_url(cls) -> str:
        """Get webapp URL based on environment."""
        if cls.is_production():
            # Try Railway public domain first
            if cls.RAILWAY_PUBLIC_DOMAIN:
                return f"https://{cls.RAILWAY_PUBLIC_DOMAIN}/webapp"
            # Try Railway static URL
            if cls.RAILWAY_STATIC_URL:
                return f"{cls.RAILWAY_STATIC_URL}/webapp"
            # Fallback - user needs to set RAILWAY_PUBLIC_DOMAIN
            return "https://your-app-name.up.railway.app/webapp"
        else:
            return "http://localhost:8000/webapp"


config = Config()
