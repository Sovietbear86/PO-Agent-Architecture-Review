"""Main Team Performance Agent с маршрутизацией"""

from typing import Dict, Any, Optional
from pathlib import Path

from .config import TEAM_MEMBERS_FILE, WorkflowStatusConfig
from .models import (
    TeamAnalysisRequest,
    AnalysisResult,
    TeamMember
)
from .skills.sprint_health import SprintHealthSkill
from .skills.velocity_analysis import VelocityAnalysisSkill
from .skills.flow_metrics import FlowMetricsSkill
from .skills.workload_balance import WorkloadBalanceSkill
from .skills.competency_matching import CompetencyMatchingSkill
from .skills.bottleneck_analysis import BottleneckAnalysisSkill
from .skills.forecasting import ForecastingSkill
from .skills.release_linkage import ReleaseLinkageSkill
from .skills.member_load_analysis import MemberLoadAnalysisSkill
from .skills.risk_analysis import RiskAnalysisSkill


class LLMAgent:
    """LLM-based query analyzer and response generator using SBT Hub AI API."""

    def __init__(self):
        from s21_agent.config import settings
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model or "Qwen/Qwen3-Coder-Next"
        self.timeout = settings.openai_timeout_seconds
        self.base_url = settings.openai_base_url or "https://api.ai.sbt/openai/v1"

    def generate_response(self, query: str, context: Dict[str, Any]) -> str:
        """Generate natural language response based on query and analysis context."""
        import httpx
        import json

        system_prompt = """You are a helpful product owner assistant for SberWorks Task Tracker (SWTR).

You analyze team performance metrics and task data from SWTR.

## Important: For member load analysis and risk analysis, do NOT list individual tasks.
Only provide summary metrics and recommendations for the specified team member.

## Supported Skills (Ключевые слова для запросов):

### 1. Здоровье спринта (sprint_health)
- "здоровье спринта OLP-SPRNT-3"
- " метрики спринта DMS-SPRNT-1"
- "OLP-SPRNT-2"

### 2. Velocity (velocity_analysis)
- "скорость команды"
- "velocity за последние 6 спринтов"
- "производительность команды"

### 3. Flow Metrics (flow_metrics)
- "поток задач за 30 дней"
- "flow metrics последний месяц"
- "throughput за период"

### 4. Баланс загрузки (workload_balance)
- "баланс загрузки команды"
- "загрузка сотрудников"
- "распределение задач"

### 5. Узкие места (bottleneck_analysis)
- "бутылочное горлышко"
- "узкие места в спринте"
- "проблемы с потоком"

### 6. Прогноз (forecasting)
- "прогноз завершения спринта"
- "когда закончится спринт"
- "прогноз выполнения"

### 7. Компетенции (competency_matching)
- "кто подходит для задачи"
- "подбор по компетенциям"
- "кто может взять задачу"

### 8. Релизы (release_linkage)
- "релизные задачи"
- "задачи релиза OLAP"
- "привязка к релизу"

## Rules:
1. Use the context data to provide specific answers
2. If data is unavailable, say so clearly
3. Keep answers concise but complete
4. Use bullet points for lists
5. Be friendly and professional
6. Always respond in Russian
7. Include relevant metrics from analysis results"""

        # Build context for prompt
        context_str = json.dumps(context, ensure_ascii=False, indent=2)

        user_prompt = f"""User Query: "{query}"

Analysis Results:
{context_str}

Please generate a helpful response in Russian that directly answers the user's question using the analysis results above."""

        # Try SBT Hub AI API
        if self.api_key:
            try:
                with httpx.Client(timeout=self.timeout, verify=False) as client:
                    response = client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt},
                            ],
                            "temperature": 0.5,
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
            except httpx.HTTPError as e:
                print(f"LLM API error: {e}")

        # Fallback to template-based response
        return self._fallback_response(query, context)

    def _fallback_response(self, query: str, context: Dict[str, Any]) -> str:
        """Fallback template-based response generation."""
        findings = context.get("findings", [])
        risks = context.get("risks", [])
        recommendations = context.get("recommendations", [])

        if not findings:
            return "Я не смог получить данные для анализа. Попробуйте уточнить запрос."

        # Generate summary from findings
        summary = "Анализ показал следующее:\n"
        for i, finding in enumerate(findings[:5], 1):
            summary += f"{i}. {finding}\n"

        if risks:
            summary += "\nРиски:\n"
            for i, risk in enumerate(risks[:3], 1):
                summary += f"{i}. {risk}\n"

        if recommendations:
            summary += "\nРекомендации:\n"
            for i, rec in enumerate(recommendations[:3], 1):
                summary += f"{i}. {rec}\n"

        return summary


class TeamPerformanceAgent:
    """Главный агент для анализа команды"""

    def __init__(self):
        self.skills: Dict[str, Any] = {}
        self.team_members: list[TeamMember] = []
        self.llm: Optional[LLMAgent] = None
        self._load_skills()
        self.load_team_members()
        # Context storage for multi-step interactions
        self.context: Dict[str, Any] = {}

    def _load_skills(self) -> None:
        """Загрузить все скиллы"""
        from .skills.sprint_health import SprintHealthSkill
        
        self.skills = {
            "get_tasks": SprintHealthSkill(),
            "sprint_health": SprintHealthSkill(),
            "velocity_analysis": VelocityAnalysisSkill(),
            "flow_metrics": FlowMetricsSkill(),
            "workload_balance": WorkloadBalanceSkill(),
            "competency_matching": CompetencyMatchingSkill(),
            "bottleneck_analysis": BottleneckAnalysisSkill(),
            "forecasting": ForecastingSkill(),
            "release_linkage": ReleaseLinkageSkill(),
            "member_load_analysis": MemberLoadAnalysisSkill(),
            "risk_analysis": RiskAnalysisSkill(),
            "help": SprintHealthSkill(),  # Reuse SprintHealthSkill for help (returns static help text)
        }

    def load_team_members(self) -> list[TeamMember]:
        """Загрузить данные о командах"""
        import yaml

        if not TEAM_MEMBERS_FILE.exists():
            return []

        with open(TEAM_MEMBERS_FILE, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        members = data.get('members', [])
        self.team_members = [TeamMember(**m) for m in members]
        return self.team_members

    def get_llm(self) -> Optional[LLMAgent]:
        """Get LLM agent instance (singleton)"""
        if self.llm is None:
            self.llm = LLMAgent()
        return self.llm
    
    def determine_skill(self, query: str) -> Optional[str]:
        """Определить какой скилл вызвать по запросу пользователя.

        Priority order:
        1. Sprint selection (DMS-SPRNT-1) -> get_tasks
        2. Team performance queries with specific keywords -> specific skills (with LLM)
        3. Simple task search patterns -> get_tasks (no LLM)
        4. Help queries

        Returns None if query doesn't match any known pattern.
        """
        import re

        query_lower = query.lower()

        # Priority 1: Check for sprint selection (e.g., "DMS-SPRNT-1", "STS-SPRNT-1")
        # This has highest priority and uses get_tasks skill
        sprint_select_match = re.match(r'^(DMS|OLP|WMB|STS)-SPRNT-\d+$', query.strip(), re.IGNORECASE)
        if sprint_select_match:
            return "get_tasks"

        # Priority 2: Specific team performance queries (order matters - specific first)
        # These should be checked BEFORE simple task patterns to avoid false positives
        if "насколько загружен" in query_lower or "насколько загружена" in query_lower:
            return "member_load_analysis"
        if "средняя трудоемкость" in query_lower or "трудоемкость задач" in query_lower:
            return "member_load_analysis"
        if "загружен" in query_lower or "загрузка" in query_lower:
            # Check if it's workload_balance (general team) vs member_load_analysis (specific person)
            if "загрузка" in query_lower and ("команды" in query_lower or "сотрудники" in query_lower):
                return "workload_balance"
            return "member_load_analysis"
        if "риски" in query_lower or "под риском" in query_lower or "не успеет" in query_lower:
            return "risk_analysis"
        if "скорость" in query_lower or "velocity" in query_lower or "производительность" in query_lower:
            return "velocity_analysis"
        if "поток" in query_lower or "flow" in query_lower:
            return "flow_metrics"
        if "баланс" in query_lower:
            return "workload_balance"
        if "бутылочное" in query_lower or "узкое" in query_lower:
            return "bottleneck_analysis"
        if "прогноз" in query_lower or "дата" in query_lower:
            return "forecasting"
        if "релиз" in query_lower or "выпуск" in query_lower:
            return "release_linkage"
        if "здоровье спринта" in query_lower:
            return "sprint_health"

        # Priority 3: Simple task search patterns (NO LLM needed)
        # These should use get_tasks skill without LLM analysis

        # Check for simple patterns: member name + "из спринта" + sprint ID
        # (e.g., "задачи моисеева из спринта DMS-SPRNT-1")
        simple_task_keywords = ['из спринта', 'в спринте']
        has_sprint_keyword = any(kw in query_lower for kw in simple_task_keywords)
        has_member = len(self.extract_team_members_from_query(query)) > 0

        # Check for sprint ID pattern (case-insensitive)
        sprint_pattern = r'(dms|olp|wmb|sts)-sprnt-\d+'
        has_sprint_id = re.search(sprint_pattern, query_lower) is not None

        # Check for NONE as sprint_id
        has_none_sprint = 'none' in query_lower and has_sprint_keyword

        if has_sprint_keyword and has_member and (has_sprint_id or has_none_sprint):
            return "get_tasks"

        # Priority 3.5: Member task search WITHOUT sprint (return sprint list)
        # (e.g., "задачи Гаранина", "задачи моисеева")
        # If query contains member name but NO sprint keyword, return get_tasks with empty sprint_id
        # This allows get_tasks() to return list of available sprints for user to choose
        if has_member and not has_sprint_keyword:
            return "get_tasks"

        # Priority 4: Help/what can you do queries
        if "что ты умеешь" in query_lower or "какие скиллы" in query_lower or "типы запросов" in query_lower or "привет" in query_lower or "помощь" in query_lower:
            return "help"

        # Unknown query - return None to trigger helpful error message
        return None

    def extract_team_members_from_query(self, query: str) -> list[str]:
        """Извлечь имена участников команды из запроса"""
        query_lower = query.lower()
        result = []

        for member in self.team_members:
            # Try to determine surname position
            # First, check if full name contains query (e.g., "Гаранина" in "Гаранин Родион Владимирович")
            full_name_lower = member.full_name.lower()
            if full_name_lower in query_lower:
                if member.login not in result:
                    result.append(member.login)
                continue
            
            # Try login-based matching
            login_prefix = member.login.split('.')[0].lower() if '.' in member.login else member.login.lower()
            if login_prefix in query_lower:
                if member.login not in result:
                    result.append(member.login)
                continue
            
            # If login prefix contains only latin letters and last_name contains cyrillic,
            # use last_name as surname (handles cases like "reshetnik" -> "решетник")
            full_name_parts = member.full_name.split()
            last_name = full_name_parts[-1].lower() if full_name_parts else ''

            # Check if login is transliterated and last_name is cyrillic
            is_transliterated = login_prefix.isascii() and not login_prefix.isdigit()
            is_cyrillic = any('\u0400' <= c <= '\u04FF' for c in last_name)

            if is_transliterated and is_cyrillic:
                # Use last_name (cyrillic) as surname only if it looks like a surname
                # A surname in cyrillic typically ends with specific patterns
                # "решетник", "гончаров", "жданов" - these are surnames
                # "владимирович", "Николаевич" - these are patronymics
                # Check if last_name ends with typical surname suffixes (exclude patronymic suffixes)
                patronymic_suffixes = ['ич', 'на', 'евич', 'овна', 'евна', 'ична']
                if any(last_name.endswith(suffix) for suffix in patronymic_suffixes):
                    # This is a patronymic, use first name as surname
                    surname = full_name_parts[0].lower() if full_name_parts else ''
                else:
                    # Surname suffixes for Slavic names
                    # Include both common endings and specific patterns
                    surname_suffixes = [
                        'ов', 'ев', 'ин', 'ын', 'ий', 'й', 'ск', 'ц', 'ч', 'ш', 'щ', 'а', 'я', 'ый', 'ой',
                        'ник', 'чук', 'юк', 'ук', 'ек', 'ок', 'ак', 'як', 'ец', 'иц', 'уц', 'ыц',
                        'ко', 'еко', 'енко', 'енко', 'ян', 'ян', 'овicz', 'owicz', 'wicz'
                    ]
                    if any(last_name.endswith(suffix) for suffix in surname_suffixes):
                        surname = last_name
                    else:
                        # Unknown pattern, use first name as surname
                        surname = full_name_parts[0].lower() if full_name_parts else ''
            elif login_prefix == last_name or login_prefix in last_name or last_name in login_prefix:
                surname = last_name
            else:
                surname = full_name_parts[0].lower() if full_name_parts else ''

            # If we have a surname, try to match it
            if surname:
                # Try to match surname without common endings
                base_name = surname.rstrip('а')  # "решетник" -> "решетник"
                # Also strip 'ой' ending (e.g., "долговской" -> "долговск")
                if surname.endswith('ой'):
                    base_name = surname[:-2]
                if base_name in query_lower or surname in query_lower:
                    if member.login not in result:
                        result.append(member.login)
                    continue

        return result

    def _has_member_mention(self, query: str) -> bool:
        """Проверить, содержит ли запрос упоминание участника команды.
        
        Ищет паттерны вида "задачи Иванова", "Иванову", "Иванов" (в контексте задач).
        """
        import re
        
        query_lower = query.lower()
        
        # Паттерны для упоминания участника
        patterns = [
            r'задачи\s+\w+',           # "задачи Иванова"
            r'задачи\s+\w+\s+из',      # "задачи Иванова из"
            r'задачи\s+\w+\s+в\s+спринте',  # "задачи Иванова в спринте"
            r'\w+у\s+задачи',          # "Иванову задачи"
            r'кто\s+\w+',              # "кто Гаранин"
            r'кто\s+\w+\s+работает',   # "кто Гаранин работает"
        ]
        
        for pattern in patterns:
            if re.search(pattern, query_lower):
                return True
        
        return False

    async def analyze(self, request: TeamAnalysisRequest) -> AnalysisResult:
        """Анализ команды с использованием соответствующего скилла"""
        
        skill_name = request.skill
        params = request.params
        
        if skill_name not in self.skills:
            return AnalysisResult(
                status="red",
                findings=[f"Неизвестный скилл: {skill_name}"],
                risks=["Выберите один из доступных скиллов"],
                recommendations=list(self.skills.keys()),
                sources=[],
                constraints=["Проверьте название скилла"],
                confidence=0.0,
                team_members=[],
                products=[]
            )

        import logging
        logger = logging.getLogger(__name__)

        skill = self.skills[skill_name]

        # Вызвать соответствующий метод в зависимости от скилла
        if skill_name == "get_tasks":
            logger.info(f"[get_tasks] Calling skill.get_tasks() with sprint_id={params.get('sprint_id')}, team_members={params.get('team_members')}")
            result_data = skill.get_tasks(
                query=params.get('query', ''),
                team_members=params.get('team_members', []),
                products=params.get('products', []),
                sprint_id=params.get('sprint_id'),
                status_filter=params.get('status_filter'),
                params=params
            )
            logger.info(f"[get_tasks] result_data keys: {result_data.keys()}, sprints={len(result_data.get('sprints', []))}, tasks={len(result_data.get('tasks', []))}")

            # Check if result contains sprints list (no sprint_id specified)
            # Also check if there are actual tasks to return
            sprints = result_data.get('sprints', [])
            tasks = result_data.get('tasks', [])
            needs_sprint = result_data.get('needs_sprint_selection', False)
            sprint_id = params.get('sprint_id')

            # Debug logging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[analyze] sprint_id={sprint_id}, needs_sprint={needs_sprint}, sprints={len(sprints)}, tasks={len(tasks)}")

            # If no sprint_id and needs_sprint_selection, get sprint list from get_sprint_list
            if needs_sprint and not sprint_id and not sprints:
                # Call get_sprint_list to get available sprints for user to choose from
                products_list = params.get('products', [])
                sprints = self.skills['get_tasks'].get_sprint_list(
                    products_list[0] if products_list else "WMB"
                ).get('sprints', [])
                logger.info(f"[analyze] After get_sprint_list: sprints={len(sprints)}")

            # If no sprint_id, return list of sprints for user to choose from
            if (sprints and not tasks) or (needs_sprint and not sprint_id):
                findings = [
                    f"Доступные спринты ({len(sprints)}):",
                    *[f"- {s['id']}: {s['name']} (space: {s['space']})" for s in sprints[:5]]
                ]
                if len(sprints) > 5:
                    findings.append(f"... и еще {len(sprints) - 5} спринтов")
                findings.append("Пожалуйста, укажите ID спринта (например, DMS-SPRNT-1), чтобы показать задачи")

                # Store pending sprint context for multi-step interaction
                self.context["pending_sprint"] = {
                    "team_members": params.get('team_members', []),
                    "products": params.get('products', [])
                }
                
                # Also save to file for FastAPI compatibility
                import os, json
                context_file = os.path.expanduser('~/.task-tracker/pending_sprint.json')
                try:
                    with open(context_file, 'w') as f:
                        json.dump({"team_members": params.get('team_members', []), "products": params.get('products', [])}, f)
                except:
                    pass

                return AnalysisResult(
                    status="yellow",
                    findings=findings,
                    risks=["Не указан ID спринта"],
                    recommendations=["Укажите ID спринта в запросе"],
                    sources=[],
                    constraints=["Необходимо указать sprint_id"],
                    confidence=0.5,
                    team_members=params.get('team_members', []),
                    products=params.get('products', []),
                    sprints=sprints,
                    default_sprint=result_data.get('default', sprints[0]['id'] if sprints else ""),
                    sprint_id=None
                )

            return AnalysisResult(
                status="green",
                findings=[f"Найдено {result_data['count']} задач"],
                risks=[],
                recommendations=["Выберите спринт из списка, чтобы увидеть задачи"],
                sources=[],
                constraints=[],
                confidence=0.8,
                team_members=params.get('team_members', []),
                products=params.get('products', []),
                sprints=[],
                default_sprint="",
                sprint_id=result_data.get('sprint_id'),
                tasks=result_data.get('tasks', [])
            )
        elif skill_name == "help":
            return AnalysisResult(
                status="info",
                findings=[
                    "Я - ассистент продукт-овладельца для анализа команды в SberWorks Task Tracker.",
                    "",
                    "### Доступные скиллы:",
                    "1. **Здоровье спринта** - метрики спринта: Committed scope, Completed scope, Throughput",
                    "   Пример: 'здоровье спринта OLP-SPRNT-3'",
                    "",
                    "2. **Velocity** - скорость команды за период",
                    "   Пример: 'скорость команды' или 'velocity за последние 6 спринтов'",
                    "",
                    "3. **Flow metrics** - метрики потока: Throughput, Cycle time, Lead time",
                    "   Пример: 'поток задач за 30 дней'",
                    "",
                    "4. **Баланс загрузки** - распределение задач между сотрудниками",
                    "   Пример: 'баланс загрузки команды'",
                    "",
                    "5. **Узкие места** - анализ бутылочных горлышек в процессе",
                    "   Пример: 'бутылочное горлышко в спринте'",
                    "",
                    "6. **Прогноз** - прогноз завершения спринта",
                    "   Пример: 'прогноз завершения спринта'",
                    "",
                    "7. **Компетенции** - подбор сотрудников по компетенциям",
                    "   Пример: 'кто подходит для задачи'",
                    "",
                    "8. **Релизы** - задачи, привязанные к релизу",
                    "   Пример: 'релизные задачи OLAP'",
                    "",
                    "### Новые навыки для анализа сотрудников:",
                    "9. **Средняя трудоемкость** - анализ загрузки сотрудника в спринте",
                    "   Пример: 'средняя трудоемкость задач у Шалдунова'",
                    "   Пример: 'насколько загружен Гаранин?'",
                    "   Пример: 'насколько загружен Долговской в спринте OLP-SPRNT-5'",
                    "",
                    "10. **Риски невыполнения** - выявление задач под риском",
                    "    Пример: 'задачи под риском у Долговского'",
                    "    Пример: 'риски невыполнения в спринте OLP-SPRNT-5'",
                    "",
                    "Также я могу показать задачи по участнику или спринту.",
                    "Просто спросите: 'задачи Гаранина в спринте OLP-SPRNT-3'"
                ],
                risks=[],
                recommendations=["Выберите нужный скилл и задайте вопрос"],
                sources=[],
                constraints=[],
                confidence=1.0,
                team_members=[],
                products=[]
            )
        elif skill_name == "sprint_health":
            return await skill.analyze(
                sprint_id=params.get('sprint_id', ''),
                team_members=params.get('team_members', []),
                products=params.get('products', []),
                params=params
            )
        elif skill_name == "velocity_analysis":
            return await skill.analyze(
                period_sprints=params.get('period_sprints', 6),
                team_members=params.get('team_members') if 'team_members' in params else None,
                products=params.get('products', [])
            )
        elif skill_name == "flow_metrics":
            return await skill.analyze(
                period_days=params.get('period_days', 30),
                team_members=params.get('team_members') if 'team_members' in params else None,
                products=params.get('products', [])
            )
        elif skill_name == "workload_balance":
            return await skill.analyze(
                period_days=params.get('period_days', 30),
                team_members=params.get('team_members') if 'team_members' in params else None,
                products=params.get('products', [])
            )
        elif skill_name == "competency_matching":
            return await skill.analyze(
                task_requirements=params.get('task_requirements', {}),
                exclude_members=params.get('exclude_members', []),
                max_candidates=params.get('max_candidates', 3)
            )
        elif skill_name == "bottleneck_analysis":
            return await skill.analyze(
                period_days=params.get('period_days', 30),
                team_members=params.get('team_members') if 'team_members' in params else None,
                products=params.get('products', [])
            )
        elif skill_name == "forecasting":
            return await skill.analyze(
                sprint_id=params.get('sprint_id', ''),
                remaining_effort=params.get('remaining_effort', 0),
                team_members=params.get('team_members') if 'team_members' in params else None,
                products=params.get('products', [])
            )
        elif skill_name == "release_linkage":
            return await skill.analyze(
                release_id=params.get('release_id', ''),
                team_members=params.get('team_members') if 'team_members' in params else None,
                products=params.get('products', [])
            )
        elif skill_name == "member_load_analysis":
            return await skill.analyze(
                sprint_id=params.get('sprint_id', ''),
                team_members=params.get('team_members') if 'team_members' in params else None,
                products=params.get('products', [])
            )
        elif skill_name == "risk_analysis":
            return await skill.analyze(
                sprint_id=params.get('sprint_id', ''),
                team_members=params.get('team_members') if 'team_members' in params else None,
                products=params.get('products', [])
            )

        return AnalysisResult(
            status="red",
            findings=["Ошибка в маршрутизации"],
            risks=["Не удалось определить метод вызова"],
            recommendations=["Обратиться к разработчику"],
            sources=[],
            constraints=[],
            confidence=0.0,
            team_members=[],
            products=[]
        )
    
    async def analyze_by_query(self, query: str) -> AnalysisResult:
        """Анализ по запросу пользователя (автоматическое определение скилла)"""

        # Определить скилл по запросу
        skill_name = self.determine_skill(query)

        if not skill_name:
            # Build helpful error message with examples
            available_members = [m.full_name for m in self.team_members]
            
            # Generate member-specific examples
            member_examples = []
            for member in self.team_members[:3]:  # First 3 members
                member_name = member.full_name.split()[-1]  # Get surname
                member_examples.append(f"- Задачи {member_name} из спринта (покажу список спринтов)")
                member_examples.append(f"- Задачи {member_name} из спринта OLP-SPRNT-5 (покажу задачи)")
            
            # Generate skill examples
            skill_examples = [
                "### Скиллы для анализа:",
                "- 'здоровье спринта OLP-SPRNT-5' - метрики спринта",
                "- 'скорость команды' или 'velocity за последние 6 спринтов'",
                "- 'поток задач за 30 дней'",
                "- 'баланс загрузки команды'",
                "- 'бутылочное горлышко в спринте'",
                "- 'прогноз завершения спринта'",
                "- 'кто подходит для задачи'",
                "- 'релизные задачи OLAP'",
                "",
                "### Просто задачи:",
                "- 'задачи' (покажу список спринтов)",
                "- 'задачи Шалдунова' (покажу список спринтов)",
                "- 'задачи Шалдунова из спринта OLP-SPRNT-5' (покажу задачи)",
                "",
                "### Доступные участники:",
                f"- {', '.join(available_members[:5])}"
            ]
            
            return AnalysisResult(
                status="red",
                findings=[
                    "Я не понял ваш запрос.",
                    "",
                    "Я понимаю запросы вида:",
                    *member_examples,
                    "",
                    *skill_examples
                ],
                risks=["Не удалось определить тип запроса"],
                recommendations=["Попробуйте один из примеров выше"],
                sources=[],
                constraints=["Неизвестный запрос"],
                confidence=0.0,
                team_members=[],
                products=[]
            )

        # Извлечь имена участников из запроса
        team_members = self.extract_team_members_from_query(query)

        # Если не найдено участников, но запрос явно содержит упоминание участника
        if not team_members and self._has_member_mention(query):
            available_names = [m.full_name for m in self.team_members]
            return AnalysisResult(
                status="red",
                findings=[
                    "Не найден участник команды.",
                    f"Доступные участники: {', '.join(available_names)}"
                ],
                risks=["Проверьте имя участника"],
                recommendations=["Попробуйте сокращенную фамилию или login"],
                sources=[],
                constraints=["Участник не найден в team_members.yaml"],
                confidence=0.0,
                team_members=[],
                products=[]
            )

        # Извлечь статус из запроса (открытые, закрытые, в работе и т.д.)
        # Использовать WorkflowStatusConfig для нормализации статусов
        status_filter = None
        workflow_config = WorkflowStatusConfig()
        query_lower = query.lower()

        # First check for specific status after "в статусе" (before general patterns)
        if "в статусе" in query_lower:
            import re
            status_match = re.search(r'в статусе\s+(\w+)', query_lower)
            if status_match:
                status_name = status_match.group(1)
                # Нормализовать статус
                status_filter = [workflow_config.normalize_status(status_name)]
        # Сопоставление русских и английских ключевых слов с категориями статусов
        elif "открытые" in query_lower or "открыт" in query_lower or "open" in query_lower:
            # Open статусы (Backlog) + In progress + Review Queue + QA Queue
            status_filter = workflow_config.analytics.get("backlog_statuses", ["Open"]) + \
                           ["In progress", "Ready for review", "Ready for QA"]
        elif "закрытые" in query_lower or "closed" in query_lower or "done" in query_lower:
            # Закрытые и решенные
            status_filter = ["Closed", "Resolved"]
        elif "в работе" in query_lower or "в процессе" in query_lower or "в прогрессе" in query_lower:
            # Active Work
            status_filter = ["In progress", "Reopened"]
        elif "на тестировании" in query_lower or "тестируются" in query_lower or "testing" in query_lower:
            # QA
            status_filter = ["QA", "Ready for QA"]
        elif "на ревью" in query_lower or "ревью" in query_lower or "review" in query_lower:
            # Review
            status_filter = ["In review", "Ready for review"]
        elif "заблокированные" in query_lower or "blocked" in query_lower:
            # Waiting / Blocked
            status_filter = ["Need info"]
        elif "ожидание" in query_lower or "ожидающие" in query_lower:
            # Waiting / Blocked
            status_filter = ["Need info"]

        # Создать запрос и вызвать анализ
        params: Dict[str, Any] = {}
        if team_members:
            params["team_members"] = team_members
        if status_filter:
            params["status_filter"] = status_filter

        # Извлечь sprint_id из запроса для некоторых скиллов
        import re
        # Try to match sprint ID with or without spaces before/after it
        # Pattern for regular sprints: DMS-SPRNT-1, OLP-SPRNT-2, etc.
        # Pattern for NONE: "NONE" keyword after "в спринте" or "из спринта"
        sprint_match = re.search(r'(DMS|OLP|WMB|STS)-SPRNT-\d+', query, re.IGNORECASE)
        none_match = re.search(r'(в спринте|из спринта)\s+NONE', query, re.IGNORECASE)

        if sprint_match:
            sprint_id = sprint_match.group(0).upper()
            # Store sprint_id in params for skills that support it
            if skill_name in ["get_tasks", "sprint_health", "forecasting", "velocity_analysis",
                             "flow_metrics", "workload_balance", "bottleneck_analysis",
                             "member_load_analysis", "risk_analysis"]:
                params["sprint_id"] = sprint_id
            elif skill_name in ["competency_matching", "release_linkage"]:
                # These skills also need sprint_id for filtering
                params["sprint_id"] = sprint_id
        elif none_match:
            # User specified "NONE" as sprint_id
            if skill_name in ["get_tasks", "sprint_health", "forecasting", "velocity_analysis",
                             "flow_metrics", "workload_balance", "bottleneck_analysis",
                             "member_load_analysis", "risk_analysis",
                             "competency_matching", "release_linkage"]:
                params["sprint_id"] = "NONE"
        elif skill_name in ["get_tasks", "sprint_health"]:
            # Check if query mentions "в спринте" or "из спринта" without specific sprint
            if ("в спринте" in query.lower() or "из спринта" in query.lower()) and not sprint_match:
                # Don't know which sprint - let the skill handle it
                params["sprint_id"] = ""
            else:
                # No sprint mentioned - pass None to get all tasks
                params["sprint_id"] = None
        else:
            params["sprint_id"] = ""

        # Add query to params for get_tasks (needed for status filtering)
        if skill_name == "get_tasks":
            params["query"] = query

        # Check if query is a sprint selection (e.g., "DMS-SPRNT-1" or "OLP-SPRNT-2" or "NONE")
        import re
        sprint_select_match = re.match(r'^(DMS|OLP|WMB|STS)-SPRNT-\d+$', query.upper().strip())
        is_none_match = query.upper().strip() == "NONE"

        if (sprint_select_match or is_none_match) and "pending_sprint" in self.context:
            # User is selecting a sprint from the list
            if is_none_match:
                selected_sprint = "NONE"
            else:
                selected_sprint = sprint_select_match.group(0).upper()
            params["sprint_id"] = selected_sprint
            # Restore team_members from context
            if "team_members" in self.context["pending_sprint"]:
                params["team_members"] = self.context["pending_sprint"]["team_members"]
                print(f"DEBUG: Restored team_members: {params['team_members']}")
            # Clear pending sprint context
            if "pending_sprint" in self.context:
                del self.context["pending_sprint"]

        # Set skill-specific parameters
        if skill_name == "sprint_health":
            params.setdefault("period_days", 30)
        if skill_name == "velocity_analysis":
            params.setdefault("period_sprints", 6)
        if skill_name == "flow_metrics":
            params.setdefault("period_days", 30)
        if skill_name == "bottleneck_analysis":
            params.setdefault("period_days", 30)

        request = TeamAnalysisRequest(skill=skill_name, params=params)
        result = await self.analyze(request)

        # Check if LLM should be used for this query type
        # Only use LLM for analytical queries, not for simple task searches
        import re
        is_simple_task_request = (
            skill_name in ["get_tasks", "sprint_health", "help"]
            # get_tasks/sprint_health/help without sprint_id returns sprint list or help (no LLM needed)
            # get_tasks/sprint_health with sprint_id returns tasks (no LLM needed)
        )

        # Only generate LLM response for non-simple analytical requests
        # Simple task searches (get_tasks) don't need LLM
        if not is_simple_task_request:
            llm = self.get_llm()
            if llm and llm.api_key:
                try:
                    # For member_load_analysis and risk_analysis, don't pass tasks to LLM
                    result_data = result.model_dump()
                    if skill_name in ["member_load_analysis", "risk_analysis"]:
                        result_data["tasks"] = []
                    response = llm.generate_response(query, result_data)
                    result.findings.insert(0, f"LLM Response: {response}")
                except Exception as e:
                    print(f"LLM generation failed: {e}")

        return result
