# QA Assignment — Learning Loop 014: sprint_health analytical improvement + rollback

## Role boundary
GigaCode is TESTER ONLY. Do not edit production code, repository tests, skill definitions, configuration, AS21 data, or committed fixtures. Temporary `/tmp` scripts are allowed for isolated candidate evaluation and isolated in-memory SkillRegistry lifecycle testing only.

## Purpose
Close Gate C from `PO_AGENT_HARNESS_EVOLUTION_PLAN.md` by proving a second, analytical learning cycle on `sprint_health`, followed by explicit human-approved promotion in an isolated registry and deterministic rollback to the previous active version.

## Pre-check
1. Checkout/pull `feat/learning-loop-014-v1`, record exact HEAD and clean status.
2. Read `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`, status amendments 013 and 014.
3. Run all 012/013 tests plus `tests/test_controlled_skill_lifecycle.py`.
4. Keep AS21 read-only. Production SkillRegistry/skill files must not be mutated.

## Test A — analytical failure -> bounded proposal
Create a controlled reproducible `sprint_health` weakness on an analytical rule, not a source defect. Prefer a legitimate metric/edge case such as an empty/partial sprint metric guard, blocked/aging classification edge case, or another deterministic analytical condition that can be evaluated without inventing AS21 facts.

Feed classified failure evidence into the existing 013 synthesis path.

Required:
- failure classification is appropriate (prefer `METRIC_ERROR`, `PROMPT_FAILURE`, or `MISSING_EVIDENCE` depending on the chosen case);
- proposal is bounded to metric/prompt/evidence behavior;
- source/adapter failures remain source-contract review only;
- proposal is non-executable, sandbox-only, human approval required;
- trace/evidence IDs are retained.

## Test B — frozen sprint_health corpus
Build at least 8 safe evaluation cases for `sprint_health`, including:
- real current OLP sprint happy path;
- another real/recent sprint if available;
- blocked/WIP/aging or equivalent deterministic metric path;
- empty/nonexistent sprint control;
- the controlled analytical weakness;
- at least two protected cases that already pass baseline behavior;
- one false-green/unsupported protection where applicable.

Record real `corpus_id`, concrete `case_set_sha256`, baseline score and candidate score. No placeholders are allowed in the report.

Required: baseline and candidate use exactly the same corpus ID/hash/case count.

## Test C — isolated candidate and measurable shadow improvement
Apply only the synthesized bounded proposal in a temporary/in-memory candidate evaluator. Do not edit repo files.

Required:
- baseline is measurably weaker than candidate on the target condition;
- candidate improves the intended analytical metric;
- no previously green protected case regresses;
- false-green count remains zero;
- `LearningCycle013.run_shadow()` (or equivalent existing frozen shadow path) returns `RECOMMEND` only;
- no production mutation occurs.

If the first chosen weakness is already green, choose another legitimate analytical edge case. Never damage source truth or weaken protected expectations merely to manufacture an improvement.

## Test D — explicit human approval boundary
Use a completely isolated in-memory `SkillRegistry` loaded from `INITIAL_SKILLS`.

1. Create candidate version for `sprint_health` (for example patch version +1) using registry APIs.
2. Attach/use the green shadow evaluation artifact.
3. Call `ControlledSkillLifecycle.promote(... human_approved=False)`.
   - must fail;
   - active version must remain unchanged.
4. Call it again with `human_approved=True` and a non-empty reviewer/owner identity.
   - candidate becomes active in the isolated registry;
   - previous active version becomes deprecated;
   - a `PromotionReceipt` records previous/promoted versions.

Required: this is an isolated registry demonstration only. It must not write production skill YAML/JSON or AS21.

## Test E — rollback
Using the same isolated registry immediately after Test D:
- call `ControlledSkillLifecycle.rollback()` with explicit reviewer identity;
- verify old active version is restored;
- promoted candidate becomes deprecated;
- rollback receipt records exact restored/rolled-back versions;
- verify rollback refuses unsafe execution if active registry state changed out-of-band after promotion.

Required: `ROLLBACK_RESTORES_PREVIOUS_ACTIVE = YES`.

## Test F — lifecycle attacks
Prove all fail closed:
1. REJECT shadow artifact + human approval -> cannot promote;
2. insufficient-evidence artifact -> cannot promote;
3. missing human approval -> cannot promote;
4. candidate version missing -> cannot promote;
5. candidate version not in CANDIDATE status -> cannot promote;
6. rollback with no promotion receipt -> fail;
7. rollback after unexpected active-version change -> fail.

## Test G — real Core-8 protected regression
Re-run accepted real-AS21 Core-8 production pack.

Required:
- Core-8 = 8/8;
- false-green production controls GREEN;
- sprint completeness GREEN;
- WMB-30000 Office attachments visible unless proven live-data drift;
- AS21 mutations = 0.

## Test H — full regression
Compare to 013 baseline:
- 1183 passed
- 6 failed known debt
- 11 errors known environment/legacy debt
- 12 skipped

New 014 developer tests must pass. `NEW_HIGH_PRODUCTION_REGRESSIONS = 0`.

## Gate C authorization
Set `GATE_C_LEARNING_LOOP_GREEN = YES` iff ALL are true:
- measurable `sprint_health` improvement demonstrated on identical frozen corpus;
- bounded proposal synthesis PASS;
- source anti-learning PASS;
- shadow result = RECOMMEND only;
- explicit human approval required before isolated promotion;
- isolated candidate promotion PASS;
- rollback restores previous active version;
- lifecycle attacks fail closed;
- Core-8 remains 8/8;
- new HIGH production regressions = 0;
- automatic production mutations = 0;
- AS21 mutations = 0.

If Gate C is YES, set `READY_FOR_GATE_D_48_SKILL_RECOVERY = YES`.

## Report
Publish and push:
`qa_reports/LEARNING_LOOP_014_SPRINT_HEALTH_ROLLBACK.md`

End with concrete values only:

```text
ASSIGNMENT_ID = LEARNING_LOOP_014_SPRINT_HEALTH_ROLLBACK
CURRENT_HEAD = <sha>
AUTO_ANALYTICAL_PROPOSAL_PASS = YES|NO
SOURCE_CONTRACT_ANTI_LEARNING_PASS = YES|NO
FROZEN_CORPUS_ID = <real-id>
FROZEN_CASE_SET_SHA256 = <real-sha256>
BASELINE_SPRINT_HEALTH_SCORE = <x/y>
CANDIDATE_SPRINT_HEALTH_SCORE = <x/y>
MEASURABLE_ANALYTICAL_IMPROVEMENT_PASS = YES|NO
SHADOW_DECISION = RECOMMEND|REJECT|INSUFFICIENT_EVIDENCE
HUMAN_APPROVAL_BOUNDARY_PASS = YES|NO
ISOLATED_PROMOTION_PASS = YES|NO
PROMOTED_VERSION = <version>
ROLLBACK_RESTORES_PREVIOUS_ACTIVE = YES|NO
RESTORED_VERSION = <version>
LIFECYCLE_ATTACKS_PASS = YES|NO
CORE8_AGENT_E2E_PASS = x/8
FALSE_GREEN_CONTROLS_PASS = YES|NO
NEW_HIGH_PRODUCTION_REGRESSIONS = N
AUTOMATIC_PRODUCTION_MUTATIONS = N
AS21_MUTATIONS_DURING_TEST = N
GATE_C_LEARNING_LOOP_GREEN = YES|NO
READY_FOR_GATE_D_48_SKILL_RECOVERY = YES|NO
```

After publishing, STOP. Do not begin Gate D and do not change production code.