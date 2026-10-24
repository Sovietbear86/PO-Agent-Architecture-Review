"""Скилл: Competency Matching - Сопоставление компетенций"""

from typing import List, Dict, Any

from s21_team_performance.models import AnalysisResult, CompetencyMatchResult


class CompetencyMatchingSkill:
    """Сопоставляет требования задачи с компетенциями сотрудников"""
    
    def __init__(self):
        self.findings: List[str] = []
        self.risks: List[str] = []
        self.recommendations: List[str] = []
        self.sources: List[str] = []
        self.constraints: List[str] = []
        
    async def analyze(
        self,
        task_requirements: Dict[str, int],
        exclude_members: List[str] = None,
        max_candidates: int = 3
    ) -> AnalysisResult:
        """Сопоставить компетенции с требованиями задачи"""
        
        if not task_requirements:
            return AnalysisResult(
                status="red",
                findings=["Не указаны требования к задаче"],
                risks=["Нет данных о требуемых компетенциях"],
                recommendations=["Указать task_requirements в запросе"],
                sources=[],
                constraints=["Требуются требования к задаче"],
                confidence=0.2,
                team_members=[],
                products=[]
            )
        
        # Получить данные о сотрудниках
        team_members = await self._fetch_team_members()
        
        # Получить текущий WIP для каждого сотрудника
        current_wip = await self._fetch_current_wip()
        
        # Сопоставить компетенции
        candidates = []
        for member in team_members:
            if member.login in (exclude_members or []):
                continue
            
            # Вычислить совпадение компетенций
            matched_competencies = {}
            for req_comp, req_level in task_requirements.items():
                member_level = member.competencies.get(req_comp, 0)
                if member_level >= req_level:
                    matched_competencies[req_comp] = member_level
            
            if not matched_competencies:
                continue  # Не подходит по компетенциям
            
            # Вычислить score (упрощенно)
            score = sum(matched_competencies.values()) / (len(matched_competencies) * 5)
            allocation = member.allocation_percent / 100 if member.allocation_percent else 1.0
            max_wip = member.recommended_max_wip or 3
            current = current_wip.get(member.login, 0)
            load_factor = max(0, 1 - current / max_wip)
            
            final_score = 0.7 * score + 0.2 * allocation + 0.1 * load_factor
            
            candidates.append(CompetencyMatchResult(
                member_id=member.id,
                member_name=member.full_name,
                score=round(final_score, 3),
                competencies=matched_competencies,
                current_wip=current,
                allocation=allocation,
                warning="WIP limit reached" if current >= max_wip else None,
                recommendation="Рекомендуется" if final_score >= 0.7 else "Можно рассмотреть"
            ))
        
        # Сортировать по score
        candidates.sort(key=lambda x: x.score, reverse=True)
        top_candidates = candidates[:max_candidates]
        
        if not top_candidates:
            return AnalysisResult(
                status="yellow",
                findings=["Нет сотрудников, подходящих по компетенциям"],
                risks=["Требования к задаче высокие или команда не специализируется на этом направлении"],
                recommendations=["Рассмотреть расширение состава или переобучение"],
                sources=[],
                constraints=["Данные о компетенциях могут быть неполными"],
                confidence=0.5,
                team_members=[],
                products=[]
            )
        
        # Определить статус
        if top_candidates[0].score >= 0.7:
            status = "green"
        elif top_candidates[0].score >= 0.5:
            status = "yellow"
        else:
            status = "red"
        
        # Сформировать вывод
        self.findings = [
            f"Требуемые компетенции: {', '.join(task_requirements.keys())}",
            f"Найдено подходящих кандидатов: {len(candidates)}",
            f"Топ-кандидаты (сверху вниз):",
        ]
        
        for i, candidate in enumerate(top_candidates, 1):
            self.findings.append(
                f"{i}. {candidate.member_name} ({candidate.member_id}): score={candidate.score:.2f}, "
                f"WIP={candidate.current_wip}, competencies={', '.join(candidate.competencies.keys())}"
            )
        
        # Риски
        if top_candidates[0].warning:
            self.risks.append(f"{top_candidates[0].member_name}: {top_candidates[0].warning}")
        
        # Рекомендации
        self.recommendations = [
            f"Рекомендуется назначить: {top_candidates[0].member_name}",
        ]
        
        if len(top_candidates) > 1:
            self.recommendations.append(f"Backup: {top_candidates[1].member_name}")
        
        self.recommendations.extend([
            "Уточнить детали задачи для более точного подбора",
            "Учесть плановые отсутствия",
        ])
        
        self.sources = [
            "config/team_members.yaml",
            "knowledge/employees/*.md",
        ]
        
        self.constraints = [
            "Уровни компетенций требуют ручного подтверждения",
            "Данные о текущем WIP могут быть недостаточно точными",
            "Рекомендация не является автоматическим назначением",
        ]
        
        return AnalysisResult(
            status=status,
            findings=self.findings,
            risks=self.risks,
            recommendations=self.recommendations,
            sources=self.sources,
            constraints=self.constraints,
            confidence=0.7,
            team_members=[c.member_id for c in top_candidates],
            products=[]
        )
    
    async def _fetch_team_members(self) -> List[Any]:
        """Получить данные о сотрудниках (заглушка)"""
        from s21_team_performance.models import TeamMember
        
        return [
            TeamMember(
                id="Kalachanov.V.V",
                full_name="Калачанов Виктор Вячеславович",
                login="Kalachanov.V.V",
                email="Kalachanov.V.V@sbertech.ru",
                products=["OLAP", "DTMS"],
                team_role="Владелец продукта",
                professional_profile="Владелец продуктов OLAP Analytics и DataMarts",
                grade=13,
                competencies={"olap": 4, "datamarts": 4, "architecture": 3},
                allocation_percent=100,
                recommended_max_wip=3,
            ),
            TeamMember(
                id="Garanin.R.V",
                full_name="Гаранин Родион Владимирович",
                login="Garanin.R.V",
                email="Garanin.R.V@sbertech.ru",
                products=["OLAP", "DTMS"],
                team_role="Лидер продукта",
                professional_profile="Технический лидер / ведущий Java-разработчик",
                grade=13,
                competencies={"java": 5, "go": 3, "cpp": 4, "architecture": 4},
                allocation_percent=100,
                recommended_max_wip=3,
            ),
            TeamMember(
                id="Goncharov.A.O",
                full_name="Гончаров Александр Олегович",
                login="Goncharov.A.O",
                email="Goncharov.A.O@sbertech.ru",
                products=["OLAP"],
                team_role="Участник команды",
                professional_profile="Java-разработчик",
                grade=11,
                competencies={"java": 4, "olap": 2},
                allocation_percent=100,
                recommended_max_wip=3,
            ),
        ]
    
    async def _fetch_current_wip(self) -> Dict[str, int]:
        """Получить текущий WIP по сотрудникам (заглушка)"""
        return {
            "Kalachanov.V.V": 2,
            "Garanin.R.V": 3,
            "Goncharov.A.O": 1,
        }
