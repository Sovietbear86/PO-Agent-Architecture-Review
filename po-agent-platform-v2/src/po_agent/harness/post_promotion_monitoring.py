"""Bounded post-promotion monitoring for governed evolution releases.

The monitor compares immutable baseline metrics with a bounded stream of live
observations. It can detect degradation and produce an exact rollback
recommendation, but it has no authority to perform rollback itself.
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, replace
from enum import Enum
from typing import Iterable


class MetricDirection(str, Enum):
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"


@dataclass(frozen=True)
class MetricRule:
    name: str
    direction: MetricDirection
    allowed_regression_ratio: float = 0.05

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("metric rule name is required")
        if not math.isfinite(self.allowed_regression_ratio) or self.allowed_regression_ratio < 0:
            raise ValueError("allowed_regression_ratio must be finite and non-negative")


@dataclass(frozen=True)
class MetricValue:
    name: str
    value: float

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("metric name is required")
        if not math.isfinite(self.value):
            raise ValueError("metric value must be finite")


@dataclass(frozen=True)
class MonitoringBaseline:
    baseline_id: str
    promotion_id: str
    candidate_id: str
    candidate_fingerprint: str
    release_ref: str
    metrics: tuple[MetricValue, ...]

    @classmethod
    def create(
        cls,
        *,
        promotion_id: str,
        candidate_id: str,
        candidate_fingerprint: str,
        release_ref: str,
        metrics: Iterable[MetricValue],
    ) -> "MonitoringBaseline":
        values = tuple(metrics)
        cls._validate_identity(promotion_id, candidate_id, candidate_fingerprint, release_ref)
        cls._validate_unique_metrics(values)
        if not values:
            raise ValueError("monitoring baseline requires metrics")
        return cls(
            baseline_id=str(uuid.uuid4()),
            promotion_id=promotion_id.strip(),
            candidate_id=candidate_id.strip(),
            candidate_fingerprint=candidate_fingerprint.strip(),
            release_ref=release_ref.strip(),
            metrics=values,
        )

    @staticmethod
    def _validate_identity(
        promotion_id: str,
        candidate_id: str,
        candidate_fingerprint: str,
        release_ref: str,
    ) -> None:
        if not promotion_id.strip():
            raise ValueError("promotion_id is required")
        if not candidate_id.strip():
            raise ValueError("candidate_id is required")
        if not candidate_fingerprint.strip():
            raise ValueError("candidate_fingerprint is required")
        if not release_ref.strip():
            raise ValueError("release_ref is required")

    @staticmethod
    def _validate_unique_metrics(values: tuple[MetricValue, ...]) -> None:
        names = [item.name for item in values]
        if len(names) != len(set(names)):
            raise ValueError("duplicate metric names are not allowed")

    def metric_map(self) -> dict[str, float]:
        return {item.name: item.value for item in self.metrics}


@dataclass(frozen=True)
class MonitoringPolicy:
    rules: tuple[MetricRule, ...]
    min_observations: int = 3
    max_observations: int = 20
    breach_observations_required: int = 2
    fail_closed_on_provider_error: bool = True

    def __post_init__(self) -> None:
        if not self.rules:
            raise ValueError("monitoring policy requires metric rules")
        names = [rule.name for rule in self.rules]
        if len(names) != len(set(names)):
            raise ValueError("duplicate metric rules are not allowed")
        if self.min_observations <= 0:
            raise ValueError("min_observations must be positive")
        if self.max_observations < self.min_observations:
            raise ValueError("max_observations must be >= min_observations")
        if self.breach_observations_required <= 0:
            raise ValueError("breach_observations_required must be positive")
        if self.breach_observations_required > self.max_observations:
            raise ValueError("breach_observations_required cannot exceed max_observations")


@dataclass(frozen=True)
class HealthObservation:
    observation_id: str
    promotion_id: str
    release_ref: str
    sequence: int
    metrics: tuple[MetricValue, ...]
    provider_error: str | None = None

    @classmethod
    def create(
        cls,
        *,
        promotion_id: str,
        release_ref: str,
        sequence: int,
        metrics: Iterable[MetricValue],
        provider_error: str | None = None,
    ) -> "HealthObservation":
        values = tuple(metrics)
        if not promotion_id.strip():
            raise ValueError("promotion_id is required")
        if not release_ref.strip():
            raise ValueError("release_ref is required")
        if sequence <= 0:
            raise ValueError("observation sequence must be positive")
        MonitoringBaseline._validate_unique_metrics(values)
        error = provider_error.strip() if provider_error is not None else None
        if error == "":
            error = None
        return cls(
            observation_id=str(uuid.uuid4()),
            promotion_id=promotion_id.strip(),
            release_ref=release_ref.strip(),
            sequence=sequence,
            metrics=values,
            provider_error=error,
        )

    def metric_map(self) -> dict[str, float]:
        return {item.name: item.value for item in self.metrics}


class MonitoringVerdict(str, Enum):
    COLLECTING = "collecting"
    HEALTHY = "healthy"
    DEGRADATION_DETECTED = "degradation_detected"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    PROVIDER_ERROR = "provider_error"


@dataclass(frozen=True)
class MetricAssessment:
    name: str
    baseline_value: float
    observed_value: float
    regression_ratio: float
    breached: bool


@dataclass(frozen=True)
class MonitoringAssessment:
    verdict: MonitoringVerdict
    observation_count: int
    breach_observation_count: int
    assessments: tuple[MetricAssessment, ...]
    reason: str


@dataclass(frozen=True)
class RollbackRecommendation:
    recommendation_id: str
    monitor_id: str
    promotion_id: str
    candidate_id: str
    candidate_fingerprint: str
    release_ref: str
    reason: str
    breach_observation_count: int


@dataclass(frozen=True)
class PostPromotionMonitorState:
    monitor_id: str
    baseline: MonitoringBaseline
    policy: MonitoringPolicy
    observations: tuple[HealthObservation, ...]
    latest_assessment: MonitoringAssessment
    recommendation: RollbackRecommendation | None = None


class PostPromotionMonitor:
    """Deterministic, bounded health monitor with no deployment authority."""

    def __init__(self) -> None:
        self._states: dict[str, PostPromotionMonitorState] = {}

    def start(self, *, baseline: MonitoringBaseline, policy: MonitoringPolicy) -> PostPromotionMonitorState:
        baseline_names = set(baseline.metric_map())
        required_names = {rule.name for rule in policy.rules}
        missing = sorted(required_names - baseline_names)
        if missing:
            raise ValueError(f"baseline missing required metrics: {', '.join(missing)}")
        state = PostPromotionMonitorState(
            monitor_id=str(uuid.uuid4()),
            baseline=baseline,
            policy=policy,
            observations=(),
            latest_assessment=MonitoringAssessment(
                verdict=MonitoringVerdict.COLLECTING,
                observation_count=0,
                breach_observation_count=0,
                assessments=(),
                reason="monitoring_started",
            ),
        )
        self._states[state.monitor_id] = state
        return state

    def state(self, monitor_id: str) -> PostPromotionMonitorState | None:
        return self._states.get(monitor_id)

    def record(self, monitor_id: str, observation: HealthObservation) -> PostPromotionMonitorState:
        state = self._require_state(monitor_id)
        if state.recommendation is not None:
            raise ValueError("monitor already produced rollback recommendation")
        if observation.promotion_id != state.baseline.promotion_id:
            raise ValueError("observation promotion_id does not match monitoring baseline")
        if observation.release_ref != state.baseline.release_ref:
            raise ValueError("observation release_ref does not match monitoring baseline")
        if len(state.observations) >= state.policy.max_observations:
            raise ValueError("monitoring observation budget exhausted")
        expected_sequence = len(state.observations) + 1
        if observation.sequence != expected_sequence:
            raise ValueError(f"observation sequence must be {expected_sequence}")
        if any(existing.observation_id == observation.observation_id for existing in state.observations):
            raise ValueError("duplicate observation_id")

        observations = (*state.observations, observation)
        assessment = self._assess(state.baseline, state.policy, observations)
        updated = replace(state, observations=observations, latest_assessment=assessment)
        self._states[monitor_id] = updated
        return updated

    def recommend_rollback(self, monitor_id: str, *, reason: str | None = None) -> RollbackRecommendation:
        state = self._require_state(monitor_id)
        if state.recommendation is not None:
            raise ValueError("rollback recommendation already exists")
        if state.latest_assessment.verdict not in {
            MonitoringVerdict.DEGRADATION_DETECTED,
            MonitoringVerdict.PROVIDER_ERROR,
        }:
            raise ValueError("rollback recommendation requires detected degradation")
        recommendation = RollbackRecommendation(
            recommendation_id=str(uuid.uuid4()),
            monitor_id=state.monitor_id,
            promotion_id=state.baseline.promotion_id,
            candidate_id=state.baseline.candidate_id,
            candidate_fingerprint=state.baseline.candidate_fingerprint,
            release_ref=state.baseline.release_ref,
            reason=(reason or state.latest_assessment.reason).strip(),
            breach_observation_count=state.latest_assessment.breach_observation_count,
        )
        if not recommendation.reason:
            raise ValueError("rollback recommendation reason is required")
        self._states[monitor_id] = replace(state, recommendation=recommendation)
        return recommendation

    def _assess(
        self,
        baseline: MonitoringBaseline,
        policy: MonitoringPolicy,
        observations: tuple[HealthObservation, ...],
    ) -> MonitoringAssessment:
        latest = observations[-1]
        if latest.provider_error and policy.fail_closed_on_provider_error:
            return MonitoringAssessment(
                verdict=MonitoringVerdict.PROVIDER_ERROR,
                observation_count=len(observations),
                breach_observation_count=sum(1 for item in observations if item.provider_error),
                assessments=(),
                reason=f"monitoring provider error: {latest.provider_error}",
            )

        baseline_map = baseline.metric_map()
        required_names = {rule.name for rule in policy.rules}
        observation_map = latest.metric_map()
        missing = sorted(required_names - set(observation_map))
        if missing:
            return MonitoringAssessment(
                verdict=MonitoringVerdict.INSUFFICIENT_EVIDENCE,
                observation_count=len(observations),
                breach_observation_count=0,
                assessments=(),
                reason=f"observation missing required metrics: {', '.join(missing)}",
            )

        current_assessments = tuple(
            self._assess_metric(
                rule=rule,
                baseline_value=baseline_map[rule.name],
                observed_value=observation_map[rule.name],
            )
            for rule in policy.rules
        )
        breach_observations = 0
        for item in observations:
            if item.provider_error and policy.fail_closed_on_provider_error:
                breach_observations += 1
                continue
            values = item.metric_map()
            if required_names - set(values):
                continue
            if any(
                self._assess_metric(
                    rule=rule,
                    baseline_value=baseline_map[rule.name],
                    observed_value=values[rule.name],
                ).breached
                for rule in policy.rules
            ):
                breach_observations += 1

        if breach_observations >= policy.breach_observations_required:
            return MonitoringAssessment(
                verdict=MonitoringVerdict.DEGRADATION_DETECTED,
                observation_count=len(observations),
                breach_observation_count=breach_observations,
                assessments=current_assessments,
                reason="post-promotion regression threshold exceeded",
            )
        if len(observations) < policy.min_observations:
            verdict = MonitoringVerdict.COLLECTING
            reason = "minimum observation window not reached"
        elif any(item.breached for item in current_assessments):
            verdict = MonitoringVerdict.COLLECTING
            reason = "single-window regression observed; waiting for confirmation"
        else:
            verdict = MonitoringVerdict.HEALTHY
            reason = "post-promotion health within allowed regression thresholds"
        return MonitoringAssessment(
            verdict=verdict,
            observation_count=len(observations),
            breach_observation_count=breach_observations,
            assessments=current_assessments,
            reason=reason,
        )

    @staticmethod
    def _assess_metric(*, rule: MetricRule, baseline_value: float, observed_value: float) -> MetricAssessment:
        scale = max(abs(baseline_value), 1e-12)
        if rule.direction is MetricDirection.HIGHER_IS_BETTER:
            regression = max(0.0, baseline_value - observed_value) / scale
        else:
            regression = max(0.0, observed_value - baseline_value) / scale
        return MetricAssessment(
            name=rule.name,
            baseline_value=baseline_value,
            observed_value=observed_value,
            regression_ratio=regression,
            breached=regression > rule.allowed_regression_ratio,
        )

    def _require_state(self, monitor_id: str) -> PostPromotionMonitorState:
        state = self._states.get(monitor_id)
        if state is None:
            raise ValueError("unknown post-promotion monitor")
        return state
