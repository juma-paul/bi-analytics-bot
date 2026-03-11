import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration from environment variables"""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/bi_analytics"
    )

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # App
    APP_NAME: str = "AI BI Data Analyst"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
    ]

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list = ["csv"]

    # ETL
    ETL_BATCH_SIZE: int = 5000
    ETL_TIMEOUT_SECONDS: int = 300

    # Query
    QUERY_TIMEOUT_SECONDS: int = 30
    CACHE_TTL_MINUTES: int = 60

    # Limits
    MIN_ROWS: int = 10
    MAX_ROWS: int = 100000

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


settings = Settings()
