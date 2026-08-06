from s21_agent.services.ranker import RankingSignals, rank


def test_rank() -> None:
    value = rank(RankingSignals(fulltext=1, semantic=1, metadata=1, freshness=1, source_quality=1))
    assert value == 1.0
