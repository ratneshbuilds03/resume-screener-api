import os
from typing import List

from dotenv import load_dotenv

load_dotenv()


def _parse_list(value: str | None, default: List[str]) -> List[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL") or "sqlite:///./resume_scanner.db"
    MONGODB_URL: str = os.getenv("MONGODB_URL") or "mongodb://localhost:27017"
    MONGODB_DB: str = os.getenv("MONGODB_DB", "resume_db")
    REDIS_URL: str = os.getenv("REDIS_URL") or "redis://localhost:6379/0"
    SECRET_KEY: str = os.getenv("SECRET_KEY") or "dev-secret-change-me"
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY") or ""
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID") or ""
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY") or ""
    AWS_BUCKET_NAME: str = os.getenv("AWS_BUCKET_NAME") or ""
    AWS_REGION: str = os.getenv("AWS_REGION") or "ap-south-1"
    CORS_ORIGINS: List[str] = _parse_list(
        os.getenv("CORS_ORIGINS"),
        [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
        ],
    )


settings = Settings()