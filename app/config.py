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
    def get_webapp_url(cls) -> str | None:
        """Get webapp URL based on environment. Always returns HTTPS for production. Returns None if not configured."""
        # Check if we have Railway domain (production)
        if cls.RAILWAY_PUBLIC_DOMAIN:
            # Ensure HTTPS
            domain = cls.RAILWAY_PUBLIC_DOMAIN
            if not domain.startswith('http'):
                domain = f"https://{domain}"
            return f"{domain}/webapp"
        
        if cls.RAILWAY_STATIC_URL:
            # Ensure HTTPS
            url = cls.RAILWAY_STATIC_URL
            if url.startswith('http://'):
                url = url.replace('http://', 'https://')
            elif not url.startswith('http'):
                url = f"https://{url}"
            return f"{url}/webapp"
        
        # No URL configured - return None (bot will work without WebApp button)
        return None


config = Config()
