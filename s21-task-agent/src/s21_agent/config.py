from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    s21_base_url: str
    s21_api_token: str = ""
    s21_projects: str = ""
    s21_verify_tls: bool = True
    s21_timeout_seconds: int = 30
    s21_max_results: int = 50
    s21_max_attachment_mb: int = 50
    s21_cache_ttl_seconds: int = 900
    s21_read_only: bool = True


settings = Settings()
