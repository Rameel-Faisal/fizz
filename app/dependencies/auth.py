from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config import settings

# This tells FastAPI: look for a header called "X-API-Key" on incoming requests
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Dependency that checks the X-API-Key header against the list of valid
    keys in .env. Raises 401 if missing or invalid. If valid, the request
    is allowed to proceed to the actual route.
    """
    valid_keys = [k.strip() for k in settings.VALID_API_KEYS.split(",") if k.strip()]

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key — include an X-API-Key header"
        )

    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return api_key