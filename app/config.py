

from pydantic_settings import BaseSettings
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_BASE_URL: str = "http://localhost:8000"
    VALID_API_KEYS: str = "" 
    class Config:
        env_file = str(ENV_PATH)
        extra = "ignore" 
settings = Settings()