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
    database_url_env: str = Field(default="", alias="DATABASE_URL")
    test_database_url: str = Field(default="", alias="TEST_DATABASE_URL")

    @property
    def database_url(self) -> str:
        """Get PostgreSQL connection URL"""
        if self.database_url_env:
            return self.database_url_env
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
    collection: str = Field(
        default="document_embeddings", alias="MILVUS_COLLECTION_NAME"
    )
    url: str = Field(default="", alias="MILVUS_URL")
    token: str = Field(default="", alias="MILVUS_TOKEN")


class AISettings(BaseSettings):
    """AI service configuration"""

    class Config:
        env_prefix = ""

    deepseek_api_key: str = Field(default="test-api-key", alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL"
    )
    deepseek_model: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL")
    max_tokens: int = Field(default=1000, alias="MAX_TOKENS")
    temperature: float = Field(default=0.7, alias="TEMPERATURE")

    # Embedding model settings
    embedding_model: str = Field(
        default="Qwen/Qwen3-Embedding-0.6B", alias="EMBEDDING_MODEL"
    )
    embedding_dimension: int = Field(default=1024, alias="EMBEDDING_DIMENSION")
    embedding_device: str = Field(default="cpu", alias="EMBEDDING_DEVICE")

    # Mock service configuration
    use_mock_service: bool = Field(default=False, alias="USE_MOCK_AI_SERVICE")


class ChainlitSettings(BaseSettings):
    """Chainlit frontend configuration"""

    class Config:
        env_prefix = "CHAINLIT_"

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8001)
    debug_mode: bool = Field(default=False)
    headless: bool = Field(default=False)
    watch: bool = Field(default=False)


class Settings(BaseSettings):
    """Main application settings"""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields in .env file

    # Application settings
    app_name: str = Field(default="City Guide Smart Assistant", alias="APP_NAME")
    app_version: str = "1.0.0"
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    secret_key: str = Field(
        default="your-secret-key-change-in-production", alias="SECRET_KEY"
    )

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

    # Search configuration
    search_results_limit: int = Field(default=10, alias="SEARCH_RESULTS_LIMIT")
    search_similarity_threshold: float = Field(
        default=0.7, alias="SEARCH_SIMILARITY_THRESHOLD"
    )
    hybrid_search_weight_vector: float = Field(
        default=0.7, alias="HYBRID_SEARCH_WEIGHT_VECTOR"
    )
    hybrid_search_weight_keyword: float = Field(
        default=0.3, alias="HYBRID_SEARCH_WEIGHT_KEYWORD"
    )

    # External API configuration
    government_api_base_url: str = Field(
        default="https://api.shenzhen.gov.cn", alias="GOVERNMENT_API_BASE_URL"
    )
    government_api_key: str = Field(default="", alias="GOVERNMENT_API_KEY")
    google_maps_api_key: str = Field(default="", alias="GOOGLE_MAPS_API_KEY")
    baidu_maps_api_key: str = Field(default="", alias="BAIDU_MAPS_API_KEY")

    # Rate limiting
    rate_limit_requests_per_minute: int = Field(
        default=60, alias="RATE_LIMIT_REQUESTS_PER_MINUTE"
    )
    rate_limit_requests_per_hour: int = Field(
        default=1000, alias="RATE_LIMIT_REQUESTS_PER_HOUR"
    )

    # Caching configuration
    cache_ttl_seconds: int = Field(default=300, alias="CACHE_TTL_SECONDS")
    session_timeout_minutes: int = Field(default=30, alias="SESSION_TIMEOUT_MINUTES")

    # Monitoring and analytics
    enable_analytics: bool = Field(default=True, alias="ENABLE_ANALYTICS")
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")

    # Security settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"], alias="CORS_ORIGINS"
    )
    allowed_hosts: list[str] = Field(
        default=["localhost", "127.0.0.1"], alias="ALLOWED_HOSTS"
    )


# Global settings instance
settings = Settings()
