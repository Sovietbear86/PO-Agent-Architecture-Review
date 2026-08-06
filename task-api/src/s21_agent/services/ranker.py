"""Ranking service for S21 Agent."""
from typing import List

from s21_agent.config import settings
from s21_agent.models.task import Task
from s21_agent.services.llm_client import LLMClient


def rank_tasks(tasks: List[Task], query: str = "") -> List[Task]:
    """Rank tasks by relevance to query using LLM for semantic matching."""
    if not tasks:
        return tasks
    
    if not query:
        return tasks
    
    llm = LLMClient()
    
    # Only use LLM if API key is available
    if not llm.api_key:
        # Fallback to rule-based ranking
        return _rule_based_rank(tasks, query)
    
    try:
        # Use LLM to get relevance scores
        return _llm_rank(tasks, query, llm)
    except Exception:
        # Fallback to rule-based if LLM fails
        return _rule_based_rank(tasks, query)


def _llm_rank(tasks: List[Task], query: str, llm: LLMClient) -> List[Task]:
    """Rank tasks using LLM semantic analysis."""
    # Build prompt for LLM
    tasks_text = "\n".join([
        f"- {t.source_id}: {t.title} ({t.description[:200] if t.description else ''})"
        for t in tasks[:20]  # Limit to 20 tasks for API
    ])
    
    system_prompt = """You are a search relevance assessor. Rate how relevant each task is to the query.
    
Output JSON with relevance scores from 0 to 100 for each task ID."""

    user_prompt = f"""Query: {query}

Tasks to rank:
{tasks_text}

Output JSON format:
{{"WMB-123": 95, "WMB-456": 70, "WMB-789": 45}}"""

    try:
        response = llm.analyze_task(query, tasks_text[:3000], user_prompt)
        
        # Parse scores from response
        import json
        import re
        
        # Try to extract JSON from response
        json_match = re.search(r'\{[^}]+\}', response)
        if json_match:
            scores = json.loads(json_match.group())
        else:
            scores = {}
        
        # Apply scores
        def relevance_score(task: Task) -> float:
            base_score = scores.get(task.source_id, 50.0)
            
            # Boost for exact title match
            if query.lower() in task.title.lower():
                base_score = min(100, base_score + 20)
            
            # Boost for ID match
            if query.lower() in task.source_id.lower():
                base_score = min(100, base_score + 30)
            
            return base_score
        
        return sorted(tasks, key=relevance_score, reverse=True)
        
    except Exception:
        return _rule_based_rank(tasks, query)


def _rule_based_rank(tasks: List[Task], query: str) -> List[Task]:
    """Rule-based ranking fallback."""
    query_lower = query.lower()

    def relevance_score(task: Task) -> float:
        score = 0.0

        # Title match (highest weight)
        if query_lower in task.title.lower():
            score += 3.0

        # Description match
        if task.description and query_lower in task.description.lower():
            score += 1.0

        # ID match (exact)
        if query_lower in task.source_id.lower():
            score += 5.0
        
        # Partial ID match
        if task.source_id.lower().startswith(query_lower):
            score += 4.0

        return score

    return sorted(tasks, key=relevance_score, reverse=True)
