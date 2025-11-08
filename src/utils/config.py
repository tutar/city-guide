"""
Configuration management for City Guide Smart Assistant
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration settings"""

    class Config:
        env_prefix = "POSTGRES_"

    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    db: str = Field(default="cityguide")
    user: str = Field(default="cityguide_user")
    password: str = Field(default="cityguide_password")

    @property
    def database_url(self) -> str:
        """Generate PostgreSQL connection URL"""
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.db}"
        )


class MilvusSettings(BaseSettings):
    """Milvus vector database configuration"""

    class Config:
        env_prefix = "MILVUS_"

    host: str = Field(default="localhost")
    port: int = Field(default=19530)
    collection: str = Field(default="document_embeddings")


class AISettings(BaseSettings):
    """AI service configuration"""

    class Config:
        env_prefix = ""

    deepseek_api_key: str = Field(default="test-api-key", alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL"
    )
    max_tokens: int = Field(default=1000, alias="MAX_TOKENS")
    temperature: float = Field(default=0.7, alias="TEMPERATURE")

    # Embedding model settings
    embedding_model: str = Field(
        default="Qwen/Qwen3-Embedding-0.6B", alias="EMBEDDING_MODEL"
    )
    embedding_dimension: int = Field(default=1024, alias="EMBEDDING_DIMENSION")


class ChainlitSettings(BaseSettings):
    """Chainlit frontend configuration"""

    class Config:
        env_prefix = "CHAINLIT_"

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    debug_mode: bool = Field(default=False)


class Settings(BaseSettings):
    """Main application settings"""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    app_name: str = "City Guide Smart Assistant"
    app_version: str = "1.0.0"

    # Sub-configurations
    database: DatabaseSettings = DatabaseSettings()
    milvus: MilvusSettings = MilvusSettings()
    ai: AISettings = AISettings()
    chainlit: ChainlitSettings = ChainlitSettings()

    # Performance settings
    search_timeout: int = Field(default=5, alias="SEARCH_TIMEOUT")
    conversation_timeout: int = Field(
        default=1800, alias="CONVERSATION_TIMEOUT"
    )  # 30 minutes


# Global settings instance
settings = Settings()
