"""API-key authentication dependency."""
from fastapi import Header, HTTPException, status

from .config import settings


def require_api_key(x_api_key: str = Header(default="", alias="X-API-Key")):
    """Require a matching X-API-Key header unless auth is disabled in .env."""
    if not settings.API_KEY:
        return  # auth disabled (dev)
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )