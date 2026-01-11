from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Neo4j Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str

    # OpenAI Configuration
    openai_api_key: str
    model_name: str = "text-embedding-3-large"
    embedding_batch_size: int = 50

    # API Configuration
    api_title: str = "Quote Visualization API"
    api_version: str = "1.0.0"
    api_description: str = "API for managing quotes, people, and semantic relationships"

    # CORS Configuration
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Similarity Configuration
    similarity_threshold: float = 0.75

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra='ignore')


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
