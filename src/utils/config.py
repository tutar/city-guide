"""
Configuration management for City Guide Smart Assistant
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field


class DatabaseSettings(BaseSettings):
    """Database configuration settings"""

    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="city_guide", env="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", env="POSTGRES_USER")
    postgres_password: str = Field(default="password", env="POSTGRES_PASSWORD")

    @property
    def database_url(self) -> str:
        """Generate PostgreSQL connection URL"""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


class MilvusSettings(BaseSettings):
    """Milvus vector database configuration"""

    milvus_host: str = Field(default="localhost", env="MILVUS_HOST")
    milvus_port: int = Field(default=19530, env="MILVUS_PORT")
    milvus_collection: str = Field(default="document_embeddings", env="MILVUS_COLLECTION")


class AISettings(BaseSettings):
    """AI service configuration"""

    deepseek_api_key: str = Field(..., env="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", env="DEEPSEEK_BASE_URL")
    max_tokens: int = Field(default=1000, env="MAX_TOKENS")
    temperature: float = Field(default=0.7, env="TEMPERATURE")

    # Embedding model settings
    embedding_model: str = Field(default="Qwen/Qwen3-Embedding-0.6B", env="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=1024, env="EMBEDDING_DIMENSION")


class ChainlitSettings(BaseSettings):
    """Chainlit frontend configuration"""

    chainlit_host: str = Field(default="0.0.0.0", env="CHAINLIT_HOST")
    chainlit_port: int = Field(default=8000, env="CHAINLIT_PORT")
    debug_mode: bool = Field(default=False, env="DEBUG_MODE")


class Settings(BaseSettings):
    """Main application settings"""

    app_name: str = "City Guide Smart Assistant"
    app_version: str = "1.0.0"

    # Sub-configurations
    database: DatabaseSettings = DatabaseSettings()
    milvus: MilvusSettings = MilvusSettings()
    ai: AISettings = AISettings()
    chainlit: ChainlitSettings = ChainlitSettings()

    # Performance settings
    search_timeout: int = Field(default=5, env="SEARCH_TIMEOUT")
    conversation_timeout: int = Field(default=1800, env="CONVERSATION_TIMEOUT")  # 30 minutes

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()