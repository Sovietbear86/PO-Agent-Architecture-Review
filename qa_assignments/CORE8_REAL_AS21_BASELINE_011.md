# QA Assignment: CORE8 REAL AS21 BASELINE 011

## Objective
Establish a trustworthy real-data baseline for the eight Core-8 PO Agent capabilities before any further Learning Loop work. Use real AS21/SWTR data only for acceptance evidence. Do not weaken production behavior to satisfy tests.

## Mandatory pre-check
1. Work on `feat/real-baseline-candidate-eval-v1` (or create a dedicated child branch if needed; report exact branch/HEAD).
2. Read the project evolution/master plan and the original specification containing the 48 skills.
3. Locate the previous definition/tests/reports for Core-8 in repository history/current tree. Do NOT invent a new Core-8 list if an authoritative existing list exists.
4. Read the latest reports, especially `qa_reports/AS21_OFFICE_ATTACHMENTS_VISIBILITY_RETEST_010B.md`.
5. Fix the known stale test mock from 010B first: `test_get_task_requires_exact_key_not_first_search_hit_and_no_q` must understand the attachment metadata call. Production behavior must not be reverted.
6. Run targeted adapter tests and full regression. Record baseline and current counts.

## Source-of-truth rules
- Real AS21 is read through MCP-SWTR / swtr-read production path.
- No AS21 mutations.
- Do not substitute fixtures/mocks for real-data acceptance evidence.
- Synthetic tests are allowed only for edge cases for which no real sample is available; label them explicitly.
- Preserve exact-task semantics: never accept a first search hit as proof for an exact key.
- Preserve canonical Task mapping and explicit filtering contracts restored in prior stages.
- Attachments are part of canonical task richness. WMB-30000 is the proven real attachment reference (5 XLSX files as of 010B).

## Phase A — Recover authoritative Core-8
Search repository files AND git history for the exact eight capabilities previously selected/tested for Harness. Produce a table:
`ID | skill/capability | original 48-skill mapping | production entry point | required AS21 attributes | prior test/report evidence`.

If current implementation terminology differs from the original specification, map old -> new explicitly. Any missing capability is a finding, not permission to redefine Core-8.

## Phase B — Real AS21 capability matrix
For each recovered Core-8 capability, execute at least:
- one positive real-data case;
- one negative/empty or false-green case where meaningful;
- verification of evidence/source facts;
- verification that required canonical attributes survive mapping.

Use known real anchors where applicable:
- WMB space and `WMB-30000` for exact task + attachment richness;
- DMS and OLP spaces for team/sprint-oriented checks;
- real team-member identities from the repository's team list, not invented users;
- existing real examples already proven in previous QA reports may be reused, but rerun them now.

For task filtering, explicitly cover combinations required by Core-8, including when relevant:
- space/project;
- assignee;
- status;
- sprint;
- release/version;
- exact task key.
Verify AND semantics for combined filters and fail-closed behavior for unknown values.

## Phase C — Attribute contract audit
Do NOT attempt to expose every raw AS21 field merely because it exists. Instead build an attribute coverage matrix driven by the Core-8 skills:
`canonical field | AS21/SWTR source path | extractor | skills consuming it | real sample | status`.

At minimum audit fields needed by the recovered Core-8: key/source_id, title/summary, description where required, status/workflow status, space/project, assignee display identity + stable external/login id, sprint, release/version, attachments metadata, and any other field actually required by a Core-8 capability.

For user-valued SWTR attributes verify nested `swtr_attributes[].value.externalId` extraction. For sprint/release verify the actual real source attribute paths rather than assumptions.

## Phase D — Core-8 end-to-end through PO Agent
Adapter-only success is insufficient. Run each Core-8 scenario through the actual PO Agent/Harness production request path. Where semantic interpretation requires an LLM, report separately:
1. deterministic/adaptor capability result;
2. semantic interpretation result;
3. final agent answer/evidence.

Do not call a capability GREEN if only a direct adapter script works but the agent-facing path fails.

If `/api/v1/query` fails because the LLM is unconfigured, treat this as an integration blocker for semantic E2E, not as an AS21 adapter failure. Determine the repository-supported LLM configuration contract from code/docs; do not invent secrets or commit credentials.

## Phase E — False-green/adversarial attacks
At minimum test:
- nonexistent task key;
- nonexistent assignee;
- nonexistent project/space;
- nonexistent sprint;
- unsupported/unknown filter field;
- contradictory combined filters;
- exact-key lookup cannot return a different search hit;
- attachment metadata from another task cannot leak into target task;
- no AS21 writes/mutations.

## Phase F — Regression gates
Run:
1. targeted Core-8 tests;
2. AS21 adapter/source-contract tests;
3. Harness tests relevant to Core-8;
4. full project regression.

No unexplained new regression is acceptable. If a test is stale, update the test/mock to the production contract and prove why; do not merely waive it in the report.

## Required report
Publish `qa_reports/CORE8_REAL_AS21_BASELINE_011.md` and commit/push it.

Report sections:
1. Executive verdict
2. Branch/HEAD/environment
3. Recovered authoritative Core-8 table
4. Original 48-skill traceability
5. Real AS21 test dataset/anchors
6. Attribute coverage matrix
7. Results for each Core-8 capability
8. Agent-facing E2E results
9. Semantic/LLM configuration status
10. False-green attacks
11. Regression results
12. Bugs/fixes/commits made during 011
13. Architecture findings
14. Gate decision
15. Machine-readable summary

## Gate
Set `READY_FOR_LEARNING_LOOP_012 = YES` only if ALL are true:
- authoritative Core-8 recovered and traceable to original specification;
- 8/8 capabilities pass on real AS21 through their required production path;
- required attribute mapping is proven on real data;
- agent-facing E2E is GREEN for all scenarios that require it;
- semantic layer required by those scenarios is operational;
- false-green attacks pass;
- no unexplained new regressions;
- AS21 mutations = 0.

Otherwise set NO and list exact blockers with severity and owner/component.

Machine-readable footer must include:
```
ASSIGNMENT_ID = CORE8_REAL_AS21_BASELINE_011
CORE8_RECOVERED = <n>/8
CORE8_REAL_DATA_PASS = <n>/8
CORE8_AGENT_E2E_PASS = <n>/8
CORE8_ATTRIBUTE_CONTRACT_PASS = YES|NO
SEMANTIC_LAYER_OPERATIONAL = YES|NO|NOT_REQUIRED
FALSE_GREEN_ATTACKS_PASS = YES|NO
NEW_CODE_REGRESSIONS_VS_PREVIOUS_GREEN = <n>
AS21_MUTATIONS_DURING_TEST = <n>
BLOCKER_COUNT = <n>
READY_FOR_LEARNING_LOOP_012 = YES|NO
```

## Important sequencing
Do not start modifying Learning Loop behavior in this assignment. 011 establishes the trusted Core-8 baseline. Learning Loop verification/improvement is the next gate only after 011 is GREEN.