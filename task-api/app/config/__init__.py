"""Configuration module."""
import os
from typing import Optional


class Settings:
    """Application settings."""

    # Jira configuration
    JIRA_URL: str = os.getenv("JIRA_URL", "https://portal.works.prod.sbt")
    JIRA_API_TOKEN: Optional[str] = os.getenv("JIRA_API_TOKEN")
    JIRA_USERNAME: Optional[str] = os.getenv("JIRA_USERNAME")

    # Local database
    USE_LOCAL_DB: bool = os.getenv("USE_LOCAL_DB", "true").lower() == "true"


settings = Settings()
