# A227 UI Parity Pre-Gate — QA Report

**Verdict:** `AGENT_CORE_V4_UI_PARITY_RED_A227_PRE_GATE`
**Classification:** `RED_P0_FOCUSED_V4_TEST_FAILURES` (owner-added core tests fail at START_HEAD)
**START_HEAD:** `3e5b28c3bbedf48d18c9c8d77f8c33350bba4210`
**Branch:** `feat/core8-real-query-hardening-v2`
**Date:** 2026-09-30
**Role:** QA/tester only. No production/frontend/backend/plugin/test/config code was modified.

---

## Summary

P0 (build + focused retained V4/plugin tests) is **RED**. `tsc --noEmit` and `vite build` pass,
and every focused test relevant to **task attachment search / sprint predictability / release forecast**
passes — but **two retained V4 core tests added by the owner in this diff fail at START_HEAD**, and one of
them is *literally the P1 attachment-search scenario*. Per the assignment rule “P0: Any failure => RED STOP”
and the instruction “stop at first RED, return evidence”, the gate stops here. **P1–P4 were not executed.**

---

## P0 — build

### P0.1 worktree / HEAD
- `git pull --ff-only` → already up to date. `START_HEAD = 3e5b28c`.
- `git status --short` → only **untracked QA artifacts** (harness `.mjs`/`.py`/e2e `.spec.ts` from prior
  assignments). **Zero tracked-file modifications** → clean worktree.

### P0.2 frontend build — GREEN
- `npx tsc --noEmit` → **exit 0**, no diagnostics.
- `npx vite build` → **exit 0**; 101 modules transformed;
  `dist/assets/index-*.js` 279.29 kB (gzip 89.63 kB), `index-*.css` 47.56 kB.

### P0.3 focused retained V4/plugin tests — RED (first boundary)

Focused set (attachment search + sprint predictability + release forecast + the two core files the owner
touched this diff):

```
tests/test_agent_core_v4_attachment_sprint_scope.py
tests/test_harness_attachment_skills.py
tests/test_agent_core_v4_wave_s2.py            # sprint.predictability
tests/test_harness_sprint_intelligence.py      # sprint predictability
tests/test_agent_core_v4_batch6_release_forecast.py
tests/test_agent_core_v4_reliable.py           # owner-modified core
tests/test_agent_core_v4_robust_protocol.py    # owner-modified core
→ 2 failed, 50 passed
```

Full V4 blast-radius check (`tests/test_agent_core_v4*.py tests/test_v4*.py`): **2 failed, 231 passed.**
The blast radius is **exactly the two failures below** — nothing else regressed.

---

## Failure D-A227P-1 — `test_agent_core_v4_reliable.py::test_literal_source_status_filters_authoritative_raw_status`

```
tests/test_agent_core_v4_reliable.py:262
    task.status_category = StatusCategory.IN_PROGRESS if normalized else StatusCategory.TODO
E   AttributeError: type object 'StatusCategory' has no attribute 'IN_PROGRESS'
```

**Root cause (test-logic bug, not a production regression).**
The test imports `StatusCategory` from `po_agent.domain.models` (line 6) but references members that do not
exist on that enum. Live enum members (probed at runtime):

```
StatusCategory  = BACKLOG, WAITING, ACTIVE_WORK, REVIEW_QUEUE, REVIEW, QA_QUEUE,
                  TESTING, COMPLETED_PENDING, COMPLETED, CANCELLED, UNKNOWN
TaskStatus      = UNKNOWN, OPEN, NEED_INFO, IN_PROGRESS, READY_FOR_REVIEW, IN_REVIEW,
                  READY_FOR_QA, QA, REOPENED, RESOLVED, CLOSED, CANCELLED
```

`IN_PROGRESS` lives on **`TaskStatus`**, not `StatusCategory`; `TODO` exists on **neither** enum. The test
confuses the two enums.

**Provenance:** the test function is **not present at A227 `db5e35f`** — it was added by the owner in this
diff (`git cat-file -e db5e35f:...reliable.py` → no such def). Owner commit `e81533f test(v4): align status
tests with stable core` was intended to fix the status tests but this one still uses the wrong enum.

**Owner fix:** drive the assertion on the authoritative source field it is named after
(`status_raw` / `status_type`), or use real `StatusCategory` members (e.g. `ACTIVE_WORK` for the in-progress
row, `BACKLOG`/`WAITING` for the other). Do not reference `TaskStatus` members on `StatusCategory`.

---

## Failure D-A227P-2 — `test_agent_core_v4_robust_protocol.py::test_repeated_provider_validation_uses_deterministic_observation_bound_recovery`

```
po_agent.harness.agent_core_v4.V4ContractError:
    planner failed robust bounded repair: ['ValueError', 'ValueError', 'ValueError', 'ValueError']
src/po_agent/harness/agent_core_v4_robust.py:233
```

**Setup:** the test builds a `task.search_attachments` capability + `task-attachments` skill, seeds two
observations (`space.resolve`→WMB, `member.resolve`→Kalachanov.V.V), uses `AlwaysRaisesClient` (LLM raises
on every call) and the exact **P1 attachment query**
`“Открытые задачи Калачанова с вложениями в пространстве WMB”`, then calls
`RobustSkillNativePlannerV4.next_decision(...)` expecting a *deterministic observation-bound recovery*.

**Root cause (contract mismatch — test asserts a behavior the stable core intentionally lacks).**
`agent_core_v4_robust.py` `next_decision` (lines 155–233) has **no** deterministic observation-bound
recovery path. It performs 4 bounded LLM re-attempts; on a provider that always raises it appends
`ValueError` ×4 and, at line 233, **fails closed** with `V4ContractError`. The module docstring is explicit
about this being the intended design:

```
agent_core_v4_robust.py:14-16
    Recovery is deliberately action-only. A repair turn may never manufacture a
    terminal READY decision: if the model cannot recover a valid LOAD/CALL within
    the bounded attempts, the runtime fails closed.
```

So the reverted “stable reliable core” **deliberately fails closed** on repeated provider validation
failure; the newly added test instead asserts a deterministic recovery that does not exist.

**Provenance:** the test function is **not present at A227 `db5e35f`** — added in this diff. Owner commit
`68d95ea test(v4): align robust protocol tests with stable core` did not reconcile this test.

**Owner fix (choose one):**
- (a) **Align the test to the stable-core contract** — assert the fail-closed `V4ContractError` (this
  matches `robust.py:14-16,233`) and rename it accordingly; or
- (b) if deterministic observation-bound recovery is a *required* capability, implement it in the core —
  but that is a Harness/Core change and conflicts with the stated intent to keep the stable reliable core.

---

## P4 — preliminary observation (not executed; flagged for the re-gate)

The owner diff `db5e35f..3e5b28c` **modifies stable Harness/Core files**, which P4 requires to have
“zero new owner changes to stable Harness/Core for this UI correction”:

```
src/po_agent/harness/agent_core_v4.py          |  21 +-
src/po_agent/harness/agent_core_v4_reliable.py |  57 ++++++
src/po_agent/harness/agent_core_v4_robust.py   |  24 +++
src/po_agent/llm/real.py                       |  22 ++-
```

Commit `221f133 revert(v4): keep stable reliable core for A227 UI parity` suggests these are reverts *toward*
the stable core, but they are still net changes vs A227 `db5e35f`. Full P4 (raw-text passthrough, zero phrase
router, zero direct AS21 from frontend, attachment-status plugin ownership) was **not run** per the stop rule —
reconcile during the A227R re-gate.

---

## Phases not executed (stop rule)

- **P1** Tasks UI parity — not run.
- **P2** Sprint Predictability — not run.
- **P3** Release Forecast — not run.
- **P4** architecture audit — preliminary core-diff note only.

No live services were started; no source/AS21 reads were issued. QA was static + automated-test only.

---

## Evidence reproduction

```bash
cd po-agent-platform-v2
frontend:  cd frontend && npx tsc --noEmit && npx vite build     # both exit 0
focused:   ./.venv/bin/python -m pytest \
  tests/test_agent_core_v4_attachment_sprint_scope.py \
  tests/test_harness_attachment_skills.py \
  tests/test_agent_core_v4_wave_s2.py \
  tests/test_harness_sprint_intelligence.py \
  tests/test_agent_core_v4_batch6_release_forecast.py \
  tests/test_agent_core_v4_reliable.py \
  tests/test_agent_core_v4_robust_protocol.py -q        # 2 failed, 50 passed
full v4:   ./.venv/bin/python -m pytest tests/test_agent_core_v4*.py tests/test_v4*.py -q   # 2 failed, 231 passed
```

---

## Recommendation

**STOP.** Do not resume A227R P1–P7 yet. Owner must fix D-A227P-1 (wrong enum members in the reliable
status-filter test) and D-A227P-2 (robust-protocol test asserting unimplemented recovery — align to the
stable-core fail-closed contract) so the focused P0 test set is GREEN at a new START_HEAD; then re-run the
A227 UI parity pre-gate from P0. Reconciliation of the stable-core diff (preliminary P4 note) is also
required before the live UI parity phases are trusted.
