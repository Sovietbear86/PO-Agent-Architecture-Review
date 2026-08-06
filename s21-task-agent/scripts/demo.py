from s21_agent.services.quality_scorer import (
    CriterionScore,
    calculate_quality_score,
    category,
)

criteria = [
    CriterionScore("goal", 15, 0.9, "Цель сформулирована"),
    CriterionScore("acceptance_criteria", 20, 0.5, "Критерии частично измеримы"),
    CriterionScore("dependencies", 10, 0.4, "Не все зависимости указаны"),
]

score = calculate_quality_score(criteria)
print({"score": score, "category": category(score)})
