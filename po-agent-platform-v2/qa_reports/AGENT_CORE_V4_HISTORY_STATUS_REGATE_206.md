# A206 post-fix — History / Status Re-Gate

**Verdict:** `AGENT_CORE_V4_HISTORY_STATUS_REGATE_RED`
**Sole blocking defect:** `AGENT_SIDE_STATUS_LABEL_LOSS` — the agent renders 4 of the 7 real source status names as `"Unknown"` in `task.history` / `task.time_in_status` timelines.
**Important:** the owner's A206 Task-API-side fix (route → live `get_task_history`, payload parser, fail-closed timestamps, terminal closure, person+status constraint) is **fully verified correct**. The blocking defect is a **pre-existing** agent-side status-normalization gap that the now-working history route has exposed. Not a regression of the A206 fix.

| Field | Value |
|---|---|
| Branch | `feat/core8-real-query-hardening-v2` |
| START_HEAD | `128edd2bf2681c377181a48c0fc15c5bf3398d4b` |
| A206 diagnostic START | `7d505dc2e3204ae66942af83117f80b3fe62447a` |
| A205 rollback checkpoint | `checkpoint/v4-a205-green@1fd519105ba6612f535ad98a55cb1302f387ca43` |
| Agent | 8212 (PID 75749, restarted on `128edd2`) /live 200 |
| Task API | 8241 (PID 75600, restarted on `128edd2`) /health 200 |
| MCP-SWTR | 3000 (PID 29268) |
| UI | 5175 (`[::1]`, PID 55236) 200 |

---

## Phase 0 — pull / diff

- `git pull --ff-only`: `0a1262c..128edd2` (owner fix bundle + docs/spec).
- Delta `7d505dc..128edd2` bounded exactly to the A206 fix surface:
  - `task-api/app/routers/swtr_read.py` — history route/tool/schema + live payload parser + page completeness;
  - `task-intelligence.py` — terminal time-in-status closure;
  - `_task_live_handlers.py` + `task_catalog.py` — `task.search_assignee` optional `status`;
  - `agent_core_v4.py` — generic planner constraint-preservation rule (1 line, no entity hardcode);
  - `test_agent_core_v4_task_catalog.py`, `test_swtr_read_facade.py`; docs/spec.
- **No new skill ids, no Agent Core entity hardcode, no local history fallback.**
- Owner diff did **NOT** touch `domain/models.py`, `adapters/task_api.py`, or `workflow/status.py` → the agent status-label mapping is pre-existing (see Phase 3 root cause).

## Phase 1 — focused automated tests (all GREEN)

| Suite | Result |
|---|---|
| `task-api: tests/test_swtr_read_facade.py` | 10 passed |
| `po-agent: tests/test_agent_core_v4_task_catalog.py` + `test_harness_task_intelligence.py` | 15 passed |
| `po-agent: tests/test_agent_core_v4*.py` + `test_v4*.py` | 131 passed |
| `po-agent: tests/test_agent_core_v4_plugin_registry.py` (P8) | 13 passed |

Zero unexplained failures.

## Phase 2 — live MCP vs Task API /history parity (3/3 EXACT)

Direct SSE `get_task_history` vs `GET /api/v1/swtr-read/tasks/{task}/history`:

| Task | raw n | api n | count | order/ts | field_code | actor | value | http | latency |
|---|---|---|---|---|---|---|---|---|---|
| DMS-380 | 6 | 6 | ✓ | ✓ | ✓ | ✓ | ✓ | 200 | 0.62s |
| DMS-399 | 2 | 2 | ✓ | ✓ | ✓ | ✓ | ✓ | 200 | 0.19s |
| WMB-30000 | 4 | 4 | ✓ | ✓ | ✓ | ✓ | ✓ | 200 | 0.20s |

- `field_code` exactly from `entity.code`; `changed_at` exactly from `createdAt` (offset-aware, parsed equal, **no `now()` substitution**); actor from `user.externalId`.
- Status values normalized to **real source names**, not dict strings — e.g. DMS-380 `Зарегистрирован → Открыт → На исправлении → Тестирование → Закрыт`; WMB-30000 `Открыт → Escalated → В работе → Escalated → Закрыт`.
- `page_info = {complete: true, has_next: false, source_tool: "get_task_history", total_elements: N}` — completeness checked, no local fallback.
- **Task-API-side parser: EXACT.** The A206 parser fix is verified.

## Phase 3 — task.history E2E (15/15 COMPLETED) + RED localization

5× each for DMS-380 / DMS-399 / WMB-30000. All 15 runs `COMPLETED runtime_contract`, actual `task.history` execution, correct transition **count, order, timestamps (µs-exact), author**, assignee-change events correctly excluded (only `workflow_status` counted), no fabricated transitions, provenance preserved.

**RED — status labels not exact.** The timeline `from`/`to` cells render `"Unknown"` for source names the agent's `normalize_task_status` map lacks. Observed real source statuses vs agent render:

| Source status (raw) | Agent render | In map? |
|---|---|---|
| Зарегистрирован | Open | ✓ |
| **Открыт** | **Unknown** | ✗ (map has feminine `открыта`, not `открыт`) |
| **На исправлении** | **Unknown** | ✗ (absent) |
| Тестирование | QA | ✓ |
| **Закрыт** | **Unknown** | ✗ (map has feminine `закрыта`, not `закрыт`) |
| **Escalated** | **Unknown** | ✗ (absent) |
| В работе | In progress | ✓ |

Result: 4 of 7 real statuses → `Unknown`; timelines read e.g. DMS-380 `Open → Unknown → Unknown → QA → Unknown`. This violates Phase 3 "exact status-transition timeline vs raw MCP oracle" — the source *does* name these statuses (proven in Phase 2), the agent loses them.

**Root cause (agent-side, pre-existing, localized):**
- `po_agent-platform-v2/src/po_agent/domain/models.py:158` `normalize_task_status()` — hardcoded `status_map` with a small English/Russian subset and masculine/feminine mismatches; unmapped names fall to `TaskStatus.UNKNOWN`.
- `TaskStatus` (models.py:37) is a fixed 12-value English enum that does not represent the source's status vocabulary.
- `adapters/task_api.py:507 get_task_history()` maps `old_value`/`new_value` (real source names from the now-correct Task API) through `normalize_task_status` → `StatusTransition.from_status/to_status` (enum).
- `task_intelligence.py:83` renders `transition.to_status.value` → `"Unknown"`.

**Minimal owner fix boundary (not implemented in A206 QA):** carry the authoritative source status name through the timeline instead of a lossy enum projection — e.g. add a raw `from_name`/`to_name` (or `source_status`) field to `StatusTransition` populated from the Task API's already-correct `old_value`/`new_value`, and render that in the timeline/durations; or make `normalize_task_status` a faithful pass-through preserving the source name. Do not hardcode a per-status list (fragile to source vocabulary growth).

## Phase 4 — task.time_in_status E2E (15/15 COMPLETED, durations exact)

Oracle = raw MCP `createdAt` timestamps. 5× each.

- **DMS-399 (open):** `Открыт` interval 20:19:07.208→20:19:16.515 exact; final open `На исправлении` extends only to **current time** (offset-aware), no negative interval. Correct.
- **DMS-380 (terminal):** historical intervals exact (5.84s / 152.75s / 10d15h10m42.6s); **final terminal `Закрыт` interval = 0.0 ending at closure 10:51:55.273 — NOT extended to now** (owner `ba03829` closure fix verified). Correct.
- **WMB-30000 (status revisit):** two separate `Escalated` intervals preserved (10d3h15m + 7d20h38m), `В работе` between them (4m20.8s); final `Закрыт` = 0.0 at closure. Revisit not lost, terminal not extended. Correct.

All `from_ts_parity=True` (interval boundaries µs-exact); apparent "mismatches" in the 0.0h/144s cells are 2-decimal-`hours` rounding artifacts, not corruption. **Durations: exact. Labels: same `Unknown` defect as Phase 3** (e.g. `Unknown 243.25h` for `Escalated`).

## Phase 5 — person + status regression (10/10 deterministic) — GREEN

Fresh oracle immediately before testing: Garanin DMS active = 8, terminal = 3 (DMS-248, DMS-262, DMS-36).

- `Открытые задачи Родиона Гаранина в DMS` ×10 fresh sessions: **10/10** terminal capability `task.search` with `status=not_completed` in executed arguments; **8/8 exact** active-key parity every run; **zero** terminal tasks (DMS-248/262/36) leaked; no run labels an unconstrained collection "open". The A206 P8a stochastic constraint-drop is **fixed and deterministic**.
- `Активные задачи Родиона Гаранина в DMS` ×3: `status=not_completed`, 8/8 exact (open-only). Correct.
- `Все задачи Родиона Гаранина в DMS` ×3: `task.search_assignee` **without** status (unfiltered), 11 tasks = full collection. Correct — the "all" case is not over-filtered.

## Phase 6 — ordinary status controls (retained, exact) — GREEN

Fresh source parity (source drifted +1 closed task since A206; agent matches the fresh source exactly):
- `Открытые задачи в DMS`: **87/87 exact**.
- `Закрытые задачи в DMS`: **143/143 exact** = full terminal set (answer: «статус «completed»», self-consistent terminal semantics).
- `Покажи список задач в текущем спринте DMS и их статусы`: **65/65 exact** (DMS-SPRNT-3, `sprint.current`→`task.search`).

## Phase 7 — capability honesty (2/2)

Both queries answer honestly, distinguishing the capability definition from live source availability («Да, у меня есть capability «task.history»… Однако это зависит от того, exposes ли авторитетный источник историю…»). No unconditional claim, no fabrication. Cosmetic: answer text lands in `question` with `NEEDS_CLARIFICATION` and no options (same A206 shape variance), not a safety issue.

## Phase 8 — retained architecture / source safety — GREEN

- Local `/api/v1/tasks` factual reads during the whole E2E: **0**.
- History fetched only from live REAL AS21/MCP: **33** live `swtr-read/tasks/{code}/history` hits (= P2 3 + P3 15 + P4 15); no fake/frozen/cache timeline.
- dummy-55 / plugin gate: **13/13** GREEN.
- No production skill hardcode in Agent Core (owner diff audit).

---

## Decision

The owner's A206 fix bundle is **correct and fully verified**: history route/source working (P2 3/3 exact), Task-API parser exact, timestamps fail-closed with no `now()` substitution, terminal time-in-status closure exact, person+status deterministic 10/10, ordinary status controls exact, no local fallback, plugin invariant GREEN.

The re-gate is **RED** on one requirement — Phase 3 "exact status-transition timeline vs raw MCP oracle" — because the agent-side `normalize_task_status` (pre-existing, `domain/models.py`) collapses 4 of 7 real source status names (`Открыт`, `На исправлении`, `Закрыт`, `Escalated`) to `Unknown` in the `task.history` and `task.time_in_status` timelines. The source names these correctly (proven in Phase 2); the loss is entirely downstream in the agent.

**Verdict:** `AGENT_CORE_V4_HISTORY_STATUS_REGATE_RED`
**Root cause (sole):** agent-side status-label loss in `normalize_task_status` / `TaskStatus` enum projection (pre-existing, exposed by the now-working history route).
**Minimal next step:** carry the authoritative source status name through `StatusTransition` and render it in timeline/durations (see Phase 3 fix boundary). No production changes made by QA. Wave S remains paused.

QA artifacts (untracked, repo root): `qa_206r_p2_parity.py`, `qa_206r_e2e.py`, `qa_206r_p4_check.py`, `qa_206r_restart_agent.sh`, `qa_206r_p2_results.json`, `qa_206r_oracle.json`; raw/API payloads `/tmp/qa206r_{raw,api}_{task}.json`, oracle intervals `/tmp/qa206r_oracle_intervals_{task}.json`; logs `/tmp/qa206r_{p2,e2e}.log`, agent `/tmp/qa206r_agent.log`.
