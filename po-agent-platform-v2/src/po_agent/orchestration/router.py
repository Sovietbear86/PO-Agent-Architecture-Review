"""Intent Router for PO Agent Platform v2.

Deterministic intent classification with LLM fallback.
Supports:
- task_search
- task_summary
- task_quality
- sprint_health
- velocity
- team_workload
- competency_match
- release_health
- help
"""

import re
from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel

from po_agent.skill.registry import SkillRegistry
from po_agent.skill.skills import INITIAL_SKILLS


@dataclass
class Entity:
    """Extracted entity from query."""
    type: str  # sprint, release, member, task_key
    value: str


@dataclass
class IntentClassification:
    """Intent classification result."""
    intent: str
    confidence: float
    entities: list[Entity]
    router_version: str = "1.0.0"


class IntentRouterRequest(BaseModel):
    """Request for intent routing."""
    query: str
    session_id: Optional[str] = None


class IntentRouterResponse(BaseModel):
    """Response from intent router."""
    intent: str
    confidence: float
    entities: list[dict]
    router_version: str = "1.0.0"


class DeterministicIntentRouter:
    """Deterministic intent router with Russian phrase matching.

    Intents:
    - task_search: поиск задач
    - task_summary: резюме задачи
    - task_quality: анализ качества
    - sprint_health: здоровье спринта
    - velocity: скорость команды
    - team_workload: загрузка команды
    - competency_match: подбор по компетенциям
    - release_health: здоровье релиза
    - help: помощь

    Also provides SkillResolver for intent -> skill mapping.
    """

    # Intent to Skill mapping
    INTENT_TO_SKILL: dict[str, str] = {
        "task_search": "task_search",
        "task_summary": "task_summary",
        "task_quality": "task_quality",
        "sprint_health": "sprint_health",
        "velocity": "velocity",
        "team_workload": "team_workload",
        "competency_match": "competency_match",
        "release_health": "release_health",
        "help": "help",
    }

    def __init__(self):
        """Initialize deterministic intent router."""
        self.router_version = "1.0.0"
        self.skill_registry = SkillRegistry()
        self.skill_registry.load_skills_from_dict(INITIAL_SKILLS)

        # Intent patterns (Russian phrases)
        self.patterns = {
            "task_search": [
                r"покажи задачи",
                r"найди задачи",
                r"задачи с phrase",
                r"поиск задач",
                r"задачи по",
                r"по фразе",
                r"по ключу",
                r"по исполнителю",
                r"по спринту",
                r"по релизу",
                r"по вложению",
            ],
            "task_summary": [
                r"резюме задачи",
                r"что по задаче",
                r"описание задачи",
                r"подробности задачи",
                r"анализ задачи",
            ],
            "task_quality": [
                r"качество задачи",
                r"полная ли задача",
                r"не хватает",
                r"качество",
                r"дефекты в задаче",
                r"анализ качества",
            ],
            "sprint_health": [
                r"здоровье спринта",
                r"метрики спринта",
                r"состояние спринта",
                r"sprit health",
                r"прогресс спринта",
                r"как проходит спринт",
            ],
            "velocity": [
                r"скорость команды",
                r"velocity",
                r"производительность",
                r"выработка",
                r"скорость работы",
            ],
            "team_workload": [
                r"загрузка команды?",
                r"баланс загрузки?",
                r"кто загружен?",
                r"распределение задач",
                r"перегрузка",
                r"недогрузка",
            ],
            "competency_match": [
                r"кто подходит",
                r"подбор компетенций",
                r"по компетенциям",
                r"кто умеет",
                r"совпадение навыков",
            ],
            "release_health": [
                r"здоровье релиза?",
                r"релиз прогресс",
                r"статус релиза?",
                r"релизные задачи",
                r"релиз готов",
                r"предстоящий релиз",
            ],
            "help": [
                r"помощь",
                r"что умеешь?",
                r"справка",
                r"инструкция",
                r"как использовать",
            ],
        }

    def classify(self, query: str) -> IntentClassification:
        """Classify intent using deterministic pattern matching.

        Args:
            query: User query in Russian

        Returns:
            Intent classification result
        """
        query_lower = query.lower().strip()

        # Try exact phrase matches first
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    entities = self._extract_entities(query_lower, intent)
                    return IntentClassification(
                        intent=intent,
                        confidence=0.9,
                        entities=entities,
                        router_version=self.router_version,
                    )

        # Fallback to less specific patterns
        fallback_patterns = {
            "task_search": [
                r"задачи",
                r"task",
                r"find",
                r"search",
            ],
            "sprint_health": [
                r"спринт",
                r"sprint",
                r"SPRNT",
            ],
            "velocity": [
                r"скорость",
                r"velocity",
                r"скорость команды",
            ],
            "team_workload": [
                r"команда",
                r"работа",
                r"загрузка",
            ],
            "release_health": [
                r"релиз",
                r"release",
                r"REL",
            ],
        }

        for intent, patterns in fallback_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    entities = self._extract_entities(query_lower, intent)
                    return IntentClassification(
                        intent=intent,
                        confidence=0.5,
                        entities=entities,
                        router_version=self.router_version,
                    )

        # Default to help
        return IntentClassification(
            intent="help",
            confidence=0.0,
            entities=[],
            router_version=self.router_version,
        )

    def _extract_entities(self, query_lower: str, intent: str) -> list[Entity]:
        """Extract entities from query based on intent.

        Args:
            query_lower: Lowercase query
            intent: Classified intent

        Returns:
            List of extracted entities
        """
        entities = []

        # Sprint pattern: DMS-SPRNT-1, "текущий спринт", "нынешний спринт", etc.
        # Priority order: exact matches first
        sprint_patterns = [
            r"текущий\s*спринт",
            r"нынешний\s*спринт",
            r"SPRNT-[\w-]+",
        ]
        for pattern in sprint_patterns:
            sprint_match = re.search(pattern, query_lower, re.IGNORECASE)
            if sprint_match:
                value = sprint_match.group(0)
                if "текущий" in value or "нынешний" in value:
                    value = "current_sprint"
                entities.append(Entity(
                    type="sprint",
                    value=value,
                ))
                break
        
        # Also extract sprint IDs if mentioned
        sprint_id_pattern = r"spri\u043d\u0442[-\s]*(?:№|номер)?\s*[\w-]+"
        sprint_id_match = re.search(sprint_id_pattern, query_lower, re.IGNORECASE)
        if sprint_id_match and "current_sprint" not in query_lower:
            entities.append(Entity(
                type="sprint",
                value=sprint_id_match.group(0),
            ))

        # Release pattern: DMS-2024-Q3, REL-*, etc.
        release_pattern = r"(?:REL[-\w]+|2024-Q\d)"
        release_match = re.search(release_pattern, query_lower, re.IGNORECASE)
        if release_match:
            entities.append(Entity(
                type="release",
                value=release_match.group(0),
            ))

        # Task key pattern: WMB-123
        task_key_pattern = r"[A-Z]+-\d+"
        task_keys = re.findall(task_key_pattern, query_lower)
        for task_key in task_keys[:2]:  # Limit to first 2
            entities.append(Entity(
                type="task_key",
                value=task_key,
            ))

        # Member pattern (common Russian surnames + team members from config)
        # Surnames: Kalachanov, Garanin, Agataeva, Alekseev, Galtsov, Dolgovskoy, 
        # Kondratchikova, Kryukov, Makoshina, Moiseev, Semavin, Goncharov, Reshetnik,
        # Kuznetsov, Bezrukov, Shaldunov
        member_patterns = [
            r"(?:Иванов|Петров|Сидоров|Смирнов|Кузнецов|Попов|Васильев|Михайлов|"
            r"Калачанов|Гаранин|Агатаева|Алексеев|Гальцов|Долговской|Кондратчикова|"
            r"Крюков|Макошина|Моисеев|Семавин|Гончаров|Решетник|Кузнецов|Безруков|Шалдунов)",
            r"[А-Я][а-я]+\.[А-Я]\.\s*[А-Я][а-я]+",  # Initials format
        ]

        for pattern in member_patterns:
            member_match = re.search(pattern, query_lower)
            if member_match:
                entities.append(Entity(
                    type="member",
                    value=member_match.group(0),
                ))
                break

        return entities

    def resolve_intent_to_skill(
        self,
        intent: str,
        confidence: float = 0.0,
    ) -> Optional[dict]:
        """Resolve intent to skill using SkillRegistry.

        This is the Skill Resolver in the ADDENDUM 01 flow.

        Args:
            intent: Classified intent
            confidence: Classification confidence

        Returns:
            Skill info dict or None if skill not found
        """
        skill_id = self.INTENT_TO_SKILL.get(intent)

        if skill_id is None:
            return None

        skill = self.skill_registry.get_active_skill(skill_id)

        if skill is None:
            return None

        return {
            "skill_id": skill.skill_id,
            "skill_name": skill.name,
            "skill_version": skill.version,
            "required_context": skill.required_context,
            "optional_context": skill.optional_context,
            "allowed_capabilities": skill.allowed_capabilities,
            "workflow": [w.model_dump() for w in skill.workflow],
        }

    def get_intent_from_skill(self, skill_id: str) -> Optional[str]:
        """Get intent from skill_id.

        Args:
            skill_id: Skill ID

        Returns:
            Intent string or None
        """
        for intent, sid in self.INTENT_TO_SKILL.items():
            if sid == skill_id:
                return intent
        return None

