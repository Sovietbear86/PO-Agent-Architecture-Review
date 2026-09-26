# A219 — Batch 5 PO Workflow Gate

**Verdict: `AGENT_CORE_V4_BATCH5_PO_RED_A219`**
**First failing boundary:** `po.local_task_draft` with a non-existent source task key → planner detours to `task.lookup` → `v4_runtime_failure` (step-budget exhaustion) instead of the spec'd typed "source task not found" terminal.

**Inventory (required):**
- Live registry: **67 skills / 12 plugins**, 0 duplicates
- Canonical coverage: **53/54**
- Exact canonical missing list: **`release.forecast`** (1)

**User-focus audit (tenant scans / draft write-mutation): CLEAN.**
- tenant-wide / unscoped task scans = **0**
- local factual reads (`GET /api/v1/tasks`) = **0**
- mutations (POST/PUT/DELETE to data) = **0** (100% GET traffic)
- every draft source call = **bounded point read only**
- every draft: `write_performed=false`, `requires_approval=true`

---

- START_HEAD: `f4e183b3e3c37315d6a51994502032804b634005`
- Owner Batch 5: `b11a61f` (feat: 5 bounded PO skills), `b241b94` (test), `b88f322` (test: attention order)
- Frozen baseline: A218 GREEN (live 62/11, coverage 48/54, 6 missing). Spec rollback checkpoint `checkpoint/v4-self-introspection-green-a218` is docs-only (no git tag object, same convention as prior checkpoints); effective base commit = `89444bd` (A218 report).
- Role: QA/adversarial tester + service operator only. No production/frontend/plugin/test/config code modified.

---

## Phase 0 — Architecture invariants: GREEN

- Diff `89444bd..f4e183b` limited to `src/`+`tests/` = exactly 2 files:
  - `src/po_agent/harness/v4_plugins/wave_batch5_po.py` (+453, new plugin)
  - `tests/test_agent_core_v4_batch5_po.py` (+198, new tests)
- **Zero Agent Core/planner/runtime/session-context changes.** The pre-existing legacy files that mention `po.*` ids (`harness/po_assistant.py`, `harness/runtime.py`, `harness/skill_catalog.py`) and `domain/models.py` are **untouched** by the Batch 5 commits (verified via `git diff --name-only` over the commit range) — Batch 5 is strictly additive.
- Registry discovers exactly **one** new plugin `builtin.batch5.po_workflow` and **all five** skills (`po.attention_queue`, `po.daily_brief`, `po.status_report`, `po.reminder_draft`, `po.local_task_draft`) exactly once each; 0 duplicate ids.
- dummy-55 invariant GREEN (plugin registry suite).

### Boundedness (user focus) — code-level proof
The three production adapter methods Batch 5 uses are all **bounded** (`adapters/production_task_api.py`):
- `get_task(key)` → `GET /swtr-read/tasks/{key}` — one **point read**, typed 404→None, 502/503→`AS21SourceUnavailable`.
- `get_current_sprint_id(space)` → `GET /swtr-read/spaces/{space}/current-sprint` — one **space-scoped** read.
- `get_sprint_tasks(sprint_id, space)` → `GET /swtr-read/sprints/{sprint}/tasks?complete=true&limit=100&max_pages=100` — **bounded sprint membership**, fails closed on `complete=false`.

The Batch 5 plugin **never calls `search_tasks`** (the legacy tenant-wide route that `POAssistantCapabilities` used via `search_tasks("")`). `_current_sprint_portfolio` iterates only `APPROVED_PRODUCT_SPACES = {WMB, STS, OLP, DMS, CRPV}`.

## Phase 1 — Tests: GREEN

| Suite | Result |
|---|---|
| `test_agent_core_v4_batch5_po.py` + `agent_help` + `plugin_registry` + `planner_signature_parity` | **24/24 pass** |
| full `tests/test_agent_core_v4*.py` + `tests/test_v4*.py` | **204/204 pass** |

Zero unexplained failures; signature-parity lock (A217C guard) retained.

## Phase 2 — Independent bounded REAL AS21 oracle

Built an **independent** oracle (`qa_219_p2_oracle.py`) that queries the raw task-api `swtr-read` routes directly (not the agent's adapter) and classifies with the **certified** predicates imported from `po_agent.domain.models` (terminal/non-terminal `statusType` sets, `NEED_INFO` blocked, `age_days` from `created_at`). No tenant-wide query.

Per-space at capture time:

| Space | State | Sprint | Tasks | Completed | Blocked |
|---|---|---|---|---|---|
| CRPV | NO_CURRENT_SPRINT | — | — | — | — |
| DMS | SOURCE_BACKED | DMS-SPRNT-3 | 73 | 18 | 2 |
| OLP | SOURCE_BACKED | OLP-SPRNT-8 | 73 | 2 | 6 |
| STS | NO_CURRENT_SPRINT | — | — | — | — |
| WMB | SOURCE_BACKED | WMB-SPRNT-2 | 1 | 1 | 0 |

Aggregates: **total=147, active=126, blocked=8, unassigned=8, completed=21, attention_count=108**. Top-attention: 8 tasks at score 70 (DMS-352, DMS-379, OLP-2906, OLP-2986, OLP-3059, OLP-3118, OLP-3133, OLP-3204) — blocked+aging_14d; deterministic tie-break by key.

## Phase 3 — po.attention_queue: 9/9 PASS
5 natural forms (×2, +1 extra). Every run: `COMPLETED`/`runtime_contract`, trajectory = `po.attention_queue` only, `count=108` and **exact queue key-set + per-item score parity** to the oracle, deterministic descending-score-then-key ordering, `scoring_version=po_attention_v1`, `scope=approved_product_spaces_current_sprints`, 0 fabricated values.

## Phase 4 — po.daily_brief: 9/9 PASS
5 forms. Every run: `COMPLETED`, exact parity to oracle — active=126, blocked=8, unassigned=8, completed=21, attention_count=108, top-5 keys exact, per-space states preserved (CRPV/STS = `NO_CURRENT_SPRINT` explicit, not fabricated zeros).

## Phase 5 — po.status_report: 9/9 PASS
5 forms. Every run: `COMPLETED`, exact totals (total=147, completed=21, active=126, blocked=8), completion_percent exact, `by_product` rows exact with `NO_CURRENT_SPRINT` spaces preserved as **null metrics** (not zeros).

## Phase 6 — po.reminder_draft: safe; see D-A219-2 (cosmetic)
- **DMS-380** (×2): `COMPLETED`, one source point read only, `draft_created=true`, `write_performed=false`, `requires_approval_for_send=true`, source-backed task facts, recipient `semavin.m.m`. **PASS** on all spec assertions.
- **Assigned real task (DMS-434)**: `COMPLETED`, point read, `draft_created=true`, `write_performed=false`, `requires_approval_for_send=true`, recipient `moiseev.a.n`. **PASS**.
- **Missing key** (×2): `NEEDS_CLARIFICATION`, no capability executed, 0 source calls. **PASS**.
- **Non-existent key (DMS-999999)**: `COMPLETED` via `po.reminder_draft` direct, `draft_created=false`, `write_performed=false`. **PASS**.

All reminder runs are read-only with zero mutation. (My QA runner initially flagged the 3 "found" runs on a `warnings` surfacing check that is over-strict — see F-A219-1; the data fields all satisfy the spec.)

## Phase 7 — po.local_task_draft: 1 defect (D-A219-1)
- **source task DMS-380** (×2): `COMPLETED`, point read, `draft_created=true`, `write_performed=false`, `source=REAL_AS21`, `requires_approval_for_external_write=true`. **PASS**.
- **user subject only**: `COMPLETED`, **0 AS21 calls**, `draft_created=true`, `write_performed=false`, `source=USER_INPUT_ONLY`, approval metadata. **PASS**.
- **source + custom subject (DMS-380)**: `COMPLETED`, point read, `source=REAL_AS21`, `write_performed=false`, approval. **PASS**.
- **no subject + no source**: `NEEDS_CLARIFICATION`, 0 calls. **PASS**.
- **invalid source task (DMS-999999)**: **RED — see D-A219-1.**

Draft read-only invariant holds for every local-draft run that executed (`write_performed=false`, `requires_approval_for_external_write=true`, zero mutation).

### D-A219-1 (BLOCKING) — invalid local-draft source key crashes instead of typed not-found
**Repro:** `создай локальный черновик задачи на основе DMS-999999` — **5/5 deterministic FAILED** (4 in the official sweep window + 3 re-probes).
**Trajectory:** planner routes `task.lookup` **then** `po.local_task_draft`. `task.lookup` is not a loaded capability in that planning context → robust repair reports `capability_not_loaded:task.lookup` (repeated) → `v4_runtime_failure` / "planner step budget exhausted without READY" → generic answer *"Agent Core v4 не смог безопасно завершить траекторию."*
**Expected (spec Phase 7):** a point read of `DMS-999999` returns 404 → `po.local_task_draft` typed terminal `draft_created=false`, `write_performed=false`, "source task not found".
**Contrast (proves it is local-draft-specific, not a global regression):**
- `po.reminder_draft` on the **same** invalid key (`DMS-999999`) completes cleanly via `po.reminder_draft` direct (`draft_created=false`, 1 point read, 404→None) — **PASS**.
- `po.local_task_draft` on a **valid** key (`DMS-380`) completes cleanly (sometimes via a `task.lookup` detour, sometimes direct) — **PASS**.
So the planner only breaks when the local-draft source key is invalid. It is **safe** (fail-closed, bounded point read, no fabrication, no mutation) but does not satisfy the spec's invalid-key terminal.

## Phase 8 — Browser C (real UI): 5/5 PASS
`[::1]:5175`, all five skills via the UI (`qa_219_p8_browser.json`, screenshots `qa_219_browser_c/`):
- C1 attention queue: `COMPLETED`, count=108.
- C2 daily brief: `COMPLETED`, active=126.
- C3 status report: `COMPLETED`, total=147, by_product 5 spaces.
- C4 reminder draft (DMS-380): `COMPLETED`, `draft_created=true`, `write_performed=false`, `requires_approval=true`, UI states no send/write occurred.
- C5 local task draft (DMS-380): `COMPLETED`, `draft_created=true`, `write_performed=false`, `requires_approval=true`, UI states no AS21 write occurred.

No generic V4 ERROR, no session-id leak, no fake metrics. (Browser C uses a **valid** draft key, so it does not exercise the D-A219-1 invalid-key path.)

## Phase 9 — Retained regression: 18/18 PASS
agent.help full catalog (2/2), ping (2/2), DMS-380 lookup (2/2), current sprint DMS (2/2), Semavin member.time_spent (2/2, A215G parity retained), portfolio.overview (2/2), standalone release identity 24Q1/WMB (2/2), release progress typed SOURCE_CONDITIONAL (2/2), release health typed SOURCE_CONDITIONAL (2/2). Zero planner signature/runtime failures (A217C class remains closed).

## Phase 10 — Source/write audit: CLEAN (user focus)
Whole task-api log over the A219 window (`qa_219_p2_oracle.json` + per-run line-delta capture):
- **tenant-wide / unscoped task-query scans = 0** (no `search_tasks`, no unscoped `task-query`)
- **local factual reads (`GET /api/v1/tasks` non-swtr) = 0**
- **mutations = 0** — the log is **100% GET** (no POST/PUT/DELETE to any data route)
- PO aggregation source calls are **bounded** current-sprint/sprint-membership only: current-sprint calls only for the 5 approved spaces; sprint-tasks only for `DMS-SPRNT-3`, `OLP-SPRNT-8`, `WMB-SPRNT-2`
- **draft source calls are bounded point reads only**: `DMS-380` (34×), `DMS-434` (2×), `DMS-999999` (2×, 404)
- 7 unscoped `GET /swtr-read/versions` calls are **pre-existing A217B** release-search no-space rejections (all `400`, line 6085+, before the A219 window) — not Batch 5.
- Agent log: **0 TypeError, 0 traceback**; the only `v4_runtime_failure` occurrences are the D-A219-1 invalid local-draft key.

## Phase 11 — Inventory reconciliation: as expected
Fresh registry enumeration after Batch 5:
- **live skill_count = 67**, **plugin_count = 12** (A218's 11 + `builtin.batch5.po_workflow`), 0 duplicates
- **canonical coverage = 53/54** (47 direct + 6 semantic remaps)
- **exact canonical missing = [`release.forecast`]** (1)
- extra in V4 live beyond canonical 54 (14): `agent.help`, 9 time-accounting skills, `release.search`, `sprints.discover`, `sprints.list`, `tasks.lookup_then_assignee`
- Cross-check: 53 + 1 (missing) = 54 ✓; 53 + 14 (extra) = 67 ✓

This matches the spec's expectations exactly (67 live, 53/54 coverage, remaining missing = `release.forecast`).

---

## Findings

- **D-A219-1 (BLOCKING):** `po.local_task_draft` + invalid source key → planner `task.lookup` detour → `capability_not_loaded:task.lookup` → `v4_runtime_failure` / step-budget exhaustion → generic error, instead of the typed `draft_created=false` "source task not found" terminal. Safe (fail-closed, bounded, no mutation) but spec-nonconforming on the invalid-key path. Owner fix: prevent the planner from routing a `po.local_task_draft` grounding read through `task.lookup` (or make that grounding read the single bounded `get_task` point read the capability already performs); add a non-mocked regression for the invalid local-draft key.
- **F-A219-1 (non-blocking, cosmetic):** capability-level `warnings` (`draft_only_no_external_write`) are not surfaced to the top-level `warnings` array in the API payload. The read-only guarantee is nonetheless proven by `write_performed=false`, `requires_approval=true`, the "запись/отправка не выполнялась" answer text, and the zero-mutation audit.
- **F-A219-2 (non-blocking, QA-runner artifact):** my draft pass-requirement over-weighted the top-level warning; the spec's draft assertions are all satisfied by the data fields.

## Services (left running)
- UI: `[::1]:5175` (vite, PID 47416)
- Agent: `127.0.0.1:8212` (PID 54189 @ `f4e183b`, V4 enabled, task-api mode)
- Task API: `127.0.0.1:8241` (PID 81954, system python3)
- MCP-SWTR SSE: `127.0.0.1:3000` (PID 29268)

## Recommendation
**RED** — STOP at the first failing boundary (D-A219-1). Do **not** create an immutable Batch 5 checkpoint until the invalid local-draft key is fixed and re-gated. Everything else (boundedness, read-only drafts, zero tenant scans, zero mutations, 53/54 coverage, P3–P6, P8–P11) is GREEN and retained. After the owner fix + A219 re-gate: recommend immutable Batch 5 checkpoint and next owner step = isolated Batch 6 `release.forecast` source-contract implementation.
