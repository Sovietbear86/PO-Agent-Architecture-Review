"""Генератор отчетов команды"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from s21_team_performance.config import (
    TEAM_MEMBERS_FILE,
    TEAM_KNOWLEDGE_DIR,
    KNOWLEDGE_DIR
)
from s21_team_performance.models import TeamMember, AnalysisResult


class TeamReportGenerator:
    """Генератор отчетов для команды"""
    
    def __init__(self):
        self.team_members: List[TeamMember] = []
        self.knowledge_files: Dict[str, str] = {}
        
    def load_team_members(self) -> List[TeamMember]:
        """Загрузить данные о командах из team_members.yaml"""
        import yaml
        
        if not TEAM_MEMBERS_FILE.exists():
            return []
            
        with open(TEAM_MEMBERS_FILE, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        members = data.get('members', [])
        self.team_members = [TeamMember(**m) for m in members]
        return self.team_members
    
    def load_knowledge_files(self) -> Dict[str, str]:
        """Загрузить файлы базы знаний"""
        # Загрузить team.md
        team_md_file = TEAM_KNOWLEDGE_DIR / "team.md"
        if team_md_file.exists():
            with open(team_md_file, 'r', encoding='utf-8') as f:
                self.knowledge_files['team'] = f.read()
        
        # Загрузить achievements.md
        achievements_md_file = TEAM_KNOWLEDGE_DIR / "achievements.md"
        if achievements_md_file.exists():
            with open(achievements_md_file, 'r', encoding='utf-8') as f:
                self.knowledge_files['achievements'] = f.read()
        
        # Загрузить competencies.md
        competencies_md_file = TEAM_KNOWLEDGE_DIR / "competencies.md"
        if competencies_md_file.exists():
            with open(competencies_md_file, 'r', encoding='utf-8') as f:
                self.knowledge_files['competencies'] = f.read()
        
        # Загрузить responsibilities.md
        responsibilities_md_file = TEAM_KNOWLEDGE_DIR / "responsibilities.md"
        if responsibilities_md_file.exists():
            with open(responsibilities_md_file, 'r', encoding='utf-8') as f:
                self.knowledge_files['responsibilities'] = f.read()
        
        return self.knowledge_files
    
    def generate_summary_report(self) -> str:
        """Сгенерировать краткий отчет о команде"""
        if not self.team_members:
            self.load_team_members()
        
        report_lines = [
            "# Отчет о составе команды",
            "",
            f"**Всего участников:** {len(self.team_members)}",
            "",
        ]
        
        # Группировка по продуктам
        products = set()
        for member in self.team_members:
            products.update(member.products)
        
        for product in sorted(products):
            product_members = [m for m in self.team_members if product in m.products]
            report_lines.extend([
                f"## {product}",
                "",
                "| ФИО | Роль | Email | Login |",
                "|-----|------|-------|-------|",
            ])
            for member in product_members:
                report_lines.append(
                    f"| {member.full_name} | {member.team_role} | {member.email} | {member.login} |"
                )
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    def generate_member_profile(self, login: str) -> Optional[str]:
        """Сгенерировать профиль сотрудника"""
        member = next((m for m in self.team_members if m.login == login), None)
        if not member:
            return None
        
        lines = [
            f"# {member.full_name}",
            "",
            "## Идентификация",
            f"- **Email:** {member.email}",
            f"- **Login AS21:** {member.login}",
            f"- **Роль в команде:** {member.team_role}",
            f"- **Профессиональный профиль:** {member.professional_profile}",
            f"- **Грейд:** {member.grade or 'не указан'}",
            f"- **Продукты:** {', '.join(member.products)}",
            "",
        ]
        
        # Зоны ответственности
        responsibilities = []
        if member.team_role in ['Владелец продукта', 'Лидер продукта']:
            responsibilities.append("Управление продуктовым направлением")
        responsibilities.append(f"Работа с продуктом: {', '.join(member.products)}")
        
        lines.extend(["## Зоны ответственности", ""] + [f"- {r}" for r in responsibilities] + [""])
        
        return "\n".join(lines)
    
    def analyze_member_by_knowledge(self, login: str) -> Dict[str, Any]:
        """Анализ сотрудника по базе знаний"""
        result = {
            "login": login,
            "found": False,
            "evidence": [],
            "achievements": [],
            "competencies": [],
            "warnings": []
        }
        
        # Попытаться найти в базе знаний
        employee_file = Path(KNOWLEDGE_DIR) / "employees" / f"{login.replace('.', '_')}.md"
        if not employee_file.exists():
            # Попробовать с точкой
            employee_file = Path(KNOWLEDGE_DIR) / "employees" / f"{login}.md"
        
        if not employee_file.exists():
            result["warnings"].append(f"Профиль не найден: {login}")
            return result
        
        result["found"] = True
        
        with open(employee_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Извлечь evidence-based компетенции
        if "Evidence-based компетенции" in content:
            lines = content.split("\n")
            in_competencies = False
            for line in lines:
                if "Evidence-based компетенции" in line:
                    in_competencies = True
                    continue
                if in_competencies and line.strip().startswith("- "):
                    competencies.append(line.strip()[2:])
        
        # Извлечь достижения
        if "Достижения" in content:
            lines = content.split("\n")
            in_achievements = False
            for line in lines:
                if "Достижения" in line:
                    in_achievements = True
                    continue
                if in_achievements and line.strip().startswith("1)"):
                    achievements.append(line.strip()[2:])
        
        result["competencies"] = competencies
        result["achievements"] = achievements
        
        return result
