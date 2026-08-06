from __future__ import annotations

from typing import Any
import httpx

from s21_agent.config import settings
from s21_agent.models.task import Task


class S21Client:
    """Адаптер S21.

    TODO: сопоставить URL, параметры и поля с фактическим API S21.
    """

    def __init__(self) -> None:
        headers: dict[str, str] = {"Accept": "application/json"}
        if settings.s21_api_token:
            headers["Authorization"] = f"Bearer {settings.s21_api_token}"

        self.client = httpx.Client(
            base_url=settings.s21_base_url.rstrip("/"),
            headers=headers,
            timeout=settings.s21_timeout_seconds,
            verify=settings.s21_verify_tls,
        )

    def close(self) -> None:
        self.client.close()

    def search_tasks(self, query: str, filters: dict[str, Any] | None = None) -> list[Task]:
        raise NotImplementedError(
            "Настройте search_tasks под официальный API или MCP-контракт S21."
        )

    def get_task(self, task_id: str) -> Task:
        raise NotImplementedError(
            "Настройте get_task под официальный API или MCP-контракт S21."
        )

    def download_attachment(self, attachment_url: str) -> bytes:
        response = self.client.get(attachment_url)
        response.raise_for_status()
        return response.content
