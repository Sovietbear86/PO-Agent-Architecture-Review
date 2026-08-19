# Learning Loop 012 — implementation

## Goal
Close the controlled learning loop without granting the agent authority to mutate production skills.

## Implemented
- immutable baseline/candidate evaluation snapshots;
- explicit baseline-vs-candidate promotion gate;
- fail-closed rejection on false-green, execution-error regression, pass-rate regression, mismatched case count, or insufficient evidence;
- hard human-approval boundary: a green gate is only a recommendation;
- `ControlledLearningOrchestrator` binding an existing `SkillImprovementCandidate` to baseline/candidate evidence and a promotion decision;
- immutable `CandidateEvaluationArtifact` for human review;
- explicit prohibition on automatic `SkillRegistry` mutation/promotion in the controlled orchestrator;
- bridge from the existing `EvalRunner/EvalReport` into Learning Loop snapshots while preserving run metadata and explicit safety counters;
- developer tests anchored to the accepted Core-8 minimum sample.

## Existing architecture reused
Learning Loop 012 reuses the pre-existing evolution layer rather than replacing it:
- `SkillEvolutionPipeline` continues to own discovery/candidate lifecycle;
- `FeedbackAnalyzer` remains a candidate signal source;
- `EvalRunner` remains an evaluation producer;
- `SkillRegistry` remains the version registry and explicit promotion mechanism;
- the new controlled loop sits between candidate creation and any approval/implementation action.

## Safety invariants
Core-8 remains the release baseline. Existing AS21 real-data, attachment, false-green and fail-closed checks must remain green.

The controlled loop does **not** call `approve_candidate`, `implement_improvement`, `register_new_version`, or `promote_candidate`. A clean candidate can reach only `RECOMMEND`. Explicit human approval is necessary even to satisfy the authorization predicate, and actual production promotion remains a separate action outside 012.

## QA
GigaCode assignment:
`qa_assignments/LEARNING_LOOP_012_CONTROLLED_E2E.md`

Expected report:
`qa_reports/LEARNING_LOOP_012_QA.md`

The QA must prove rejection of degraded/false-green candidates, fail-closed insufficient evidence, human approval boundary, integration with the existing candidate pipeline and EvalRunner, unchanged Core-8 8/8 production behavior, zero autonomous SkillRegistry mutations and zero AS21 mutations.

## Acceptance
012 is complete only if independent QA returns `LEARNING_LOOP_012_CONTROLLED_E2E = PASS`. Only then may the project proceed to Learning Loop 013 (candidate synthesis/shadow improvement on a real skill failure).