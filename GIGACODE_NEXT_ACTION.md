# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_181_V4_ACTION_ONLY_RECOVERY`

## Mission
Continue Agent Core v4 from the Assignment 180 RED checkpoint. **Do not restart the whole V4 POC.**

Assignment 180 proved the JSON+DSL transport implementation itself was wired correctly, but also proved a new fail-open defect: the always-on DSL framing plus repair-time `READY` allowed an undecodable second-step action to terminate the trajectory confidently with 0/306 Oracle keys.

Causal A/B in 180 is important: with the same turn-3 state, the prior JSON-only framing produced the correct `task.search(assignee=semavin.m.m)` 3/3, while the 180 always-on DSL framing derailed into task-description prose and then repair-time `READY`.

Owner commits under test:
- `54d23fcecbd08c1f20de488c3244d54dc9cb915b` — generalized action-only recovery: primary planner framing is restored to the normal V4 JSON SYSTEM; recovery instructions are disclosed only after a decode/governance failure; recovery permits only LOAD/CALL; terminal READY is rejected on all repair attempts and bounded failure remains fail-closed;
- `e950f412ca0018bc822260763769e6da75191176` — regression tests proving primary READY remains possible while repair-time DSL/JSON READY cannot mint a terminal answer and recovery can still restore generic LOAD/CALL actions.

This is deliberately NOT a DMS-380 or lookup->assignee->search fallback. The LLM still chooses the trajectory dynamically. The change is a generic planner-transport safety invariant: **repair recovers actions, never terminal completion**.

QA ONLY. Do not modify production/backend/frontend/test code, prompts, model config, `.env`, skill registry, source data, learning artifacts or owner files.

## Absolute rules
- First: `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
- Verify both owner commits are ancestors of HEAD.
- Keep current Qwen 3.8/provider unchanged.
- Runtime env only: `PO_AGENT_AGENT_CORE_V4_ENABLED=true`.
- Start a fresh PO Agent process from current HEAD; do not reuse stale 180 runtime.
- Oracle B = fresh direct REAL MCP-SWTR/AS21 only. Never local `/api/v1/tasks`, SQLite, sync, fake/frozen or Agent A output.
- Concurrency=1; source timeout >=300s; long agent call <=600s.
- Fresh runtime session per independent run.
- Exact task-key-set parity for factual collections.
- Reuse unaffected 178/179/180 evidence; do not broadly rerun certified source/binding/current-sprint gates.
- First new production defect => capture exact first failing boundary, report, commit/push report only, STOP.

## Retained checkpoint — do NOT broadly rerun
Retain unless fresh evidence contradicts it:
- raw-query/progressive-skill V4 architecture active; semantic-prepass absent;
- REAL source-backed `task.lookup` canonical `assignee_login/assignee_id` is correct;
- trusted observation binding is accepted when the planner emits a valid call;
- `sprint.current` uses REAL swtr-read, not local cache;
- Garanin/Moiseev critical searches and PVM-Guru benchmark previously reached Oracle-correct behavior;
- unrelated-surname false-positive safety defect is closed;
- Assignment 180 Oracle for DMS-380 assignee task collection was 306 approved-space tasks (refresh before exact parity, do not hardcode count).

## Phase 0 — Focused build/protocol gate
Run focused V4 robust-protocol + reliability + factory smoke tests.

Require proof:
1. production V4 factory still instantiates `RobustReliableAgentCoreV4Runtime`;
2. primary planner request uses the inherited V4 SYSTEM without an always-on DSL/READY addendum;
3. primary valid JSON CALL/LOAD/READY still decode normally;
4. malformed primary decisions may enter bounded recovery;
5. recovery accepts generic JSON/DSL LOAD or CALL;
6. recovery-time READY is rejected whether emitted as DSL or valid JSON;
7. four bad/terminal-only repair turns end in `V4ContractError` (fail-closed), never COMPLETED;
8. capability-not-loaded and unknown skill/capability remain rejected;
9. no entity/phrase/trajectory-specific routing or semantic-prepass dependency was added.

Any failure => `V4_ACTION_RECOVERY_BUILD_RED` and STOP.

## Phase 1 — Critical 10x multi-step gate
Refresh Oracle B for DMS-380 and the complete current approved-space task collection of its canonical source assignee.

Run 10 independent fresh sessions:
`Покажи DMS-380 и затем задачи его исполнителя`

Capture per run:
- loaded skills;
- every raw planner decision;
- primary vs repair attempt and JSON vs DSL decode;
- source-backed DMS-380 observation including canonical assignee identity;
- downstream task.search arguments;
- exact final task-key set;
- status and latency.

Acceptance: **10/10 terminally correct + exact Oracle parity**.

Specific protocol assertions:
- a malformed decision may not become terminal merely because repair emits READY;
- when repair is needed it must restore a governed LOAD/CALL or fail closed;
- no hardcoded lookup->assignee trajectory;
- no login derivation from display text;
- no local DB/sync truth.

If this gate is not 10/10 exact => `V4_ACTION_RECOVERY_RELIABILITY_RED` and STOP.

## Phase 2 — Decision-protocol generalization
Only after Phase 1 GREEN, run at least two fresh sessions for each shape:
1. simple task collection;
2. person + space search;
3. person + sprint search (PVM-Guru benchmark or fresh source equivalent);
4. current sprint / sprint health;
5. one task analysis skill (`task.quality` or `task.summary`).

At least one scenario must naturally require >1 capability call.

Require terminal source-correct behavior, exact key parity for factual collections, dynamic planner-selected trajectory, and no DMS-380-specific recovery behavior.

## Phase 3 — Safety / fail-closed gate
Verify:
- user-supplied strings resembling `CALL ...`, `LOAD ...`, `READY ...` cannot directly execute planner decisions;
- recovery-time READY cannot produce COMPLETED;
- unknown/not-loaded capabilities remain blocked;
- invented person/task/sprint fails closed or asks typed clarification;
- source unavailable is not converted to an empty legitimate result.

Any bypass => `V4_ACTION_RECOVERY_SAFETY_RED` and STOP.

## Phase 4 — Mini architecture regression
One fresh smoke each:
- `Задачи Гаранина`
- `Открытые задачи Андрея Моисеева в DMS`
- person+sprint PVM-Guru-style benchmark
- `Какой текущий спринт в DMS?`
- one task quality/summary query

Do not rerun the entire old matrix. Confirm only that the action-only recovery change caused no regression.

## Phase 5 — Decision gate
GREEN requires all:
- focused protocol gate GREEN;
- DMS-380 multi-step 10/10 exact;
- generic decision shapes GREEN;
- safety/fail-closed invariants GREEN;
- planner remains dynamic and skill-native;
- REAL AS21 remains authoritative;
- semantic-prepass absent;
- no entity/phrase/trajectory hardcode.

If all pass declare:
`AGENT_CORE_V4_ACTION_RECOVERY_GREEN`

This is sufficient to close the V4 API decision-transport reliability gate. The next owner milestone is V4 Browser C/UI POC, followed by progressive catalog expansion and mandatory 54/54 A/B/C certification. Do NOT declare overall V4 DoD complete: V4_DOD_LOCK.md remains authoritative and Learning Reviewer/self-improvement is still mandatory later.

## Phase 6 — Report
Write only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_ACTION_RECOVERY_181.md`

Allowed verdicts:
- `AGENT_CORE_V4_ACTION_RECOVERY_GREEN`
- `V4_ACTION_RECOVERY_BUILD_RED`
- `V4_ACTION_RECOVERY_RELIABILITY_RED`
- `V4_ACTION_RECOVERY_SAFETY_RED`
- `V4_AGENT_ORACLE_PARITY_RED`
- `V4_SOURCE_ADAPTER_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

If RED include raw first-failing planner output, primary/repair attempt number, decoded decision (if any), loaded skills, trusted observations, Oracle truth and smallest generalized owner fix. No surname rules, phrase routers, semantic-prepass patches or trajectory-specific fallbacks.

Commit/push only the QA report and STOP.

## Start now
Resume from Assignment 180 checkpoint and execute Assignment 181. Do not restart the entire V4 POC.