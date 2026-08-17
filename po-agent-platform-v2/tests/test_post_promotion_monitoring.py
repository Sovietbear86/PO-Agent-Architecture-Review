import pytest

from po_agent.harness.post_promotion_monitoring import (
    HealthObservation,
    MetricDirection,
    MetricRule,
    MetricValue,
    MonitoringBaseline,
    MonitoringPolicy,
    MonitoringVerdict,
    PostPromotionMonitor,
)


def _baseline():
    return MonitoringBaseline.create(
        promotion_id="promotion-1",
        candidate_id="candidate-1",
        candidate_fingerprint="f" * 64,
        release_ref="release-1",
        metrics=(MetricValue("success_rate", 0.95), MetricValue("latency_ms", 100.0)),
    )


def _policy():
    return MonitoringPolicy(
        rules=(
            MetricRule("success_rate", MetricDirection.HIGHER_IS_BETTER, 0.05),
            MetricRule("latency_ms", MetricDirection.LOWER_IS_BETTER, 0.10),
        ),
        min_observations=2,
        max_observations=4,
        breach_observations_required=2,
    )


def _obs(sequence, success_rate, latency_ms, *, promotion_id="promotion-1", release_ref="release-1"):
    return HealthObservation.create(
        promotion_id=promotion_id,
        release_ref=release_ref,
        sequence=sequence,
        metrics=(MetricValue("success_rate", success_rate), MetricValue("latency_ms", latency_ms)),
    )


def test_healthy_window_becomes_healthy_after_minimum_observations():
    monitor = PostPromotionMonitor()
    state = monitor.start(baseline=_baseline(), policy=_policy())
    state = monitor.record(state.monitor_id, _obs(1, 0.94, 102.0))
    assert state.latest_assessment.verdict is MonitoringVerdict.COLLECTING
    state = monitor.record(state.monitor_id, _obs(2, 0.95, 99.0))
    assert state.latest_assessment.verdict is MonitoringVerdict.HEALTHY


def test_two_regressed_windows_detect_degradation():
    monitor = PostPromotionMonitor()
    state = monitor.start(baseline=_baseline(), policy=_policy())
    state = monitor.record(state.monitor_id, _obs(1, 0.80, 130.0))
    assert state.latest_assessment.verdict is MonitoringVerdict.COLLECTING
    state = monitor.record(state.monitor_id, _obs(2, 0.82, 125.0))
    assert state.latest_assessment.verdict is MonitoringVerdict.DEGRADATION_DETECTED
    assert state.latest_assessment.breach_observation_count == 2


def test_rollback_recommendation_has_exact_release_binding_but_no_execution_authority():
    monitor = PostPromotionMonitor()
    state = monitor.start(baseline=_baseline(), policy=_policy())
    monitor.record(state.monitor_id, _obs(1, 0.80, 130.0))
    monitor.record(state.monitor_id, _obs(2, 0.80, 130.0))
    recommendation = monitor.recommend_rollback(state.monitor_id)
    assert recommendation.promotion_id == "promotion-1"
    assert recommendation.candidate_id == "candidate-1"
    assert recommendation.candidate_fingerprint == "f" * 64
    assert recommendation.release_ref == "release-1"
    assert not hasattr(recommendation, "apply")
    assert not hasattr(monitor, "rollback")


def test_cross_promotion_and_release_observations_are_rejected():
    monitor = PostPromotionMonitor()
    state = monitor.start(baseline=_baseline(), policy=_policy())
    with pytest.raises(ValueError, match="promotion_id"):
        monitor.record(state.monitor_id, _obs(1, 0.95, 100.0, promotion_id="other"))
    with pytest.raises(ValueError, match="release_ref"):
        monitor.record(state.monitor_id, _obs(1, 0.95, 100.0, release_ref="other"))


def test_missing_required_metric_is_fail_closed_as_insufficient_evidence():
    monitor = PostPromotionMonitor()
    state = monitor.start(baseline=_baseline(), policy=_policy())
    observation = HealthObservation.create(
        promotion_id="promotion-1",
        release_ref="release-1",
        sequence=1,
        metrics=(MetricValue("success_rate", 0.95),),
    )
    state = monitor.record(state.monitor_id, observation)
    assert state.latest_assessment.verdict is MonitoringVerdict.INSUFFICIENT_EVIDENCE


def test_provider_error_is_fail_closed_and_can_recommend_rollback():
    monitor = PostPromotionMonitor()
    state = monitor.start(baseline=_baseline(), policy=_policy())
    observation = HealthObservation.create(
        promotion_id="promotion-1",
        release_ref="release-1",
        sequence=1,
        metrics=(),
        provider_error="metrics backend unavailable",
    )
    state = monitor.record(state.monitor_id, observation)
    assert state.latest_assessment.verdict is MonitoringVerdict.PROVIDER_ERROR
    recommendation = monitor.recommend_rollback(state.monitor_id)
    assert "provider error" in recommendation.reason


def test_sequence_and_observation_budget_are_bounded():
    policy = MonitoringPolicy(
        rules=(MetricRule("success_rate", MetricDirection.HIGHER_IS_BETTER, 0.05),),
        min_observations=1,
        max_observations=2,
        breach_observations_required=2,
    )
    baseline = MonitoringBaseline.create(
        promotion_id="p",
        candidate_id="c",
        candidate_fingerprint="f",
        release_ref="r",
        metrics=(MetricValue("success_rate", 1.0),),
    )
    monitor = PostPromotionMonitor()
    state = monitor.start(baseline=baseline, policy=policy)
    with pytest.raises(ValueError, match="sequence"):
        monitor.record(
            state.monitor_id,
            HealthObservation.create(
                promotion_id="p", release_ref="r", sequence=2, metrics=(MetricValue("success_rate", 1.0),)
            ),
        )
    monitor.record(
        state.monitor_id,
        HealthObservation.create(
            promotion_id="p", release_ref="r", sequence=1, metrics=(MetricValue("success_rate", 1.0),)
        ),
    )
    monitor.record(
        state.monitor_id,
        HealthObservation.create(
            promotion_id="p", release_ref="r", sequence=2, metrics=(MetricValue("success_rate", 1.0),)
        ),
    )
    with pytest.raises(ValueError, match="budget"):
        monitor.record(
            state.monitor_id,
            HealthObservation.create(
                promotion_id="p", release_ref="r", sequence=3, metrics=(MetricValue("success_rate", 1.0),)
            ),
        )


def test_invalid_or_duplicate_metric_data_is_rejected():
    with pytest.raises(ValueError):
        MetricValue("x", float("nan"))
    with pytest.raises(ValueError, match="duplicate"):
        MonitoringBaseline.create(
            promotion_id="p",
            candidate_id="c",
            candidate_fingerprint="f",
            release_ref="r",
            metrics=(MetricValue("x", 1.0), MetricValue("x", 2.0)),
        )
