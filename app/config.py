"""App configuration loaded from .env"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    # Database (read-only connection to soukchay_sysdata on apis.com.la)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "admin")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "soukchay_sysdata")
    DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4")

    # Auth — simple API key. Empty string disables auth (dev).
    API_KEY = os.getenv("API_KEY", "")

    # CORS — comma separated list of allowed origins ("*" = any)
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]


settings = Settings()