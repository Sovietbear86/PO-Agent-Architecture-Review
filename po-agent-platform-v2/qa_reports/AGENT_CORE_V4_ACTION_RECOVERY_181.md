# Assignment 181 — Agent Core v4 Action-Only Recovery

**Verdict: `V4_ACTION_RECOVERY_RELIABILITY_RED`**

**Date:** 2026-09-11
**QA role:** tester/adversarial reviewer only (no production/backend/frontend/test code, prompts, model config, skill registry, or learning data modified)
**Branch:** `feat/core8-real-query-hardening-v2`
**Test base HEAD:** `0cf2ee2542848f74c4cdc993373d0c627990b349`
**Owner commits under test (both verified as ancestors of HEAD):**
- `54d23fcecbd08c1f20de488c3244d54dc9cb915b` — `fix(v4): keep recovery action-only and fail closed` (primary framing restored to the inherited V4 JSON SYSTEM; recovery disclosed only after a decode/governance failure; recovery permits only LOAD/CALL; terminal READY rejected on all repair attempts; bounded failure stays fail-closed)
- `e950f412ca0018bc822260763769e6da75191176` — `test(v4): reject terminal ready during recovery` (primary READY still possible; repair-time DSL/JSON READY cannot mint a terminal; recovery still restores generic LOAD/CALL)

**Runtime under test:**
- Model/provider: `Qwen/Qwen3.8-27B` (unchanged, per rules)
- Env: `PO_AGENT_AGENT_CORE_V4_ENABLED=true`, `PO_AGENT_AS21_MODE=task-api`
- PO Agent: **fresh instance on `127.0.0.1:8008`** started from current HEAD `0cf2ee2`
  (health: `agent_core_v4_enabled:true, agent_core_v4_ready:true, adapter:task-api, source_status:healthy`)
- Task API: `127.0.0.1:8003` (shared, healthy) — `swtr-read` connected to MCP-SWTR (SSE, 48 tools)
- MCP-SWTR (Oracle B): `127.0.0.1:3000/sse` → REAL AS21
- Concurrency: 1. Source timeout ≥ 300 s. Long agent call ≤ 600 s. Fresh runtime session per run.

**Stale-runtime rule honored:** the Assignment 180 instance (port 8007, previous HEAD) was not reused;
a fresh PO Agent was started from `0cf2ee2` on port 8008.

---

## 0. Retained checkpoints (not re-run, no fresh contradicting evidence)

Per the assignment checkpoint: raw-query/progressive-skill V4 architecture active and
semantic-prepass absent (`semantic_prepass_used=false` in every Phase 1 run); REAL
source-backed `task.lookup` canonical `assignee_login/assignee_id` correct (re-verified live:
DMS-380 → `assignee_login=semavin.m.m`, `assignee_id=Semavin.M.M`); trusted observation
binding accepted when the planner emits a valid call; `sprint.current` uses REAL swtr-read
(retained); Garanin/Moiseev critical searches and PVM-Guru benchmark previously Oracle-correct
(retained); unrelated-surname false-positive closed (retained). The 180 Oracle for the DMS-380
assignee collection (306 approved-space tasks) was **refreshed** (below) rather than hardcoded.

---

## 1. Phase 0 — Focused build/protocol gate → GREEN

**Unit tests:** `pytest tests/test_agent_core_v4_robust_protocol.py
tests/test_agent_core_v4_reliable.py tests/test_agent_core_v4_skill_native.py` → **21/21 passed**
(includes the 4 new `e950f41` regression tests: primary DSL READY still decodable, recovery
DSL READY not decodable, repair-READY cannot turn a malformed action into a completed answer,
repair-only-READY fails closed).

**Static/behavioral gate (script `qa_181_p0_static.py`): 9/9 PASS**
1. Factory instantiates `RobustReliableAgentCoreV4Runtime`; constructed planner is `RobustSkillNativePlannerV4`. PASS
2. Primary planner request uses the **inherited V4 SYSTEM** — no always-on DSL/READY addendum
   (`DSL_SYSTEM_ADDENDUM` removed; primary system message is exactly `self.SYSTEM`); a valid
   primary JSON `call` decodes with the model's own rationale (not `dsl_recovery`). PASS
3. Primary valid JSON `LOAD`/`CALL`/`READY` all decode normally. PASS
4. A malformed primary enters bounded recovery (repair nudge appended, action recovered via DSL). PASS
5. Recovery accepts generic DSL and JSON `LOAD`/`CALL` actions. PASS
6. **Recovery-time READY is rejected whether emitted as DSL or valid JSON** (`_decode_any(allow_ready=False)`
   returns None for both); primary READY is still decodable. PASS
7. Four bad/terminal-only repair turns end in `V4ContractError` — **fail-closed, never COMPLETED**:
   `planner failed robust bounded repair: ['invalid_primary_decision','invalid_recovery_action','invalid_recovery_action','invalid_recovery_action']`. PASS
8. Capability-not-loaded and unknown skill/capability remain rejected. PASS
9. No entity/phrase/trajectory-specific routing or semantic-prepass dependency added (whitespace-ignoring
   diff `dacc42f..HEAD` over src+tests adds zero prepass/interpreter references; zero entity literals;
   zero trajectory routing branches). PASS

Phase 0 verdict: **GREEN** — does not trip `V4_ACTION_RECOVERY_BUILD_RED`.

---

## 2. Phase 1 — Critical 10× multi-step gate → RED (8/10)

### 2.1 Oracle B (refreshed, REAL AS21 only)

Script `qa_181_p1_oracle.py` (direct MCP-SWTR + task-api `swtr-read` live read-through
cross-check; TQL `assigned_to = "Semavin.M.M"`, paged):

- **DMS-380** (REAL source): space `DMS`, status `Тестирование` (QA), sprint `DMS-SPRNT-2`,
  assignee **`Semavin.M.M`** (login `semavin.m.m`). The two REAL sources agree on the assignee.
- **Assignee task collection (Oracle B):** `assigned_to = "Semavin.M.M"` → **306 tasks, all in
  approved spaces** (`DMS`, `OLP`, `STS`). Output: `qa_181_p1_oracle.json`.

### 2.2 10 independent fresh sessions — `Покажи DMS-380 и затем задачи его исполнителя`

**Result: 8/10 terminally correct with exact 306/306 Oracle parity; 2/10 `NEEDS_CLARIFICATION`
(0/306). Not 10/10 → gate RED.**

| run | status | parity | trajectory (decode) | terminal |
|-----|--------|--------|---------------------|----------|
| 1,2,3,4,6,8,9,10 | COMPLETED | **306/306** | load `tasks.lookup_then_assignee` (JSON) → `task.lookup DMS-380` (JSON) → `task.search assignee=semavin.m.m` (JSON) → `ready` (JSON) | `ready` / JSON |
| 5,7 | NEEDS_CLARIFICATION | 0/306 | load `tasks.lookup_then_assignee` (JSON) → `task.lookup DMS-380` (JSON) → **`task.lookup` via DSL (wrong capability, no `task_key`)** | `call` / DSL |

Tally: `8 × (COMPLETED, ready, JSON-terminal)` + `2 × (NEEDS_CLARIFICATION, call, DSL)`.

### 2.3 The Assignment-180 fail-open defect is CONFIRMED FIXED

- **No run minted a terminal via a DSL/recovery path.** The 8 correct runs terminate with a
  **JSON `ready`**; the 2 failing runs terminate on a **`call` action** (a legal recovery action),
  not a `ready`. The `any_terminal_via_dsl` flag is set only because the 2 failures' *last step* is
  a DSL-decoded `call` — an action, not a terminal completion.
- **No 0-key `COMPLETED` exists** (the 180 signature). The specific 180 bug — a malformed
  second-step action terminating the trajectory confidently with `COMPLETED` and 0/306 keys via a
  recovery-minted `READY` — is gone. The action-only invariant (repair recovers actions, never
  terminal completion) holds in all 10 runs.

So the owner's fix did exactly what it set out to do. The gate is RED for a **different, separate**
reason.

### 2.4 Exact first failing boundary (captured)

The failing runs diverge at **turn 3** (the decision following the `task.lookup` observation).
Raw-output probe (`qa_181_p1_rawturn3.py`, current action-only-recovery runtime, in-process capture
wrapper, 8 independent rounds at the identical turn-3 state):

State at the boundary:
- `loaded_skills = ("tasks.lookup_then_assignee",)`
- observation 1 = REAL `task.lookup DMS-380` with `data.assignee_login="semavin.m.m"`,
  `data.assignee_id="Semavin.M.M"`, **and the full unbounded `task.description`** — a ~1416-char
  TLS/ClickHouse error stack trace (`javax.net.ssl.SSLException: Unsupported or unrecognized SSL
  message`, JDBC/`DatamartsClient.getQueryLog` frames, SSL config tables).

**Primary (attempt 1) — malformed in 8/8 probe rounds:** the model does not emit a planner decision;
it writes a free-form bug-analysis essay *about the task description* ("## Анализ ошибки SSL в
ClickHouse JDBC …"). This is undecodable → recovery is triggered (8/8 rounds).

**Recovery (attempts 2–4) — intermittent capability choice:** the model non-deterministically
recovers to one of:
- **correct** `{"call":{"capability_id":"task.search","arguments":{"assignee":"semavin.m.m"}}}` →
  7/8 probe rounds, 8/10 batch runs → 306/306 COMPLETED; **or**
- **wrong** `{"call":{"capability_id":"task.lookup","key":"semavin.m.m"}}` (probe) /
  `CALL task.lookup assignee=Semavin.M.M project=DMS sprint=DMS-SPRINT-2 source=swtr` (batch run5) /
  `CALL task.lookup source=REAL_AS21` (batch run7) → `task.lookup` is a valid, loaded capability so
  governance accepts it, but it is invoked **without a valid `task_key`** → the handler raises
  `V4NeedsClarification("Какую задачу нужно открыть?")` → `NEEDS_CLARIFICATION`, 0 keys.

Probe tally: `('call','task.search',recovery)=7`, `('call','task.lookup',recovery)=1`.
Batch tally: 8 correct / 2 wrong-capability clarification.

### 2.5 Defect characterization

- **Not a protocol bug in the recovery transport.** The action-only invariant is intact; recovery
  correctly refuses terminal READY and correctly restores well-formed actions. Both JSON and DSL
  recovery paths are exercised and both are governed (capability must be loaded).
- **Root cause = model attention reliability at turn 3, surfaced by an unbounded observation
  field.** DMS-380's `description` is a long technical error log; `_compact_data` compacts task
  *collections* but passes the single-task `description` **in full** to the planner. The model is
  reliably captured by it into writing an analysis (malformed primary), then on recovery it usually
  — but not always — re-derives the correct next action. When it re-derives the *wrong* capability
  (`task.lookup` on the assignee instead of `task.search`), it fails closed as a spurious
  clarification.
- **This is not introduced by the owner's action-only fix.** The primary framing is the same
  inherited V4 JSON SYSTEM the 179 runtime used; the description-induced distraction and the
  wrong-capability recovery are model behaviors the fix did not target. The fix correctly resolved
  the specific 180 fail-open defect; it does not, and was not designed to, guarantee 10/10 on a
  query whose source task carries a long distractor description.
- Consequence: the strict 10/10 acceptance is not met (8/10), so the gate is RED and, per the
  assignment's first-new-defect / not-10-of-10 rule, execution **STOPs here**. Phases 2–4
  (generalization, safety, regression) were **not run** and are recorded as skipped.

---

## 3. Verdict and smallest generalized owner fix

**Verdict: `V4_ACTION_RECOVERY_RELIABILITY_RED`**

- Phase 0: GREEN (9/9 static + 21/21 unit).
- Phase 1: **8/10** (acceptance = 10/10 terminally correct + exact Oracle parity).
- The 180 fail-open defect is proven fixed; the action-only recovery invariant is intact.
- The gate fails on a separate, reproducible model-reliability issue at turn 3: an unbounded
  `task.description` in the planner observation distracts the primary into a non-decision essay,
  and recovery then occasionally recovers the wrong capability → spurious clarification.

**Smallest generalized owner fix (no surname rules, phrase routers, semantic-prepass patches, or
trajectory-specific fallbacks):**

1. **Bound the free-text `description` (and similar unstructured fields) in the planner-facing
   `task.lookup` observation.** In `AgentCoreV4Runtime._compact_data`, truncate `task["description"]`
   to a bounded length (or omit it from the planner view while retaining the structured identity
   fields: `key`, `assignee_login`, `assignee_id`, `status`, `sprint_id`). This is an
   **observation-hygiene rule that applies to every `task.lookup` observation**, not to DMS-380
   specifically; it anchors the planner on the structured identity it must bind to, rather than
   feeding it a long error log that pulls it into analysis. This directly removes the primary's
   essay-distractor and should lift the correct-recovery rate toward 10/10.
2. (Secondary, optional) In the recovery prompt, restate that the recovered action must be one of
   the **loaded skill's declared capabilities** and consistent with the trusted observation
   (the model already has both); this is generic and does not name any specific capability as the
   "next" one.

After the fix, this assignment's Phase 1 gate (10× DMS-380 two-step, 10/10 exact against the
refreshed 306-key Oracle B) plus Phases 2–4 must be re-run.

---

## 4. Evidence artifacts (local, untracked)

- `qa_181_p0_static.py` — Phase 0 9-item gate (9/9 PASS)
- `qa_181_p1_oracle.py` / `qa_181_p1_oracle.json` — Oracle B refresh (DMS-380 → Semavin.M.M; 306 keys)
- `qa_181_p1_runner.py` / `qa_181_p1_results.json` — 10× Phase 1 batch (8/10; per-run trajectory +
  JSON/DSL decode + terminal transport)
- `qa_181_p1_rawturn3.py` / `po-agent-platform-v2/qa_181_p1_rawturn3.json` — raw turn-3 primary +
  recovery outputs, 8 rounds (primary essay 8/8; recovery → task.search 7/8, task.lookup 1/8)

**Git:** this report is the only committed file. **STOP** — gate not 10/10; no further phases, no
next assignment.