"""Feedback analyzer for skill evolution in PO Agent Platform v2.

Analyzes feedback to identify improvement candidates.
"""

import re
from typing import Optional, List, Dict, Any

from po_agent.evolution.models import (
    ImprovementType,
    SkillImprovementCandidate,
    CandidateStatus,
)


class FeedbackAnalyzer:
    """Analyzer for user feedback to identify improvement opportunities."""

    # Negative sentiment keywords
    NEGATIVE_KEYWORDS = [
        "плохо", "хуже", "неправильно", "не работает", "ошибка",
        "неверно", "не понял", "непонятно", "сбивая", "ошибся",
        "не помог", "неактуально", "некорректно", "неполный",
    ]

    # Positive sentiment keywords
    POSITIVE_KEYWORDS = [
        "хорошо", "отлично", "правильно", "понятно", "помог",
        "актуально", "корректно", "полный", "точно",
    ]

    # Improvement intent keywords
    IMPROVEMENT_INTENTS = {
        "accuracy": [
            "неправильно", "ошибка", "неверно", "ошибся",
        ],
        "clarification": [
            "не понял", "непонятно", "что значит", "упрощ",
            "объясни", "прост", "другими словами",
        ],
        "rating": [
            "плохо", "хуже", "убавь", "улучш", "добавь",
        ],
    }

    def __init__(self, negative_threshold: float = 0.3):
        """Initialize feedback analyzer.

        Args:
            negative_threshold: Threshold for negative sentiment
        """
        self.negative_threshold = negative_threshold

    def analyze_text(
        self,
        text: str,
    ) -> Dict[str, Any]:
        """Analyze feedback text.

        Args:
            text: Feedback text

        Returns:
            Analysis results
        """
        text_lower = text.lower()

        # Count positive and negative keywords
        negative_count = sum(
            1 for kw in self.NEGATIVE_KEYWORDS
            if kw in text_lower
        )
        positive_count = sum(
            1 for kw in self.POSITIVE_KEYWORDS
            if kw in text_lower
        )

        total_keywords = negative_count + positive_count
        negative_ratio = (
            negative_count / total_keywords
            if total_keywords > 0
            else 0
        )

        # Identify improvement intent
        improvement_intents = []
        for intent_type, keywords in self.IMPROVEMENT_INTENTS.items():
            if any(kw in text_lower for kw in keywords):
                improvement_intents.append(intent_type)

        return {
            "negative_count": negative_count,
            "positive_count": positive_count,
            "negative_ratio": negative_ratio,
            "is_negative": negative_ratio >= self.negative_threshold,
            "improvement_intents": improvement_intents,
            "has_feedback": total_keywords > 0,
        }

    def analyze_feedback_entry(
        self,
        feedback: Dict[str, Any],
    ) -> Optional[SkillImprovementCandidate]:
        """Analyze a single feedback entry.

        Args:
            feedback: Feedback entry dict

        Returns:
            Improvement candidate or None
        """
        # Extract data from feedback
        data = feedback.get("data", {})
        text = data.get("comment", "")

        analysis = self.analyze_text(text)

        if not analysis["is_negative"]:
            return None

        # Determine improvement type from intent
        improvement_type = self._map_improvement_intent(
            analysis["improvement_intents"]
        )

        if not improvement_type:
            return None

        # Create candidate
        candidate = SkillImprovementCandidate(
            candidate_id=f"feedback-{feedback.get('feedback_id', 'unknown')}",
            skill_id=data.get("skill_id", "unknown"),
            skill_version=data.get("skill_version", "1.0.0"),
            improvement_type=improvement_type,
            threshold_value=0.0,  # Will be set during analysis
            current_value=analysis["negative_ratio"],
            feedback_samples=[feedback],
            status=CandidateStatus.IDENTIFIED,
        )

        return candidate

    def _map_improvement_intent(
        self,
        intents: List[str],
    ) -> Optional[ImprovementType]:
        """Map improvement intent to improvement type.

        Args:
            intents: List of intent types

        Returns:
            Improvement type or None
        """
        intent_mapping = {
            "accuracy": ImprovementType.LOW_ACCURACY,
            "clarification": ImprovementType.HIGH_CLARIFICATION_RATE,
            "rating": ImprovementType.LOW_RATING,
        }

        for intent in intents:
            if intent in intent_mapping:
                return intent_mapping[intent]

        return None

    def analyze_multiple_feedback(
        self,
        feedback_list: List[Dict[str, Any]],
    ) -> List[SkillImprovementCandidate]:
        """Analyze multiple feedback entries.

        Args:
            feedback_list: List of feedback entries

        Returns:
            List of improvement candidates
        """
        candidates = []

        for feedback in feedback_list:
            candidate = self.analyze_feedback_entry(feedback)
            if candidate:
                candidates.append(candidate)

        return candidates


# Export for convenience
__all__ = ["FeedbackAnalyzer"]
