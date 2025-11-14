"""Application configuration using Pydantic Settings"""

from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    # Application
    app_name: str = Field(default="OpenChat", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    secret_key: str = Field(..., alias="SECRET_KEY")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"],
        alias="CORS_ORIGINS"
    )

    # Database
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="openchat", alias="POSTGRES_DB")
    postgres_user: str = Field(default="openchat", alias="POSTGRES_USER")
    postgres_password: str = Field(..., alias="POSTGRES_PASSWORD")
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")

    @validator("database_url", pre=True, always=True)
    def assemble_db_url(cls, v: Optional[str], values: dict) -> str:
        if v:
            return v
        return (
            f"postgresql://{values.get('postgres_user')}:{values.get('postgres_password')}"
            f"@{values.get('postgres_host')}:{values.get('postgres_port')}"
            f"/{values.get('postgres_db')}"
        )

    # Redis
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")

    @validator("redis_url", pre=True, always=True)
    def assemble_redis_url(cls, v: Optional[str], values: dict) -> str:
        if v:
            return v
        password = values.get('redis_password')
        if password:
            return f"redis://:{password}@{values.get('redis_host')}:{values.get('redis_port')}/0"
        return f"redis://{values.get('redis_host')}:{values.get('redis_port')}/0"

    # MinIO / S3
    minio_host: str = Field(default="localhost", alias="MINIO_HOST")
    minio_port: int = Field(default=9000, alias="MINIO_PORT")
    minio_access_key: str = Field(default="minioadmin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field(default="openchat", alias="MINIO_BUCKET")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")

    # Qdrant
    qdrant_host: str = Field(default="localhost", alias="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, alias="QDRANT_PORT")
    qdrant_api_key: Optional[str] = Field(default=None, alias="QDRANT_API_KEY")
    qdrant_url: Optional[str] = Field(default=None, alias="QDRANT_URL")

    @validator("qdrant_url", pre=True, always=True)
    def assemble_qdrant_url(cls, v: Optional[str], values: dict) -> str:
        if v:
            return v
        return f"http://{values.get('qdrant_host')}:{values.get('qdrant_port')}"

    # LLM Providers
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL")

    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022", alias="ANTHROPIC_MODEL")

    ollama_host: str = Field(default="http://localhost:11434", alias="OLLAMA_HOST")
    ollama_model: str = Field(default="llama3.1:8b", alias="OLLAMA_MODEL")

    # Search
    tavily_api_key: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")
    brave_api_key: Optional[str] = Field(default=None, alias="BRAVE_API_KEY")

    # Authentication
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, alias="JWT_EXPIRATION_HOURS")
    refresh_token_expiration_days: int = Field(default=30, alias="REFRESH_TOKEN_EXPIRATION_DAYS")

    # Security
    enable_prompt_injection_detection: bool = Field(default=True, alias="ENABLE_PROMPT_INJECTION_DETECTION")
    enable_pii_detection: bool = Field(default=True, alias="ENABLE_PII_DETECTION")
    enable_content_filtering: bool = Field(default=True, alias="ENABLE_CONTENT_FILTERING")
    lakera_guard_api_key: Optional[str] = Field(default=None, alias="LAKERA_GUARD_API_KEY")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_per_minute: int = Field(default=100, alias="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, alias="RATE_LIMIT_PER_HOUR")

    # Caching
    semantic_cache_enabled: bool = Field(default=True, alias="SEMANTIC_CACHE_ENABLED")
    semantic_cache_threshold: float = Field(default=0.95, alias="SEMANTIC_CACHE_THRESHOLD")
    cache_ttl_seconds: int = Field(default=3600, alias="CACHE_TTL_SECONDS")

    # Features
    enable_web_search: bool = Field(default=True, alias="ENABLE_WEB_SEARCH")
    enable_rag: bool = Field(default=True, alias="ENABLE_RAG")
    enable_file_upload: bool = Field(default=True, alias="ENABLE_FILE_UPLOAD")
    max_file_size_mb: int = Field(default=50, alias="MAX_FILE_SIZE_MB")
    max_files_per_conversation: int = Field(default=40, alias="MAX_FILES_PER_CONVERSATION")

    # Monitoring
    prometheus_enabled: bool = Field(default=True, alias="PROMETHEUS_ENABLED")
    jaeger_enabled: bool = Field(default=False, alias="JAEGER_ENABLED")
    jaeger_endpoint: Optional[str] = Field(default=None, alias="JAEGER_ENDPOINT")
    langsmith_api_key: Optional[str] = Field(default=None, alias="LANGSMITH_API_KEY")
    langsmith_project: str = Field(default="openchat", alias="LANGSMITH_PROJECT")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")


settings = Settings()
