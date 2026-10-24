"""LLM-based Intent Router for PO Agent Platform v2.

Primary intent classification using LLM with few-shot learning.
Fallback to deterministic patterns for known phrases.

This enables the agent to generalize from examples rather than
hardcoding every possible Russian phrase variation.
"""

import json
import re
from typing import Optional

from po_agent.llm.client import LLMClient, LLMMessage
from po_agent.orchestration.router import (
    IntentClassification,
    Entity,
    IntentRouterRequest,
    IntentRouterResponse,
)
from po_agent.skill.registry import SkillRegistry
from po_agent.skill.skills import INITIAL_SKILLS


# Import regex for fast path patterns
from po_agent.orchestration.router import DeterministicIntentRouter


class LLMIntentRouter:
    """LLM-based intent router with deterministic fallback.

    Architecture:
    1. Fast deterministic check for known phrases
    2. LLM classification for ambiguous or new phrases
    3. Fallback to deterministic for confidence < 0.5

    Benefits:
    - Generalizes from examples (few-shot learning)
    - Handles Russian phrase variations naturally
    - Easy to add new intents without code changes
    - Maintains deterministic speed for known patterns
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
    ):
        """Initialize LLM intent router.

        Args:
            llm_client: LLM client for intent classification (optional)
        """
        self.llm_client = llm_client
        self.skill_registry = SkillRegistry()
        self.skill_registry.load_skills_from_dict(INITIAL_SKILLS)

        # Deterministic patterns for fast path (high confidence)
        self.fast_patterns = {
            "task_search": [
                r"покажи задачи",
                r"найди задачи",
                r"задачи с",
                r"поиск задач",
            ],
            "task_summary": [
                r"резюме задачи",
                r"что по задаче",
                r"описание задачи",
            ],
            "task_quality": [
                r"качество задачи",
                r"анализ качества",
            ],
            "sprint_health": [
                r"здоровье спринта",
                r"метрики спринта",
            ],
            "velocity": [
                r"скорость команды",
                r"velocity",
            ],
            "team_workload": [
                r"загрузка команды",
                r"баланс загрузки",
            ],
            "competency_match": [
                r"по компетенциям",
                r"подбор компетенций",
            ],
            "release_health": [
                r"здоровье релиза",
                r"статус релиза",
            ],
            "help": [
                r"помощь",
                r"что умеешь",
            ],
        }

        # Few-shot examples for LLM
        self.examples = [
            {
                "query": "покажи задачи из спринта DMS-SPRNT-1",
                "intent": "task_search",
                "entities": [
                    {"type": "sprint", "value": "DMS-SPRNT-1"}
                ],
            },
            {
                "query": "задачи Гаранина в текущем спринте",
                "intent": "task_search",
                "entities": [
                    {"type": "member", "value": "Гаранин"},
                    {"type": "sprint", "value": "current_sprint"}
                ],
            },
            {
                "query": "что ты умеешь",
                "intent": "help",
                "entities": [],
            },
            {
                "query": "суммаризируй задачу WMB-123",
                "intent": "task_summary",
                "entities": [
                    {"type": "task_key", "value": "WMB-123"}
                ],
            },
            {
                "query": "подбери специалиста по Python",
                "intent": "competency_match",
                "entities": [
                    {"type": "member", "value": "Python"}
                ],
            },
            {
                "query": "покажи задачи Калачанова",
                "intent": "task_search",
                "entities": [
                    {"type": "member", "value": "Калачанов"}
                ],
            },
        ]

        # Build regex patterns from fast_patterns
        self._compiled_patterns = {}
        for intent, patterns in self.fast_patterns.items():
            combined = "|".join(f"(?:{p})" for p in patterns)
            self._compiled_patterns[intent] = re.compile(combined, re.IGNORECASE)

    def classify_fast(self, query: str) -> Optional[IntentClassification]:
        """Fast deterministic classification for known patterns.

        Returns high-confidence classification for known phrases.
        Returns None if query doesn't match known patterns.

        Args:
            query: User query

        Returns:
            Intent classification with high confidence, or None
        """
        query_lower = query.lower().strip()

        for intent, pattern in self._compiled_patterns.items():
            if pattern.search(query_lower):
                entities = self._extract_entities(query_lower, intent)
                return IntentClassification(
                    intent=intent,
                    confidence=0.9,
                    entities=entities,
                    router_version="2.0.0",
                )

        return None

    def _extract_entities(self, query_lower: str, intent: str) -> list[Entity]:
        """Extract entities from query using DeterministicIntentRouter logic."""
        # Use DeterministicIntentRouter's _extract_entities
        det_router = DeterministicIntentRouter()
        return det_router._extract_entities(query_lower, intent)

    async def classify_with_llm(self, query: str) -> IntentClassification:
        """Classify intent using LLM with few-shot learning.

        Args:
            query: User query

        Returns:
            Intent classification
        """
        system_prompt = """You are an intent classifier for a Product Owner Agent Platform.

Available intents:
1. task_search - поиск задач по фразе, ключу, исполнителю, спринту, релизу
2. task_summary - резюме задачи, что по задаче, подробности
3. task_quality - анализ качества задачи, полная ли задача
4. sprint_health - здоровье спринта, метрики спринта
5. velocity - скорость команды, производительность
6. team_workload - загрузка команды, баланс загрузки
7. competency_match - подбор по компетенциям, кто подходит
8. release_health - здоровье релиза, статус релиза
9. help - помощь, что умеешь

Extract entities:
- sprint: DMS-SPRNT-1, current_sprint, any sprint identifier
- release: DMS-2024-Q3, REL-*, any release identifier
- member: any person name (Russian or login)
- task_key: WMB-123, DMS-456, any task identifier

Output format (JSON only):
{
    "intent": "<intent_name>",
    "confidence": <0.0-1.0>,
    "entities": [
        {"type": "<type>", "value": "<value>"}
    ]
}"""

        # Build few-shot prompt
        examples_text = "\n".join(
            f'Query: "{ex["query"]}"\n'
            f'Response: {json.dumps({"intent": ex["intent"], "entities": ex["entities"]})}'
            for ex in self.examples[:5]  # Top 5 examples
        )

        user_prompt = f"""Examples:
{examples_text}

Now classify this query:
Query: "{query}"

Output JSON only:"""

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

        try:
            if self.llm_client:
                response = await self.llm_client.complete(messages)
                content = response.choices[0].message.content if response.choices else ""
            else:
                # Fallback for testing without LLM
                content = '{"intent": "help", "confidence": 0.5, "entities": []}'

            # Parse JSON
            data = json.loads(content.strip())
            intent = data.get("intent", "help")
            confidence = float(data.get("confidence", 0.5))

            # Validate intent
            allowed_intents = list(self.fast_patterns.keys())
            if intent not in allowed_intents:
                intent = "help"
                confidence = 0.3

            # Extract entities
            entities_data = data.get("entities", [])
            entities = [
                Entity(type=e.get("type", "unknown"), value=e.get("value", ""))
                for e in entities_data
            ]

            return IntentClassification(
                intent=intent,
                confidence=confidence,
                entities=entities,
                router_version="2.0.0",
            )

        except (json.JSONDecodeError, Exception) as e:
            # Fallback to deterministic
            fast_result = self.classify_fast(query)
            if fast_result:
                return fast_result

            return IntentClassification(
                intent="help",
                confidence=0.0,
                entities=[],
                router_version="2.0.0",
            )

    async def classify(self, query: str) -> IntentClassification:
        """Classify intent with fast path + LLM fallback.

        Strategy:
        1. Try fast deterministic first (for known phrases)
        2. If low confidence or no match, use LLM

        Args:
            query: User query

        Returns:
            Intent classification
        """
        # Fast path for known patterns
        fast_result = self.classify_fast(query)
        if fast_result and fast_result.confidence >= 0.8:
            return fast_result

        # LLM classification for ambiguous cases (async)
        return await self.classify_with_llm(query)

    def resolve_intent_to_skill(self, intent: str) -> Optional[dict]:
        """Resolve intent to skill using SkillRegistry.

        Args:
            intent: Classified intent

        Returns:
            Skill info dict or None
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
        """Get intent from skill_id."""
        return self.skill_registry.get_intent_from_skill(skill_id)

    @property
    def INTENT_TO_SKILL(self) -> dict[str, str]:
        """Intent to Skill mapping."""
        return {
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
