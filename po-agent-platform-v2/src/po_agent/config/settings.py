"""Settings configuration for PO Agent Platform v2."""

from pathlib import Path
from typing import Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# settings.py -> config -> po_agent -> src -> po-agent-platform-v2
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_PROJECT_ENV = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables and project .env."""

    # Absolute project .env prevents the production semantic layer from silently
    # switching off merely because uvicorn/GigaCode was started one directory up.
    # Process environment still has normal pydantic-settings precedence.
    model_config = SettingsConfigDict(
        env_file=(str(_PROJECT_ENV), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="po-agent-platform-v2")
    app_version: str = Field(default="0.1.0")
    app_env: str = Field(default="development")
    app_port: int = Field(default=8004)
    app_host: str = Field(default="127.0.0.1")

    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    correlation_id_header: str = Field(default="X-Request-ID")

    as21_mode: str = Field(
        default="fake",
        description="fake or task-api",
        validation_alias=AliasChoices("AS21_MODE", "PO_AGENT_AS21_MODE"),
    )
    task_api_base_url: str = Field(
        default="http://localhost:8003",
        validation_alias=AliasChoices("TASK_API_BASE_URL", "PO_AGENT_TASK_API_BASE_URL"),
    )
    task_api_timeout_seconds: float = Field(
        default=30.0,
        validation_alias=AliasChoices("TASK_API_TIMEOUT_SECONDS", "PO_AGENT_TASK_API_TIMEOUT_SECONDS"),
    )
    team_config_path: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("TEAM_CONFIG_PATH", "PO_AGENT_TEAM_CONFIG_PATH"),
    )
    agent_core_v3_enabled: bool = Field(
        default=False,
        description="Enable the explicitly certified Agent Core v3 pilot routing seam",
        validation_alias=AliasChoices("AGENT_CORE_V3_ENABLED", "PO_AGENT_AGENT_CORE_V3_ENABLED"),
    )
    swtr_base_url: str = Field(default="https://portal.works.prod.sbt/swtr")
    swtr_token: Optional[str] = Field(default=None)

    semantic_llm_enabled: bool = Field(default=True)
    llm_api_base_url: str = Field(default="https://api.ai.sbt/openai/v1")
    llm_api_key: Optional[str] = Field(default=None)
    llm_model_name: str = Field(default="Qwen/Qwen3-Coder-Next")
    llm_tls_verify: bool = Field(default=True)

    database_url: str = Field(default="sqlite:///data/app.db")
    learned_semantics_path: str = Field(default="data/learned_semantics.json")

    config_dir: str = Field(default="config")
    data_dir: str = Field(default="data")
    docs_dir: str = Field(default="docs")
    scripts_dir: str = Field(default="scripts")


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    global _settings
    _settings = None
