# apps/backend/config.py
"""Backend configuration using pydantic Settings.
Loads environment variables from .env (handled by python-dotenv in main).
All required secrets have no defaults; missing variables raise ValidationError.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Core settings
    APP_ENV: str = "development"  # development | production
    LOG_LEVEL: str = "INFO"

    # LM Studio
    LMSTUDIO_BASE_URL: str
    LMSTUDIO_GENERATION_MODEL: str = "qwen3-8b"
    LMSTUDIO_EMBEDDING_MODEL: str = "qwen3-embedding-0.6b"
    LMSTUDIO_EMBEDDING_DIMENSIONS: int = 1024

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "graphora_chunks"

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str

    # PostgreSQL (asyncpg URL)
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
