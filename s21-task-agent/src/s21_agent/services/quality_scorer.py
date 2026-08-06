from dataclasses import dataclass


@dataclass
class CriterionScore:
    name: str
    weight: int
    score: float
    rationale: str
    source: str | None = None


def calculate_quality_score(criteria: list[CriterionScore]) -> float:
    total_weight = sum(item.weight for item in criteria)
    if total_weight == 0:
        return 0.0
    weighted = sum(item.weight * item.score for item in criteria)
    return round(weighted / total_weight, 1)


def category(score: float) -> str:
    if score >= 90:
        return "готова к разработке"
    if score >= 75:
        return "в целом готова, нужны небольшие уточнения"
    if score >= 50:
        return "требуется доработка постановки"
    return "не готова к реализации"
