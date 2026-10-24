"""Initial skill definitions for PO Agent Platform v2.

Skills:
- task_search: поиск задач
- task_summary: резюме задачи
- task_quality: анализ качества
- sprint_health: здоровье спринта
- velocity: скорость команды
- team_workload: загрузка команды
- competency_match: подбор по компетенциям
- release_health: здоровье релиза
- help: помощь

Each skill defines:
- skill_id
- version
- intents (what triggers the skill)
- required_context
- optional_context
- allowed_capabilities
- workflow steps
"""

from po_agent.skill.models import (
    SkillDefinition,
    ClarificationPolicy,
    WorkflowStep,
)

# Skill 1: task_search
SKILL_TASK_SEARCH = SkillDefinition(
    skill_id="task_search",
    name="Поиск задач",
    version="1.0.0",
    intents=[
        "task_search",
        "find_tasks",
        "search_tasks",
    ],
    description="Поиск задач по критериям (спринт, исполнитель, фраза)",
    required_context=["sprint_id"],
    optional_context=["member_login", "release_id", "phrase"],
    clarification_policy=ClarificationPolicy.AUTO,
    allowed_capabilities=["search_tasks"],
    workflow=[
        WorkflowStep(
            name="resolve_context",
            description="Resolve search context",
        ),
        WorkflowStep(
            name="execute_search",
            description="Execute task search",
            capability="search_tasks",
            input_mapping={
                "sprint_id": "sprint_id",
                "member_login": "assignee",
                "release_id": "release_id",
            },
        ),
    ],
)

# Skill 2: task_summary
SKILL_TASK_SUMMARY = SkillDefinition(
    skill_id="task_summary",
    name="Резюме задачи",
    version="1.0.0",
    intents=["task_summary", "get_task", "task_details"],
    description="Получить резюме задачи (статус, оценка, прогресс)",
    required_context=["task_id"],
    optional_context=[],
    clarification_policy=ClarificationPolicy.AUTO,
    allowed_capabilities=["get_task"],
    workflow=[
        WorkflowStep(
            name="resolve_context",
            description="Resolve task context",
        ),
        WorkflowStep(
            name="load_task",
            description="Load task details",
            capability="get_task",
        ),
        WorkflowStep(
            name="synthesize_summary",
            description="Generate summary",
        ),
    ],
)

# Skill 3: task_quality
SKILL_TASK_QUALITY = SkillDefinition(
    skill_id="task_quality",
    name="Анализ качества задачи",
    version="1.0.0",
    intents=["task_quality", "quality_check", "defects"],
    description="Проверить качество задачи (полность, соответствие шаблону)",
    required_context=["task_id"],
    optional_context=[],
    clarification_policy=ClarificationPolicy.AUTO,
    allowed_capabilities=["get_task", "analyze_quality"],
    workflow=[
        WorkflowStep(
            name="resolve_context",
            description="Resolve task context",
        ),
        WorkflowStep(
            name="load_task",
            description="Load task details",
            capability="get_task",
        ),
        WorkflowStep(
            name="analyze_quality",
            description="Analyze task quality",
            capability="analyze_quality",
        ),
    ],
)

# Skill 4: sprint_health
SKILL_SPRINT_HEALTH = SkillDefinition(
    skill_id="sprint_health",
    name="Здоровье спринта",
    version="1.0.0",
    intents=["sprint_health", "sprint_status", "sprint_metrics"],
    description="Метрики спринта (committed scope, completed scope, blocked)",
    required_context=["sprint_id"],
    optional_context=["member_login"],
    clarification_policy=ClarificationPolicy.AUTO,
    allowed_capabilities=["get_sprint", "calculate_metrics"],
    workflow=[
        WorkflowStep(
            name="resolve_context",
            description="Resolve sprint context",
        ),
        WorkflowStep(
            name="load_sprint",
            description="Load sprint tasks",
            capability="get_sprint",
        ),
        WorkflowStep(
            name="calculate_metrics",
            description="Calculate sprint metrics",
            capability="calculate_metrics",
        ),
    ],
)

# Skill 5: velocity
SKILL_VELOCITY = SkillDefinition(
    skill_id="velocity",
    name="Скорость команды",
    version="1.0.0",
    intents=["velocity", "speed", "throughput"],
    description="Velocity команды за период",
    required_context=["product"],
    optional_context=["member_login", "period_sprints"],
    clarification_policy=ClarificationPolicy.AUTO,
    allowed_capabilities=["get_velocity"],
    workflow=[
        WorkflowStep(
            name="resolve_context",
            description="Resolve velocity context",
        ),
        WorkflowStep(
            name="load_velocity",
            description="Load velocity data",
            capability="get_velocity",
        ),
    ],
)

# Skill 6: team_workload
SKILL_TEAM_WORKLOAD = SkillDefinition(
    skill_id="team_workload",
    name="Загрузка команды",
    version="1.0.0",
    intents=["team_workload", "workload", "load_balance"],
    description="Баланс загрузки между членами команды",
    required_context=["product"],
    optional_context=["member_login"],
    clarification_policy=ClarificationPolicy.AUTO,
    allowed_capabilities=["get_workload"],
    workflow=[
        WorkflowStep(
            name="resolve_context",
            description="Resolve workload context",
        ),
        WorkflowStep(
            name="load_workload",
            description="Load workload data",
            capability="get_workload",
        ),
    ],
)

# Skill 7: competency_match
SKILL_COMPETENCY_MATCH = SkillDefinition(
    skill_id="competency_match",
    name="Подбор по компетенциям",
    version="1.0.0",
    intents=["competency_match", "match_skills", "skills_match"],
    description="Найти сотрудника с нужными компетенциями для задачи",
    required_context=["task_id", "member_login"],
    optional_context=[],
    clarification_policy=ClarificationPolicy.AUTO,
    allowed_capabilities=["match_competency"],
    workflow=[
        WorkflowStep(
            name="resolve_context",
            description="Resolve competency context",
        ),
        WorkflowStep(
            name="load_requirements",
            description="Load task requirements",
            capability="get_task",
        ),
        WorkflowStep(
            name="match_competency",
            description="Match competencies",
            capability="match_competency",
        ),
    ],
)

# Skill 8: release_health
SKILL_RELEASE_HEALTH = SkillDefinition(
    skill_id="release_health",
    name="Здоровье релиза",
    version="1.0.0",
    intents=["release_health", "release_status", "release_progress"],
    description="Статус релиза и прогресс выполнения",
    required_context=["release_id"],
    optional_context=["member_login"],
    clarification_policy=ClarificationPolicy.AUTO,
    allowed_capabilities=["get_release", "calculate_release_progress"],
    workflow=[
        WorkflowStep(
            name="resolve_context",
            description="Resolve release context",
        ),
        WorkflowStep(
            name="load_release",
            description="Load release data",
            capability="get_release",
        ),
    ],
)

# Skill 9: help
SKILL_HELP = SkillDefinition(
    skill_id="help",
    name="Помощь",
    version="1.0.0",
    intents=["help", "what_can_you_do", "supported_queries"],
    description="Показать доступные запросы",
    required_context=[],
    optional_context=[],
    clarification_policy=ClarificationPolicy.NEVER,
    allowed_capabilities=[],
    workflow=[
        WorkflowStep(
            name="get_help",
            description="Return help text",
        ),
    ],
)


# List of all initial skills
INITIAL_SKILLS = [
    SKILL_TASK_SEARCH,
    SKILL_TASK_SUMMARY,
    SKILL_TASK_QUALITY,
    SKILL_SPRINT_HEALTH,
    SKILL_VELOCITY,
    SKILL_TEAM_WORKLOAD,
    SKILL_COMPETENCY_MATCH,
    SKILL_RELEASE_HEALTH,
    SKILL_HELP,
]


def get_initial_skills() -> list:
    """Get list of all initial skill definitions.

    Returns:
        List of SkillDefinition
    """
    return INITIAL_SKILLS


def get_skill_by_id(skill_id: str) -> SkillDefinition:
    """Get skill definition by ID.

    Args:
        skill_id: Skill ID

    Returns:
        Skill definition

    Raises:
        ValueError: If skill not found
    """
    for skill in INITIAL_SKILLS:
        if skill.skill_id == skill_id:
            return skill
    raise ValueError(f"Skill not found: {skill_id}")


# Export for convenience
__all__ = [
    "SKILL_TASK_SEARCH",
    "SKILL_TASK_SUMMARY",
    "SKILL_TASK_QUALITY",
    "SKILL_SPRINT_HEALTH",
    "SKILL_VELOCITY",
    "SKILL_TEAM_WORKLOAD",
    "SKILL_COMPETENCY_MATCH",
    "SKILL_RELEASE_HEALTH",
    "SKILL_HELP",
    "INITIAL_SKILLS",
    "get_initial_skills",
    "get_skill_by_id",
]
