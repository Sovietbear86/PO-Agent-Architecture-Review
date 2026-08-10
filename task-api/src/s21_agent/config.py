"""Pydantic settings for S21 Agent."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Agent settings from environment."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # SWTR/MCP connection settings
    mcp_host: str = "localhost"
    mcp_port: int = 3000
    mcp_timeout_seconds: int = 30
    mcp_read_only: bool = True

    # Agent behavior
    max_results: int = 50
    show_sources: bool = True
    show_confidence: bool = True
    require_confirmation_for_writes: bool = True

    # Search settings
    exact_first: bool = True
    fulltext_enabled: bool = True
    semantic_enabled: bool = False
    attachment_search_enabled: bool = True

    # Security
    redact_secrets_in_logs: bool = True
    allow_external_llm: bool = False
    execute_macros: bool = False
    execute_attachment_code: bool = False

    # OpenAI settings for LLM-based analysis
    openai_api_key: Optional[str] = None
    openai_model: str = "Qwen/Qwen3-Coder-Next"
    openai_base_url: str = "https://api.ai.sbt/openai/v1"
    openai_timeout_seconds: int = 60

    # If not set from env, try to read from file
    def __init__(self, **data):
        super().__init__(**data)
        if not self.openai_api_key:
            try:
                with open("/Users/kalachanov.v.v/.config/openai/api_key", "r") as f:
                    self.openai_api_key = f.read().strip()
            except:
                pass

settings = Settings()
