"""Configuration management for Voluntier platform."""

from functools import lru_cache
from typing import Any, Dict, List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="DB_")
    
    url: str = Field(default="postgresql+asyncpg://voluntier_user:voluntier_password@localhost:5432/voluntier")
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)
    pool_timeout: int = Field(default=30)
    pool_recycle: int = Field(default=3600)
    echo: bool = Field(default=False)


class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="REDIS_")
    
    url: str = Field(default="redis://:redis_password@localhost:6379/0")
    max_connections: int = Field(default=10)
    retry_on_timeout: bool = Field(default=True)
    socket_timeout: int = Field(default=5)


class Neo4jSettings(BaseSettings):
    """Neo4j configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="NEO4J_")
    
    uri: str = Field(default="bolt://localhost:7687")
    user: str = Field(default="neo4j")
    password: str = Field(default="neo4j_password")
    database: str = Field(default="voluntier")


class TemporalSettings(BaseSettings):
    """Temporal configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="TEMPORAL_")
    
    host: str = Field(default="localhost:7233")
    namespace: str = Field(default="default")
    task_queue: str = Field(default="voluntier-task-queue")
    workflow_execution_timeout: int = Field(default=3600)  # 1 hour
    workflow_run_timeout: int = Field(default=600)  # 10 minutes
    workflow_task_timeout: int = Field(default=10)  # 10 seconds
    activity_start_to_close_timeout: int = Field(default=60)  # 1 minute
    activity_heartbeat_timeout: int = Field(default=30)  # 30 seconds


class SecuritySettings(BaseSettings):
    """Security configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="SECURITY_")
    
    secret_key: str = Field(default="your-super-secret-key-change-in-production")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)
    password_reset_expire_minutes: int = Field(default=15)
    email_verification_expire_hours: int = Field(default=24)


class LLMSettings(BaseSettings):
    """LLM and AI service configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="LLM_")
    
    vllm_base_url: str = Field(default="http://localhost:8000")
    openai_api_key: Optional[str] = Field(default=None)
    default_model: str = Field(default="microsoft/DialoGPT-medium")
    max_tokens: int = Field(default=1000)
    temperature: float = Field(default=0.7)
    timeout: int = Field(default=30)


class ObservabilitySettings(BaseSettings):
    """Observability and monitoring configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="OBSERVABILITY_")
    
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    metrics_enabled: bool = Field(default=True)
    tracing_enabled: bool = Field(default=True)
    prometheus_port: int = Field(default=9090)
    jaeger_endpoint: Optional[str] = Field(default=None)


class AgentSettings(BaseSettings):
    """Autonomous agent configuration settings."""
    
    model_config = SettingsConfigDict(env_prefix="AGENT_")
    
    max_retry_attempts: int = Field(default=3)
    retry_backoff_factor: float = Field(default=2.0)
    max_parallel_workflows: int = Field(default=10)
    human_approval_required: List[str] = Field(
        default=[
            "security_threat_response",
            "database_migration",
            "system_configuration_change",
            "user_data_deletion",
            "financial_transaction",
        ]
    )
    auto_approve_workflows: List[str] = Field(
        default=[
            "volunteer_registration",
            "event_creation",
            "notification_sending",
            "data_sync",
            "report_generation",
        ]
    )


class Settings(BaseSettings):
    """Main application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application settings
    app_name: str = Field(default="Voluntier")
    app_version: str = Field(default="0.1.0")
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    api_prefix: str = Field(default="/api/v1")
    
    # Service configurations
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    neo4j: Neo4jSettings = Field(default_factory=Neo4jSettings)
    temporal: TemporalSettings = Field(default_factory=TemporalSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
    agent: AgentSettings = Field(default_factory=AgentSettings)
    
    # CORS settings
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: List[str] = Field(default=["*"])
    cors_allow_headers: List[str] = Field(default=["*"])
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    def get_database_url(self) -> str:
        """Get database URL for SQLAlchemy."""
        return self.database.url
    
    def get_redis_url(self) -> str:
        """Get Redis URL."""
        return self.redis.url
    
    def get_temporal_host(self) -> str:
        """Get Temporal server host."""
        return self.temporal.host


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Global settings instance
settings = get_settings()