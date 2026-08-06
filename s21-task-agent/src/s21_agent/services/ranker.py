from dataclasses import dataclass


@dataclass
class RankingSignals:
    fulltext: float = 0.0
    semantic: float = 0.0
    metadata: float = 0.0
    freshness: float = 0.0
    source_quality: float = 0.0


def rank(signals: RankingSignals) -> float:
    value = (
        0.35 * signals.fulltext
        + 0.35 * signals.semantic
        + 0.15 * signals.metadata
        + 0.10 * signals.freshness
        + 0.05 * signals.source_quality
    )
    return round(value, 4)
