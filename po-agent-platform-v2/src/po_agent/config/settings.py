"""Settings configuration for PO Agent Platform v2."""

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="po-agent-platform-v2")
    app_version: str = Field(default="0.1.0")
    app_env: str = Field(default="development")
    app_port: int = Field(default=8004)
    app_host: str = Field(default="127.0.0.1")

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    # Correlation ID
    correlation_id_header: str = Field(default="X-Request-ID")

    # AS21/SWTR Adapter
    swtr_base_url: str = Field(default="https://portal.works.prod.sbt/swtr")
    swtr_token: Optional[str] = Field(default=None)

    # LLM Provider (OpenAI-compatible)
    llm_api_base_url: str = Field(default="https://api.ai.sbt/v1")
    llm_api_key: Optional[str] = Field(default=None)
    llm_model_name: str = Field(default="qwen-coder-3.7")

    # Storage
    database_url: str = Field(default="sqlite:///data/app.db")

    # Paths
    config_dir: str = Field(default="config")
    data_dir: str = Field(default="data")
    docs_dir: str = Field(default="docs")
    scripts_dir: str = Field(default="scripts")


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset global settings (useful for testing)."""
    global _settings
    _settings = None
