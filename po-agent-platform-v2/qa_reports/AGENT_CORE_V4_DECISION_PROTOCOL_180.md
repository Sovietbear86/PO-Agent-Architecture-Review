# Assignment 180 — Agent Core v4 Decision Protocol Reliability

**Verdict: `V4_DECISION_PROTOCOL_RELIABILITY_RED`**

**Date:** 2026-09-11
**QA role:** tester/adversarial reviewer only (no production/backend/frontend/test code, prompts, model config, skill registry, or learning data modified)
**Branch:** `feat/core8-real-query-hardening-v2`
**Test base HEAD:** `cf657ce89d925e63deac03653bd5fd705a1a3cb1`
**Owner commits under test (all verified as ancestors of HEAD):**
- `54371e57f73543f52102994746488fe5bc42d74a` — `feat(v4): add provider-robust planner decision protocol` (new `agent_core_v4_robust.py`: `RobustSkillNativePlannerV4` JSON-primary + typed DSL `LOAD`/`CALL`/`READY` recovery; `RobustReliableAgentCoreV4Runtime`)
- `b29ce9f4eb856287d65c0fd76ff7e46826945761` — `feat(v4): wire provider-robust planner runtime` (runtime factory instantiates `RobustReliableAgentCoreV4Runtime` when V4 enabled)
- `1a1c2d38211fc18035baf4fd2a5e099b3856e558` — `test(v4): cover robust JSON and DSL decision decoding`

**Runtime under test:**
- Model/provider: `Qwen/Qwen3.8-27B` (unchanged, per rules)
- Env: `PO_AGENT_AGENT_CORE_V4_ENABLED=true`, `PO_AGENT_AS21_MODE=task-api`
- PO Agent: **fresh instance on `127.0.0.1:8007`** started from current HEAD `cf657ce`
  (health: `agent_core_v4_enabled:true, agent_core_v4_ready:true, adapter:task-api, source_status:healthy`)
- Task API: `127.0.0.1:8003` (shared, healthy) — `swtr-read` connected to MCP-SWTR (SSE, 48 tools)
- MCP-SWTR (Oracle B): `127.0.0.1:3000/sse` → REAL AS21
- Concurrency: 1. Source timeout ≥ 300 s. Long agent call ≤ 600 s. Fresh runtime session per run.

---

## 0. Retained checkpoints (not re-run, no fresh contradicting evidence)

Per the assignment checkpoint: V4 raw-query/progressive-skill architecture active and
semantic-prepass absent (`semantic_prepass_used=false` confirmed in every Phase 1 run);
task.lookup source-backed canonical assignee fields correct (re-verified live: DMS-380
→ `assignee_login=semavin.m.m`, `assignee_id=Semavin.M.M`); canonical literal/observation
binding accepted when the planner emits a valid decision (Phase 0 item 5 + retained 179);
`sprint.current` REAL swtr-read GREEN (retained); Garanin/Moiseev Oracle-exact searches
(retained); PVM-Guru terminal behavior (retained); `Гарановых` false-positive closed
(retained); cross-skill source handlers other than the decision transport retained.

Stale runtime rule honored: Assignment 179 instance (port 8006, previous HEAD) was **not**
reused. A fresh PO Agent was started from `cf657ce` on port 8007; all Phase 1 Agent A
traffic went to it.

---

## 1. Phase 0 — Build/unit/static gate → GREEN

**Unit tests:** `pytest tests/test_agent_core_v4_robust_protocol.py
tests/test_agent_core_v4_reliable.py tests/test_agent_core_v4_skill_native.py` → **18/18 passed**
(7 new robust-protocol tests: DSL LOAD/CALL/READY decoding, multi-word quoted values,
multi-line rejection, malformed-JSON → DSL recovery on 2nd attempt, non-hardcoded
second-step CALL recovery).

**Static/governance gate (script `qa_180_p0_static.py`): 7/7 PASS**
1. Factory wires `RobustReliableAgentCoreV4Runtime` as the production V4 runtime when the
   flag is enabled; constructed runtime's planner is `RobustSkillNativePlannerV4`. PASS
2. Valid JSON decision decodes as the **primary** protocol (`_decode_any` tries
   `_extract_json_object` before `_decode_dsl`; JSON decision carries the model's own
   rationale, not `dsl_recovery`). PASS
3. Malformed JSON recovers through the generic typed DSL on the 2nd bounded attempt. PASS
4. DSL decisions convert to ordinary `V4Decision` objects (`kind`/`capability_id`/
   `arguments` typed, `arguments: Mapping[str, str]` — contract-consistent with JSON path). PASS
5. A DSL `CALL` **cannot** invoke a capability that has not been loaded:
   `capability_not_loaded:task.search` (nothing loaded) and unknown `task.invent`
   both rejected through all 4 bounded attempts → `V4ContractError`. PASS
6. No person/sprint/space/task/trajectory-specific fallback in the robust module:
   zero entity literals (Garanin/Semavin/Moiseev/DMS-/OLP-/SPRNT/Гаранин/Моисеев/…),
   zero trajectory-specific routing branches. PASS
7. No semantic-prepass dependency in the robust module; whitespace-ignoring diff
   `a5e5d91..HEAD` over src+tests adds zero semantic-prepass/semantic-interpreter
   references (the only substantive factory delta is the robust runtime import/instantiation). PASS

Phase 0 verdict: **GREEN** — the build gate does not trip `V4_DECISION_PROTOCOL_BUILD_RED`.

---

## 2. Phase 1 — Critical 10× decision-reliability gate → RED (0/10)

### 2.1 Oracle B (refreshed, REAL AS21 only)

Script `qa_180_p1_oracle.py` (direct MCP-SWTR + task-api `swtr-read` live read-through
cross-check; TQL `assigned_to = "Semavin.M.M"`, paged):

- **DMS-380** (REAL source): space `DMS`, status `Тестирование` (QA), sprint `DMS-SPRNT-2`,
  assignee **`Semavin.M.M`** (login `semavin.m.m`, display `Семавин Михаил Михайлович`).
  Direct MCP `get_task`/`read_unit` for DMS-380 remained flaky (known 179 behavior —
  `get_task` by code returned a foreign unit `SOLT-147558`); the reliable REAL path is
  task-api `swtr-read` get_task, and the two REAL sources **agree on the assignee**.
- **Assignee task collection (Oracle B):** `assigned_to = "Semavin.M.M"` →
  **306 tasks, all in approved spaces** (`DMS`, `OLP`, `STS`). Matches the 179 checkpoint.
- Output: `qa_180_p1_oracle.json` (306 keys).

### 2.2 10 independent fresh sessions — `Покажи DMS-380 и затем задачи его исполнителя`

**Result: 0/10 terminally correct; 0/306 exact parity in every run.**

| run | status | prepass | loaded skill(s) | trajectory (decode source) | keys | latency |
|-----|--------|---------|-----------------|---------------------------|------|---------|
| 1–10 (all) | COMPLETED | false | `tasks.lookup_then_assignee` | 1: `load_skill` (JSON) → 2: `task.lookup task_key=DMS-380` (JSON) → 3: **`ready` (DSL)** | **0/306** | 21.8–54.6 s |

Every run: planner loads `tasks.lookup_then_assignee` (planner-selected, not hardcoded),
performs the REAL `task.lookup`, then **terminates with `READY` at turn 3 without ever
calling `task.search`**. The terminal answer is a confident, incomplete DMS-380 summary
(e.g. run 1: "Задача находится на этапе тестирования и закреплена за Семавиным М. М. в
спринте DMS-SPRNT-2") — no mention of the 306 assignee tasks.

Evidence hygiene note: during this batch a duplicate runner process was briefly running
concurrently (launcher error, killed after run 2). Runs 1–2 therefore had a short
concurrent overlap; runs 3–10 are clean sequential. All 10 runs show the **identical
deterministic pattern** (temperature 0), so the batch is valid evidence; the overlap is
disclosed.

### 2.3 Exact first failing boundary (captured)

The first failing boundary is **turn 3 of the planner loop** — the decision following the
`task.lookup` observation. Raw-output probe (`qa_180_p1_rawturn3.py`, production wiring
`settings → RealLLMClient → LLMJsonSemanticInterpreter → build_runtime_bundle →
RobustReliableAgentCoreV4Runtime`, in-process capture wrapper; 3 independent rounds, all
identical):

State at the boundary:
- `user_query = "Покажи DMS-380 и затем задачи его исполнителя"`
- `loaded_skills = ("tasks.lookup_then_assignee",)` — its declared procedure: *"Call
  task.lookup for the user-supplied task key. Use the authoritative assignee from the
  observation, never infer a person from prose. Call task.search for that assignee…"*
- observation 1 = REAL `task.lookup DMS-380` with `data.assignee_login = "semavin.m.m"`,
  `data.assignee_id = "Semavin.M.M"` (canonical, trusted — the observation the model
  should bind to)

**Raw planner output, every round (2 bounded LLM calls):**

Attempt 1 (1631 chars) — the model does not emit any decision; it writes a free-form
bug-analysis essay about the DMS-380 *description* (a TLS/ClickHouse error report):

```
# Анализ бага: SSL-ошибка в ClickHouse JDBC

## Суть проблемы

Приложение не может установить соединение с ClickHouse через JDBC из-за **сбоя TLS-рукопожатия**.

## Цепочка корневой причины

```
javax.net.ssl.SSLException: Unsupported or unrecognized SSL message
  ← SSLSocketInputRecord.handleUnknownRecord()
    ← SSLSocketImpl.startHandshake()
...
| # | Причина | Вероятность |
|---|---------|-------------|
| 1 | ClickHouse-сервер **не настроен на SSL**, а клиент пытается использовать `ssl=true` | Высокая |
...
```

→ `_decode_any`: no JSON object, no `LOAD`/`CALL`/`READY` line → undecoded
(`invalid_json_and_dsl_decision`) → `DSL_REPAIR` nudge sent.

Attempt 2 (160 chars) — the model complies with the repair nudge, which offers
`READY <short answer>`, and emits exactly one DSL line:

```
READY SSL handshake failure: ClickHouse server likely not configured for TLS while JDBC client uses ssl=true; verify connection string and server https config
```

→ `_decode_dsl` accepts it: `V4Decision("ready", answer="SSL handshake failure: …",
rationale="dsl_recovery")` → `_decision_allowed` passes (ready is always allowed) →
**loop returns COMPLETED** with the synthesized DMS-380-only answer. `task.search` is
never called; the assignee's 306 tasks are never fetched.

### 2.4 Causal A/B proof — the robust protocol itself changed the turn-3 behavior

Probe `qa_180_p1_ab_probe.py`: **identical turn-3 state** (same adapter, catalog, loaded
skill, same REAL task.lookup observation, same model, temperature 0) but with the
Assignment-179 runtime `ReliableAgentCoreV4Runtime` (JSON-only `SkillNativePlannerV4`,
no DSL addendum, no DSL repair):

**All 3 rounds, single LLM call each, valid JSON, correct trajectory continuation:**

```json
{"load_skill":null,
 "call":{"capability_id":"task.search","arguments":{"assignee":"semavin.m.m"}},
 "ready":null,
 "rationale":"Task DMS-380 is already resolved (observation step 1). Its assignee is
 semavin.m.m. Now I need to search for all tasks assigned to this person to fulfill the
 second part of the user's request."}
```

→ decodes to `call task.search assignee=semavin.m.m` — the correct, source-safe next
step, bound to the trusted observation value (the exact call that produced 306/306 in
179 when the planner emitted valid JSON).

**Conclusion:** the only delta between A (180 robust) and B (179 JSON-only) is the
decision-transport layer introduced by `54371e5` — `DSL_SYSTEM_ADDENDUM` (always present
in the system prompt, presenting `READY <short answer>` as a first-class one-liner) and
`DSL_REPAIR` (explicitly offering `READY` as a recovery option). Under that framing the
same model at the same state (a) derails into a free-form analysis of the task
description instead of emitting the follow-on capability call, and (b) on the repair
nudge emits a one-line `READY` that the decoder accepts as a legitimate terminal
decision. The JSON-only framing keeps the model on the action path and emits the correct
`task.search` call in one shot, 3/3.

### 2.5 Defect characterization

This is a **new production defect introduced by the robust decision protocol** (not
present in the 179 runtime):

1. The DSL recovery channel can **mint an accepted terminal `READY` decision**. A `READY`
   line is structurally indistinguishable from a legitimate "trajectory complete"
   decision, so governance (`_decision_allowed`) accepts it. In the 179 protocol the same
   model derailment produced a malformed JSON *call attempt* → `invalid_json_decision` ×3
   → `V4ContractError` → **FAILED (fail-closed)**. In the 180 protocol it produces a
   clean one-line `READY` → **COMPLETED with a confident, incomplete answer (fail-open)**.
2. The always-on `DSL_SYSTEM_ADDENDUM` shifts the planner's decision framing: 10/10
   production runs and 3/3 probes terminated early at turn 3 (0/306), whereas the A/B
   control (179 framing) continued correctly 3/3.

Phase 1 RED triggers (assignment): *task collection differs from Oracle B* (0 vs 306 in
all 10 runs). The transport itself works (JSON primary decodes, DSL decodes, bounded
repair functions, capability gating intact per Phase 0 item 5) — the failure is the
protocol's decision-reliability behavior, not the source, binding, or adapter.

Per the assignment's first-new-defect rule, execution **STOPs here**: Phases 2–4
(generalization, safety, regression) were **not run** and are recorded as skipped.

---

## 3. Verdict and required owner fix

**Verdict: `V4_DECISION_PROTOCOL_RELIABILITY_RED`**

- Phase 0: GREEN (7/7 static + 18/18 unit).
- Phase 1: **0/10** (acceptance = 10/10 terminally correct + exact Oracle parity).
- Root cause is in the robust decision protocol's prompt/decoder surface (the `READY`
  channel in the always-on addendum and in the repair nudge), proven causally by the A/B
  probe; it deterministically converts the mandatory benchmark into a fail-open,
  confidently incomplete COMPLETED.

**Smallest generalized owner fix (no surname/phrase/semantic-prepass/trajectory rules):**

1. **`READY` must not be offered as a recovery serialization.** In `DSL_REPAIR` (and,
   preferably, out of the always-on `DSL_SYSTEM_ADDENDUM`), present only `LOAD` and
   `CALL` as recovery options. Recovery's job is to restore an *action* after a broken
   serialization; it must not mint a terminal decision. `READY` remains fully available
   as a **primary** decision (JSON or DSL on attempt 1) when the model genuinely has
   completed the trajectory.
2. **Defense in depth in `RobustSkillNativePlannerV4.next_decision`:** on repair attempts
   (attempt ≥ 2), reject `ready` decisions decoded via `dsl_recovery`
   (failure tag e.g. `recovery_ready_not_permitted`) and continue the bounded loop;
   accept `ready` via the primary attempt only. This is trajectory-agnostic: it applies
   uniformly to every capability/skill and changes no entity, binding, or source
   semantics.

This keeps the genuinely good part of the owner fix (LOAD/CALL transport hardening that
survives malformed JSON) while removing the fail-open early-exit the A/B probe
demonstrates. After the fix, this assignment's Phase 1 gate (10× DMS-380 two-step,
10/10 exact against the refreshed 306-key Oracle B) plus Phases 2–4 must be re-run.

---

## 4. Evidence artifacts (local, untracked)

- `qa_180_p0_static.py` — Phase 0 7-item gate (7/7 PASS)
- `qa_180_p1_oracle.py` / `qa_180_p1_oracle.json` — Oracle B refresh (DMS-380 → Semavin.M.M; 306 keys)
- `qa_180_p1_runner.py` / `qa_180_p1_results.json` — 10× Phase 1 batch (0/10, per-run trajectory + decode source)
- `qa_180_p1_rawturn3.py` / `po-agent-platform-v2/qa_180_p1_rawturn3.json` — raw turn-3 planner outputs, 3 rounds (essay → `READY` via dsl_recovery)
- `qa_180_p1_ab_probe.py` / `po-agent-platform-v2/qa_180_p1_ab_probe.json` — A/B causal probe (179 JSON-only runtime: 3/3 correct `task.search` call, single LLM call)

**Git:** this report is the only committed file. STOP — no further phases, no next assignment.