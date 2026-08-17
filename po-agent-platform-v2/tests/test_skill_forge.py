from po_agent.harness.failure_miner import FailureCluster
from po_agent.harness.skill_forge import ForgeArtifactKind, ForgePolicy, SkillArtifact, SkillForge


def cluster(category="intent_mismatch"):
    return FailureCluster(
        key=f"{category}:x",
        category=category,
        count=2,
        eval_ids=("e1", "e2"),
        queries=("q1", "q2"),
        expected_intents=("task_search",),
        affected_skill_ids=("task-search-product",),
        recommendation="review safely",
    )


def test_intent_cluster_forges_routing_metadata():
    artifact = SkillForge().forge(cluster())
    assert artifact.kind is ForgeArtifactKind.ROUTING_METADATA
    assert artifact.target_intents == ("task_search",)
    assert artifact.target_skill_ids == ("task-search-product",)
    assert artifact.executable is False
    assert artifact.apply is False


def test_entity_cluster_forges_context_policy():
    artifact = SkillForge().forge(cluster("entity_resolution"))
    assert artifact.kind is ForgeArtifactKind.ENTITY_CONTEXT_POLICY
    assert artifact.proposed_change["constraint"] == "source_grounding_remains_mandatory"


def test_fact_cluster_forges_evidence_contract():
    artifact = SkillForge().forge(cluster("answer_fact"))
    assert artifact.kind is ForgeArtifactKind.EVIDENCE_SYNTHESIS_CONTRACT
    assert artifact.proposed_change["constraint"] == "source_backed_facts_only"


def test_unknown_cluster_fails_to_manual_review_artifact():
    artifact = SkillForge().forge(cluster("unknown"))
    assert artifact.kind is ForgeArtifactKind.MANUAL_REVIEW
    assert artifact.proposed_change["execution_authority"] == "none"


def test_acceptance_contract_is_safety_first():
    artifact = SkillForge().forge(cluster())
    contract = artifact.acceptance_contract
    assert contract["must_pass_source_eval_ids"] == ["e1", "e2"]
    assert contract["must_not_increase_safety_regressions"] is True
    assert contract["must_not_increase_new_code_regressions"] is True
    assert contract["must_not_increase_wrong_skill_selections"] is True
    assert contract["must_not_increase_hallucinated_entities"] is True
    assert contract["must_not_increase_ungrounded_answers"] is True


def test_shadow_plan_requires_same_seeds_and_approval():
    artifact = SkillForge().forge(cluster())
    plan = artifact.shadow_eval_plan
    assert plan["mode"] == "baseline_vs_candidate"
    assert plan["same_seed_for_both_runners"] is True
    assert plan["require_shadow_evaluation"] is True
    assert plan["human_approval_required"] is True


def test_forge_bounds_examples_and_target_skills():
    c = FailureCluster(
        key="intent_mismatch:x",
        category="intent_mismatch",
        count=4,
        eval_ids=("e1", "e2", "e3", "e4"),
        queries=("q1", "q2", "q3", "q4"),
        expected_intents=("task_search",),
        affected_skill_ids=("s1", "s2", "s3"),
        recommendation="review safely",
    )
    artifact = SkillForge(ForgePolicy(max_examples=2, max_target_skills=2)).forge(c)
    assert artifact.examples == ("q1", "q2")
    assert artifact.target_skill_ids == ("s1", "s2")


def test_artifact_bridges_to_improvement_candidate_without_apply_authority():
    artifact = SkillForge().forge(cluster())
    candidate = artifact.to_improvement_candidate()
    assert candidate.kind == "forge:routing_metadata"
    assert candidate.source_eval_ids == ("e1", "e2")
    assert candidate.proposed_change["apply"] is False
    assert candidate.proposed_change["executable"] is False
    assert candidate.proposed_change["forge_artifact_id"] == artifact.artifact_id
    assert candidate.requires_human_approval is True


def test_artifact_rejects_executable_or_applying_state():
    base = dict(
        artifact_id="a",
        created_at="now",
        source_failure_key="k",
        source_eval_ids=("e",),
        kind=ForgeArtifactKind.MANUAL_REVIEW,
        title="t",
        rationale="r",
        target_skill_ids=(),
        target_intents=(),
        examples=("q",),
        proposed_change={},
        acceptance_contract={},
        shadow_eval_plan={},
    )
    try:
        SkillArtifact(**base, executable=True)
        assert False, "expected executable artifact to be rejected"
    except ValueError:
        pass
    try:
        SkillArtifact(**base, apply=True)
        assert False, "expected applying artifact to be rejected"
    except ValueError:
        pass


def test_empty_cluster_evidence_is_rejected():
    c = FailureCluster(
        key="intent_mismatch:x",
        category="intent_mismatch",
        count=0,
        eval_ids=(),
        queries=(),
        expected_intents=(),
        affected_skill_ids=(),
        recommendation="review safely",
    )
    try:
        SkillForge().forge(c)
        assert False, "expected evidence-less cluster to be rejected"
    except ValueError:
        pass
