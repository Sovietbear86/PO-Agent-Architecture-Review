from s21_agent.services.quality_scorer import (
    CriterionScore,
    calculate_quality_score,
    category,
)


def test_quality_score() -> None:
    score = calculate_quality_score([
        CriterionScore("goal", 50, 1.0, "ok"),
        CriterionScore("criteria", 50, 0.5, "partial"),
    ])
    assert score == 0.8


def test_category() -> None:
    assert category(95) == "готова к разработке"
