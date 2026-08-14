"""LLM Intent Fallback for PO Agent Platform v2.

Used only when deterministic routing has low confidence.
Strict JSON schema, allowlisted intents only.
"""

import json
from typing import Optional

from po_agent.llm.client import LLMClient, LLMMessage, LLMResponse
from po_agent.orchestration.router import IntentClassification, Entity


class LLIntentFallback:
    """LLM-based intent fallback for low-confidence routing.

    Rules:
    - Only for confidence < 0.5 from deterministic router
    - Strict JSON schema
    - Allowlisted intents only
    - Invalid output -> unknown/help
    """

    def __init__(
        self,
        llm_client: LLMClient,
    ):
        """Initialize LLM intent fallback.

        Args:
            llm_client: LLM client for intent classification
        """
        self.llm_client = llm_client

    async def classify(
        self,
        query: str,
        deterministic_intent: Optional[str] = None,
        deterministic_confidence: float = 0.0,
    ) -> IntentClassification:
        """Classify intent using LLM fallback.

        Only called when deterministic confidence is low (< 0.5).

        Args:
            query: User query
            deterministic_intent: Intent from deterministic router (if any)
            deterministic_confidence: Confidence from deterministic router

        Returns:
            Intent classification result
        """
        system_prompt = """You are an intent classifier for a PO Agent Platform.

Available intents (choose exactly one):
- task_search: поиск задач по фразе, ключу, исполнителю, спринту, релизу
- task_summary: резюме задачи, что по задаче
- task_quality: анализ качества задачи, полная ли задача
- sprint_health: здоровье спринта, метрики спринта
- velocity: скорость команды, производительность
- team_workload: загрузка команды, баланс загрузки
- competency_match: подбор по компетенциям, кто подходит
- release_health: здоровье релиза, статус релиза
- help: помощь, что умеешь

Output format (JSON only, no other text):
{
    "intent": "<one_of_the_allowed_intents>",
    "confidence": 0.85,
    "entities": [
        {"type": "sprint|release|member|task_key", "value": "..." }
    ]
}
"""
        user_prompt = f"""Query: "{query}"

Previous deterministic result: {deterministic_intent} (confidence: {deterministic_confidence})

Please classify the intent and extract entities."""
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

        try:
            response: LLMResponse = await self.llm_client.complete(messages)
            content = response.choices[0].message.content if response.choices else ""

            # Parse JSON
            try:
                data = json.loads(content)
                intent = data.get("intent", "")
                confidence = data.get("confidence", 0.0)
                entities_data = data.get("entities", [])

                # Validate intent
                allowed_intents = [
                    "task_search",
                    "task_summary",
                    "task_quality",
                    "sprint_health",
                    "velocity",
                    "team_workload",
                    "competency_match",
                    "release_health",
                    "help",
                ]

                if intent not in allowed_intents:
                    intent = "help"
                    confidence = 0.0

                # Parse entities
                entities = [
                    Entity(type=e.get("type", ""), value=e.get("value", ""))
                    for e in entities_data
                ]

                return IntentClassification(
                    intent=intent,
                    confidence=confidence,
                    entities=entities,
                    router_version="1.0.0",
                )

            except (json.JSONDecodeError, KeyError, TypeError):
                # Fallback to help
                return IntentClassification(
                    intent="help",
                    confidence=0.0,
                    entities=[],
                    router_version="1.0.0",
                )

        except Exception as e:
            print(f"LLM intent fallback error: {e}")
            return IntentClassification(
                intent="help",
                confidence=0.0,
                entities=[],
                router_version="1.0.0",
            )
