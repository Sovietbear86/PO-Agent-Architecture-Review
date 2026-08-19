# Learning Loop 012 — implementation

## Goal
Close the controlled learning loop without granting the agent authority to mutate production skills.

## Implemented
- immutable baseline/candidate evaluation snapshots;
- explicit baseline-vs-candidate promotion gate;
- fail-closed rejection on false-green, execution-error regression, pass-rate regression, mismatched case set, or insufficient evidence;
- hard human-approval boundary: a green gate is only a recommendation;
- developer tests anchored to the Core-8 minimum sample.

## Invariants
Core-8 remains the release baseline. Existing AS21 real-data, attachment, false-green and fail-closed checks must remain green. Learning Loop 012 does not write to SkillRegistry and cannot promote a candidate by itself.

## QA assignment for GigaCode
1. Run the full existing test suite plus `tests/test_learning_loop.py`.
2. Re-run Core-8 on the real AS21 dataset used by the accepted 011K baseline.
3. Create one controlled degraded candidate for a Core-8 skill (for example one expected case fails, or one false-green is introduced).
4. Evaluate baseline and candidate on exactly the same cases.
5. Verify the gate returns `reject` and no production skill/version changes.
6. Restore the candidate and verify an 8/8 candidate can reach only `recommend` until explicit `human_approved=True` is supplied.
7. Verify fewer than 8 comparable cases returns `insufficient_evidence`.
8. Save evidence, commands, outputs and final verdict in `qa_reports/LEARNING_LOOP_012_QA.md`.

## Acceptance
PASS only if the existing suite is green, Core-8 remains 8/8, degraded candidate is rejected, false-green is rejected, insufficient evidence fails closed, and no automatic production promotion occurs.
