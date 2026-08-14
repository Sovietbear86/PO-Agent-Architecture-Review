"""PO Orchestrator v1 for PO Agent Platform v2.

Pipeline:
- request -> route -> validate entities -> select capability -> execute -> collect evidence -> deterministic answer or LLM synthesis

With Skill Registry integration:
- request -> route -> skill resolver -> skill executor -> execute -> collect evidence -> response
"""

from datetime import datetime
from typing import Optional

from po_agent.domain.models import Task
from po_agent.llm.client import LLMClient
from po_agent.llm.mock import MockLLMClient
from po_agent.orchestration.router import IntentClassification
from po_agent.orchestration.llm_fallback import LLIntentFallback
from po_agent.orchestration.llm_router import LLMIntentRouter
from po_agent.search.intelligence import TaskIntelligenceSearch
from po_agent.summary.task_summary import TaskSummaryService
from po_agent.analysis.task_quality import TaskQualityAnalysis
from po_agent.sprint.intelligence import SprintIntelligence
from po_agent.release.intelligence import ReleaseIntelligence
from po_agent.metrics.engine import MetricsEngine
from po_agent.history.store import OperationalHistory, TraceEntry
from po_agent.feedback.store import FeedbackStore, FeedbackType
from po_agent.versions.registry import VersionRegistry
from po_agent.skill.registry import SkillRegistry
from po_agent.skill.skills import INITIAL_SKILLS
from po_agent.skill.executor import SkillExecutor


class POOrchestratorV1:
    """PO Orchestrator v1 - deterministic pipeline.

    Pipeline:
    request -> route -> validate entities -> select capability -> execute -> evidence -> response
    
    TraceRecorder:
    - OperationalHistory for execution history
    - FeedbackStore for user feedback
    - VersionRegistry for version capture
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        history_db_path: str = ":memory:",
        feedback_db_path: str = ":memory:",
    ):
        """Initialize PO Orchestrator v1.

        Args:
            llm_client: LLM client for synthesis (optional)
            history_db_path: SQLite path for operational history
            feedback_db_path: SQLite path for user feedback
        """
        self.llm_client = llm_client or MockLLMClient()

        # Capabilities
        self._router = LLMIntentRouter(llm_client=self.llm_client)
        self._llm_fallback = LLIntentFallback(self.llm_client)
        self._search = TaskIntelligenceSearch()
        self._summary = TaskSummaryService(llm_client=self.llm_client)
        self._quality = TaskQualityAnalysis(llm_client=self.llm_client)
        self._sprint = SprintIntelligence(llm_client=self.llm_client)
        self._release = ReleaseIntelligence(llm_client=self.llm_client)
        self._metrics = MetricsEngine()

        # Skill Registry integration
        self._skill_registry = SkillRegistry()
        self._skill_registry.load_skills_from_dict(INITIAL_SKILLS)
        self._skill_executor = SkillExecutor(self._skill_registry)

        # Trace Recorder components
        self._history = OperationalHistory(db_path=history_db_path)
        self._feedback = FeedbackStore(db_path=feedback_db_path)
        self._versions = VersionRegistry(db_path=":memory:")

    async def process_request(
        self,
        query: str,
        session_id: Optional[str] = None,
        tasks: Optional[list[Task]] = None,
    ) -> dict:
        """Process user request through orchestrator pipeline.

        Args:
            query: User query
            session_id: Session ID for tracking (optional)
            tasks: Pre-fetched tasks (optional, will search if not provided)

        Returns:
            Response dictionary with intent, data, evidence
        """
        # Step 1: Route intent (await async classify)
        classification = await self._router.classify(query)

        # Step 2: Fallback for low confidence
        if classification.confidence < 0.5:
            classification = await self._llm_fallback.classify(
                query,
                classification.intent,
                classification.confidence,
            )

        # Step 3: Validate entities (simple validation)
        validated_entities = self._validate_entities(classification.entities)

        # Step 4: Select and execute capability (with skill tracking)
        result, skill_info = await self._execute_capability_with_skill(
            classification.intent,
            validated_entities,
            tasks,
            classification,  # Pass classification as 4th positional arg
        )

        # Step 5: Collect evidence
        evidence = self._collect_evidence(
            classification.intent,
            classification.entities,
            result,
        )

        # Step 6: Generate response
        response = await self._generate_response(
            classification.intent,
            result,
            evidence,
        )

        # Step 7: Save trace (TraceRecorder with skill info)
        from po_agent.versions.registry import VersionRegistry
        skill_id = skill_info.get("skill_id") if skill_info else None
        skill_version = skill_info.get("skill_version") if skill_info else None
        skill_status = result.get("type", "completed")

        self._save_trace(
            trace_id="trace-" + query.replace(" ", "-")[:20],
            request_id="req-" + query.replace(" ", "-")[:20],
            session_id=session_id,
            query=query,
            intent=classification.intent,
            intent_confidence=classification.confidence,
            latency_ms=0.0,  # Will be measured in actual API
            warning_count=0,
            skill_id=skill_id,
            skill_version=skill_version,
            skill_status=skill_status,
        )

        return {
            "query": query,
            "session_id": session_id,
            "intent": classification.intent,
            "intent_confidence": classification.confidence,
            "entities": validated_entities,
            "result": result,
            "evidence": evidence,
            "response": response,
            "router_version": classification.router_version,
        }

    def _save_trace(
        self,
        trace_id: str,
        request_id: str,
        session_id: Optional[str],
        query: str,
        intent: str,
        intent_confidence: float,
        latency_ms: float,
        error_count: int = 0,
        warning_count: int = 0,
        skill_id: Optional[str] = None,
        skill_version: Optional[str] = None,
        skill_status: Optional[str] = None,
    ) -> None:
        """Save trace to operational history.

        Args:
            trace_id: Unique trace ID
            request_id: Request ID
            session_id: Session ID
            query: User query
            intent: Classified intent
            intent_confidence: Confidence score
            latency_ms: Request latency
            error_count: Number of errors
            warning_count: Number of warnings
            skill_id: Skill ID (optional)
            skill_version: Skill version (optional)
            skill_status: Skill execution status (optional)
        """
        trace_entry = TraceEntry(
            trace_id=trace_id,
            request_id=request_id,
            session_id=session_id,
            timestamp=datetime.now(),
            request=query,
            intent=intent,
            intent_confidence=intent_confidence,
            latency_ms=latency_ms,
            error_count=error_count,
            warning_count=warning_count,
            skill_id=skill_id,
            skill_version=skill_version,
            skill_status=skill_status,
        )
        self._history.add_trace(trace_entry)

    def _save_feedback(
        self,
        feedback_id: str,
        trace_id: str,
        session_id: Optional[str],
        feedback_type: FeedbackType,
        data: dict,
        skill_id: Optional[str] = None,
        skill_version: Optional[str] = None,
    ) -> None:
        """Save user feedback.

        Args:
            feedback_id: Unique feedback ID
            trace_id: Linked trace ID
            session_id: Session ID
            feedback_type: Feedback type
            data: Feedback data
            skill_id: Skill ID (optional)
            skill_version: Skill version (optional)
        """
        # Add skill info to feedback data
        feedback_data = dict(data)
        if skill_id:
            feedback_data["skill_id"] = skill_id
        if skill_version:
            feedback_data["skill_version"] = skill_version

        self._feedback.add_feedback(
            feedback_id=feedback_id,
            trace_id=trace_id,
            session_id=session_id,
            feedback_type=feedback_type,
            data=feedback_data,
        )

    def _validate_entities(self, entities: list) -> list:
        """Validate extracted entities.

        Args:
            entities: Extracted entities

        Returns:
            Validated entities list
        """
        validated = []

        for entity in entities:
            # Simple validation - ensure required fields exist
            if entity.type and entity.value:
                validated.append(entity)

        return validated

    async def _execute_capability_with_skill(
        self,
        intent: str,
        entities: list,
        tasks: Optional[list[Task]] = None,
        classification: Optional[IntentClassification] = None,  # Added for LLM intent access
    ) -> tuple[dict, dict]:
        """Execute capability with skill info tracking.

        Args:
            intent: Classified intent
            entities: Extracted entities
            tasks: Pre-fetched tasks
            classification: Intent classification result for intent access

        Returns:
            Tuple of (result, skill_info)
        """
        # Fetch tasks if not provided
        if tasks is None:
            # Will be populated by adapter in real implementation
            tasks = []

        # Skill Registry integration: Determine skill from intent
        skill_info = self._router.resolve_intent_to_skill(intent)

        if skill_info:
            # Execute using SkillExecutor
            result = await self._execute_with_skill(
                skill_info,
                entities,
                tasks,
                classification,  # Pass classification for intent access
            )
        else:
            # Fallback to direct capability execution
            result = await self._execute_direct_capability(intent, entities, tasks)

        return result, skill_info if skill_info else {"skill_id": None, "skill_version": None}

    async def _execute_with_skill(
        self,
        skill_info: dict,
        entities: list,
        tasks: list,
        classification: IntentClassification,  # Added parameter
    ) -> dict:
        """Execute capability using SkillExecutor.

        Args:
            skill_info: Skill definition info from registry
            entities: Extracted entities
            tasks: Pre-fetched tasks

        Returns:
            Capability result
        """
        skill_id = skill_info["skill_id"]
        required_context = skill_info.get("required_context", [])
        optional_context = skill_info.get("optional_context", [])

        # Build context from entities
        context = {
            "skill_id": skill_id,
            "entities": entities,
        }

        # Add optional context from entities
        for entity in entities:
            if entity.type == "sprint":
                context["sprint_id"] = entity.value
            elif entity.type == "release":
                context["release_id"] = entity.value
            elif entity.type == "member":
                context["member_login"] = entity.value
            elif entity.type == "task_key":
                context["task_id"] = entity.value
            elif entity.type == "product":
                context["product"] = entity.value

        # Check required context
        missing_required = []
        for req in required_context:
            if req not in context:
                missing_required.append(req)

        if missing_required:
            return {
                "type": "clarification_required",
                "skill_id": skill_id,
                "missing_context": missing_required,
            }

        # Execute using capability methods
        # Use intent from classification instead of skill registry lookup
        intent = classification.intent

        if intent == "task_search":
            return self._execute_task_search(entities)
        elif intent == "task_summary":
            return await self._execute_task_summary(entities, tasks)
        elif intent == "task_quality":
            return await self._execute_task_quality(entities, tasks)
        elif intent == "sprint_health":
            return self._execute_sprint_health(entities, tasks)
        elif intent == "velocity":
            return self._execute_velocity(tasks)
        elif intent == "release_health":
            return self._execute_release_health(entities, tasks)
        elif intent == "help":
            return {"type": "help", "message": "Я помогу с анализом задач, спринтов и релизов."}
        else:
            return {"type": "unknown", "message": "Неизвестный запрос"}

    async def _execute_direct_capability(
        self,
        intent: str,
        entities: list,
        tasks: list,
    ) -> dict:
        """Execute capability directly (fallback method).

        Args:
            intent: Classified intent
            entities: Extracted entities
            tasks: Pre-fetched tasks

        Returns:
            Capability result
        """
        # Fetch tasks if not provided
        if tasks is None:
            # Will be populated by adapter in real implementation
            tasks = []

        if intent == "task_search":
            return self._execute_task_search(entities)
        elif intent == "task_summary":
            return await self._execute_task_summary(entities, tasks)
        elif intent == "task_quality":
            return await self._execute_task_quality(entities, tasks)
        elif intent == "sprint_health":
            return self._execute_sprint_health(entities, tasks)
        elif intent == "velocity":
            return self._execute_velocity(tasks)
        elif intent == "release_health":
            return self._execute_release_health(entities, tasks)
        elif intent == "help":
            return {"type": "help", "message": "Я помогу с анализом задач, спринтов и релизов."}
        else:
            return {"type": "unknown", "message": "Неизвестный запрос"}

    def _execute_task_search(self, entities: list) -> dict:
        """Execute task search capability."""
        phrase = ""
        assignee = ""
        sprint = ""
        release = ""

        for entity in entities:
            if entity.type == "member":
                assignee = entity.value
            elif entity.type == "sprint":
                sprint = entity.value
            elif entity.type == "release":
                release = entity.value

        # Extract phrase from entities
        if entities and entities[0].type == "task_key":
            phrase = entities[0].value

        return {
            "type": "task_search",
            "results": [],
            "filters": {
                "phrase": phrase,
                "assignee": assignee,
                "sprint": sprint,
                "release": release,
            },
        }

    async def _execute_task_summary(
        self,
        entities: list,
        tasks: list,
    ) -> dict:
        """Execute task summary capability."""
        task_key = ""
        for entity in entities:
            if entity.type == "task_key":
                task_key = entity.value
                break

        if task_key and tasks:
            task = next((t for t in tasks if t.key == task_key), None)
            if task:
                summary = await self._summary.generate_llm_summary(task)
                return {
                    "type": "task_summary",
                    "task_key": task_key,
                    "summary": summary,
                }

        return {"type": "task_summary", "message": "Задача не найдена"}

    async def _execute_task_quality(
        self,
        entities: list,
        tasks: list,
    ) -> dict:
        """Execute task quality analysis capability."""
        task_key = ""
        for entity in entities:
            if entity.type == "task_key":
                task_key = entity.value
                break

        if task_key and tasks:
            task = next((t for t in tasks if t.key == task_key), None)
            if task:
                report = await self._quality.generate_quality_report_with_llm(task)
                return {
                    "type": "task_quality",
                    "task_key": task_key,
                    "report": report,
                }

        return {"type": "task_quality", "message": "Задача не найдена"}

    def _execute_sprint_health(self, entities: list, tasks: list) -> dict:
        """Execute sprint health capability."""
        sprint_id = ""
        for entity in entities:
            if entity.type == "sprint":
                sprint_id = entity.value
                break

        return {
            "type": "sprint_health",
            "sprint_id": sprint_id,
            "tasks_count": len(tasks),
        }

    def _execute_velocity(self, tasks: list) -> dict:
        """Execute velocity capability."""
        return {
            "type": "velocity",
            "tasks_count": len(tasks),
        }

    def _execute_release_health(self, entities: list, tasks: list) -> dict:
        """Execute release health capability."""
        release_id = ""
        for entity in entities:
            if entity.type == "release":
                release_id = entity.value
                break

        return {
            "type": "release_health",
            "release_id": release_id,
            "tasks_count": len(tasks),
        }

    def _collect_evidence(self, intent: str, entities: list, result: dict) -> list:
        """Collect evidence from execution.

        Args:
            intent: Classified intent
            entities: Extracted entities
            result: Capability result

        Returns:
            List of evidence items
        """
        evidence = []

        if entities:
            evidence.append({
                "source_type": "entities",
                "source_id": None,
                "fact": "extracted entities",
                "value": [{"type": e.type, "value": e.value} for e in entities],
            })

        if result.get("type"):
            evidence.append({
                "source_type": "capability",
                "source_id": intent,
                "fact": "capability executed",
                "value": result.get("type"),
            })

        if result.get("results"):
            evidence.append({
                "source_type": "capability",
                "source_id": intent,
                "fact": "search results",
                "value": len(result["results"]),
            })

        return evidence

    async def _generate_response(
        self,
        intent: str,
        result: dict,
        evidence: list,
    ) -> str:
        """Generate response using deterministic or LLM synthesis.

        Args:
            intent: Classified intent
            result: Capability result
            evidence: Collected evidence

        Returns:
            Response string
        """
        # Deterministic fallback
        if intent == "help":
            return (
                "Я могу помочь с:\n"
                "- Поиском задач по фразе, ключу, исполнителю, спринту, релизу\n"
                "- Анализом качества задач\n"
                "- Здоровьем спринта и скоростью команды\n"
                "- Состоянием релизов\n\n"
                "Что хотите проанализировать?"
            )

        if intent == "task_search":
            count = len(result.get("results", []))
            return f"Найдено {count} задач по вашему запросу."

        if intent == "task_summary":
            if result.get("summary"):
                return result["summary"]
            return "Не удалось сгенерировать резюме задачи."

        if intent == "task_quality":
            if result.get("report"):
                return f"Качество задачи: {result['report'].get('quality_level', 'unknown')} (score: {result['report'].get('score', 0)})"
            return "Не удалось проанализировать качество задачи."

        if intent == "sprint_health":
            return f"Анализ спринта {result.get('sprint_id', 'неизвестный')}. Всего задач: {result.get('tasks_count', 0)}."

        if intent == "velocity":
            return f"Анализ скорости команды. Обработано задач: {result.get('tasks_count', 0)}."

        if intent == "release_health":
            return f"Состояние релиза {result.get('release_id', 'неизвестный')}. Всего задач: {result.get('tasks_count', 0)}."

        return "Запрос обработан."
