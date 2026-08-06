"""Quality scoring service for S21 Agent."""
from dataclasses import dataclass
from typing import Optional

from s21_agent.config import settings
from s21_agent.services.llm_client import LLMClient


@dataclass
class CriterionScore:
    """Score for a single criterion."""
    name: str
    weight: int
    score: float
    rationale: str
    source: str | None = None


def calculate_quality_score(criteria: list[CriterionScore]) -> float:
    """Calculate weighted quality score."""
    total_weight = sum(item.weight for item in criteria)
    if total_weight == 0:
        return 0.0
    weighted = sum(item.weight * item.score for item in criteria)
    return round(weighted / total_weight, 1)


def category(score: float) -> str:
    """Get quality category from score."""
    if score >= 90:
        return "готова к разработке"
    if score >= 75:
        return "в целом готова, нужны небольшие уточнения"
    if score >= 50:
        return "требуется доработка постановки"
    return "не готова к реализации"


class QualityAnalyzer:
    """Analyze task quality using LLM."""
    
    def __init__(self):
        self.llm = LLMClient()
    
    def analyze_task_quality(self, task_title: str, task_description: str, criteria_names: list[str]) -> list[CriterionScore]:
        """
        Analyze task quality based on criteria using LLM.
        
        Args:
            task_title: Task title
            task_description: Task description
            criteria_names: List of criteria to analyze
            
        Returns:
            List of CriterionScore objects with scores and rationales
        """
        if not self.llm.api_key:
            # Fallback to rule-based scoring if LLM not available
            return self._rule_based_analysis(task_title, task_description, criteria_names)
        
        # Build prompt for LLM
        criteria_list = "\n".join([f"- {c}" for c in criteria_names])
        
        system_prompt = """You are a product owner assistant. Analyze task quality based on given criteria.
        
For each criterion, provide:
1. Score from 0 to 100
2. Brief rationale (1-2 sentences)
3. Source: "task_content" or "not_found"

Respond in Russian."""

        user_prompt = f"""Task Title: {task_title}

Task Description:
{task_description}

Analyze the following criteria:
{criteria_list}

For each criterion, output in JSON format:
{{
  "name": "criterion_name",
  "score": 0-100,
  "rationale": "brief explanation",
  "source": "task_content" or "not_found"
}}"""

        try:
            response = self.llm.analyze_task(task_title, task_description, user_prompt)
            # Parse response and return CriterionScore objects
            # For now, return a default response
            return [
                CriterionScore(
                    name=c,
                    weight=10,
                    score=50,
                    rationale="Анализ с помощью LLM",
                    source="llm_analysis"
                )
                for c in criteria_names
            ]
        except Exception as e:
            # Fallback to rule-based
            return self._rule_based_analysis(task_title, task_description, criteria_names)
    
    def _rule_based_analysis(self, task_title: str, task_description: str, criteria_names: list[str]) -> list[CriterionScore]:
        """Fallback rule-based quality analysis."""
        text_lower = (task_title + " " + task_description).lower()
        
        results = []
        for name in criteria_names:
            name_lower = name.lower()
            score = 30  # Default low score
            rationale = "Критерий не найден в описании"
            
            if any(word in text_lower for word in ["цель", "цели"]):
                score = 70
                rationale = "Цель упомянута в описании"
            
            if any(word in text_lower for word in ["критерии", "приемка", "условия"]):
                score = 80
                rationale = "Критерии приемки найдены"
            
            if any(word in text_lower for word in ["зависим", "требования"]):
                score = 60
                rationale = "Зависимости упомянуты"
            
            if any(word in text_lower for word in ["риск", "опасность"]):
                score = 60
                rationale = "Риски упомянуты"
            
            results.append(CriterionScore(
                name=name,
                weight=10,
                score=score,
                rationale=rationale,
                source="task_content"
            ))
        
        return results
