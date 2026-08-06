"""Конфигурация Team Performance Agent"""

import os
import yaml
from typing import Dict, Any
from pathlib import Path

# Базовые пути
BASE_DIR = Path(__file__).parent.parent.parent
CONFIG_DIR = BASE_DIR / "config"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"

# Конфигурационные файлы
TEAM_MEMBERS_FILE = CONFIG_DIR / "team_members.yaml"
PRODUCTS_FILE = CONFIG_DIR / "products.yaml"
METRICS_FILE = CONFIG_DIR / "metrics.yaml"
THRESHOLDS_FILE = CONFIG_DIR / "thresholds.yaml"
WORKFLOW_STATUSES_FILE = CONFIG_DIR / "workflow_statuses.yaml"

# Файлы базы знаний
TEAM_KNOWLEDGE_DIR = KNOWLEDGE_DIR / "team"
EMPLOYEES_KNOWLEDGE_DIR = KNOWLEDGE_DIR / "employees"

# Файлы команды
TEAM_MD_FILE = TEAM_KNOWLEDGE_DIR / "team.md"
ACHIEVEMENTS_MD_FILE = TEAM_KNOWLEDGE_DIR / "achievements.md"
COMPETENCIES_MD_FILE = TEAM_KNOWLEDGE_DIR / "competencies.md"
RESPONSIBILITIES_MD_FILE = TEAM_KNOWLEDGE_DIR / "responsibilities.md"

# Файлы продуктов
OLAP_KNOWLEDGE_FILE = KNOWLEDGE_DIR / "products" / "olap.md"
DATAMARTS_KNOWLEDGE_FILE = KNOWLEDGE_DIR / "products" / "datamarts.md"

# Файл источников
SOURCES_README_FILE = KNOWLEDGE_DIR / "sources" / "README.md"


class WorkflowStatusConfig:
    """Конфигурация статусной схемы AS21"""

    def __init__(self):
        self.config = None
        self._load()

    def _load(self):
        """Загрузить конфигурацию из YAML файла"""
        if WORKFLOW_STATUSES_FILE.exists():
            try:
                with open(WORKFLOW_STATUSES_FILE, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
            except Exception as e:
                print(f"Error loading workflow statuses config: {e}")
                self.config = {}
        else:
            self.config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Получить конфигурацию по умолчанию"""
        return {
            "statuses": {},
            "analytics": {
                "backlog_statuses": ["todo", "Open"],
                "waiting_statuses": ["Need info"],
                "active_work_statuses": ["in_progress", "In progress", "Reopened"],
                "review_queue_statuses": ["Ready for review"],
                "review_statuses": ["In review"],
                "qa_queue_statuses": ["Ready for QA"],
                "testing_statuses": ["QA"],
                "completed_statuses": ["done", "done", "Closed"],
                "cancelled_statuses": ["cancelled", "Cancelled"]
            },
            "cycle_time": {
                "start_status": "In progress",
                "default_end_status": "Closed"
            }
        }

    @property
    def statuses(self) -> Dict[str, Any]:
        """Получить все статусы"""
        return self.config.get("statuses", {})

    @property
    def analytics(self) -> Dict[str, Any]:
        """Получить настройки аналитики"""
        return self.config.get("analytics", {})

    @property
    def cycle_time(self) -> Dict[str, Any]:
        """Получить настройки cycle time"""
        return self.config.get("cycle_time", {})

    @property
    def basic_wip_statuses(self) -> list[str]:
        """Получить статусы для базового WIP"""
        return self.config.get("basic_wip_statuses", ["In progress", "In review", "QA", "Reopened"])

    @property
    def extended_wip_statuses(self) -> list[str]:
        """Получить статусы для расширенного WIP"""
        return self.config.get("extended_wip_statuses", ["In progress", "In review", "QA", "Reopened", "Ready for review", "Ready for QA"])

    @property
    def completed_statuses(self) -> list[str]:
        """Получить статусы завершенных задач"""
        return self.config.get("analytics", {}).get("completed_statuses", ["done", "Closed"])

    @property
    def cancelled_statuses(self) -> list[str]:
        """Получить статусы отмененных задач"""
        return self.config.get("analytics", {}).get("cancelled_statuses", ["cancelled", "Cancelled"])

    def normalize_status(self, status: str) -> str:
        """Нормализовать статус к стандартному формату"""
        if not status:
            return "todo"

        status_lower = status.lower().strip()

        # Маппинг статусов AS21 на стандартные
        status_mapping = {
            "open": "Open",
            "need info": "Need info",
            "in progress": "In progress",
            "ready for review": "Ready for review",
            "in review": "In review",
            "ready for qa": "Ready for QA",
            "qa": "QA",
            "reopened": "Reopened",
            "resolved": "Resolved",
            "closed": "Closed",
            "cancelled": "Cancelled",
            "todo": "Open",
            "in_progress": "In progress",
            "done": "Closed",
        }

        # Попытаться найти маппинг
        for key, value in status_mapping.items():
            if key.lower() == status_lower:
                return value

        # Если не найдено, вернуть как есть с большой буквы
        return status.title()


def get_employee_file(login: str) -> Path | None:
    """Получить путь к файлу профиля сотрудника по логину"""
    # Формат логина в именах файлов: Kalacanov_Viktor_Vaceslavovic.md
    # Нужно преобразовать Kalachanov.V.V -> Kalacanov_Viktor_Vaceslavovic
    normalized_login = login.replace(".", "_")
    employee_file = EMPLOYEES_KNOWLEDGE_DIR / f"{normalized_login}.md"

    if employee_file.exists():
        return employee_file
    return None


def get_all_employee_files() -> list[Path]:
    """Получить все файлы профилей сотрудников"""
    if not EMPLOYEES_KNOWLEDGE_DIR.exists():
        return []
    return list(EMPLOYEES_KNOWLEDGE_DIR.glob("*.md"))


def file_exists(path: Path) -> bool:
    """Проверить существование файла"""
    return path.exists()

