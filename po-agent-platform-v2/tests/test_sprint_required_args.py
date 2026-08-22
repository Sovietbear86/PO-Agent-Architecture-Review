from po_agent.harness.dialogue_runtime import DialogueHarnessRuntime


def test_all_sprint_task_scoped_capabilities_require_sprint_id():
    runtime = object.__new__(DialogueHarnessRuntime)

    for capability_id in (
        "sprint.health",
        "sprint.scope",
        "sprint.velocity",
        "sprint.throughput",
        "sprint.wip",
        "sprint.cycle_time",
        "sprint.lead_time",
        "sprint.predictability",
        "sprint.risk_queue",
    ):
        valid, error = runtime._validate_required_args(capability_id, {})

        assert not valid
        assert error == "Missing required slot: sprint_id"


def test_sprint_current_requires_product_not_sprint_id():
    runtime = object.__new__(DialogueHarnessRuntime)

    valid, error = runtime._validate_required_args("sprint.current", {"product": "DMS"})

    assert valid
    assert error is None
