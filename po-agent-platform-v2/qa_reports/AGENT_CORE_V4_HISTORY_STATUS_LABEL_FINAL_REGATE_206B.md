# A206B — Final Authoritative Status-Label Re-Gate

**Verdict:** `AGENT_CORE_V4_HISTORY_STATUS_LABELS_GREEN`
**Recommendation:** `PROCEED_TO_WAVE_S_APPROVAL_WITH_RELEASE_SEARCH_HELPER`

| Field | Value |
|---|---|
| Branch | `feat/core8-real-query-hardening-v2` |
| START_HEAD | `f7f846dee71b676fb0fc8d1d8f0d8aa23d521eaf` |
| Previous A206 re-gate START | `128edd2bf2681c377181a48c0fc15c5bf3398d4b` |
| A205 rollback checkpoint | `checkpoint/v4-a205-green@1fd519105ba6612f535ad98a55cb1302f387ca43` |
| Agent | 8212 (PID 11349, restarted on `f7f846d`) /live 200 |
| Task API | 8241 (PID 11274, restarted on `f7f846d`) /health 200 |
| MCP-SWTR | 3000 (PID 29268) |
| UI | 5175 (`[::1]`, PID 55236) 200 |

---

## Phase 0 — pull / diff

- `git pull --ff-only`: `8768bd6..f7f846d` (owner label-preservation bundle + docs/spec).
- Production delta `128edd2..f7f846d` limited to exactly 3 files:
  - `domain/models.py` — `StatusTransition.from_name`/`to_name` (optional) + `display_from_status`/`display_to_status` properties (source name wins, enum fallback);
  - `adapters/task_api.py` — populates `from_name`/`to_name` from the raw `old_value`/`new_value`;
  - `harness/task_intelligence.py` — history timeline + time-in-status durations render `display_*`.
- **Explicitly verified: no per-status hardcode** for `Открыт` / `На исправлении` / `Закрыт` / `Escalated` (or any other status) in the production diff — the preservation is generic for arbitrary future custom workflow names (proven by owner tests `4fc9786`/`5ac98b0` with custom labels).
- No new skill ids, no Agent Core status/skill hardcode, no local history fallback. No architecture drift.

## Phase 1 — focused automated tests (all GREEN)

| Suite | Result |
|---|---|
| `test_domain_models.py` + `test_task_api_as21_adapter.py` + `test_harness_task_intelligence.py` | 58 passed |
| `test_agent_core_v4*.py` + `test_v4*.py` | 131 passed |

Zero unexplained failures.

## Phase 2 — source/API parity retained (3/3 EXACT)

Fresh live MCP `get_task_history` vs `GET /api/v1/swtr-read/tasks/{task}/history`:

| Task | events | count | order/ts | field_code | actor | source status values |
|---|---|---|---|---|---|---|
| DMS-380 | 6 | ✓ | ✓ | ✓ | ✓ | ✓ |
| DMS-399 | 2 | ✓ | ✓ | ✓ | ✓ | ✓ |
| WMB-30000 | 4 | ✓ | ✓ | ✓ | ✓ | ✓ |

Retained from the A206 re-gate: `field_code`←`entity.code`, `changed_at`←`createdAt` (offset-aware, no `now()` substitution), actor←`user.externalId`, values = real source names, `page_info.complete=true`.

## Phase 3 — exact history labels (15/15 GREEN) — the A206 blocking defect is CLOSED

5× each for DMS-380 / DMS-399 / WMB-30000. All `COMPLETED runtime_contract`.

- **50/50 transition pairs exact** vs raw source `oldValue.name → newValue.name`; **0 cells rendered `Unknown`** across all 15 runs; 0 `to`-label mismatches.
- All mandatory labels verified rendered from live source:
  - `Открыт` ✓ (DMS-380, DMS-399, WMB-30000)
  - `На исправлении` ✓ (DMS-380, DMS-399)
  - `Закрыт` ✓ (DMS-380, WMB-30000)
  - `Escalated` ✓ (WMB-30000, ×2 revisits)
  - `В работе` ✓ (WMB-30000)
  - `Тестирование` ✓ (DMS-380)
  - `Зарегистрирован` ✓ (DMS-380, DMS-399, initial `from`)
- DMS-380 timeline now reads exactly: `Зарегистрирован → Открыт → На исправлении → Тестирование → Закрыт` (previously `Open → Unknown → Unknown → QA → Unknown`).
- WMB-30000: `Открыт → Escalated → В работе → Escalated → Закрыт` — revisit preserved with exact labels.
- Assignee-change events still excluded from status timeline; no fabricated transitions; timestamps/author retained µs-exact (P2 + P4 boundary checks).

## Phase 4 — time-in-status labels + durations (15/15 GREEN)

5× each. All `COMPLETED runtime_contract`.

- **Labels:** every duration row carries the exact source status name; **0 `Unknown`** across all 15 runs.
- **Durations rigorous proof:** all 15 runs — interval `from`/`to` boundary timestamps µs-exact vs raw MCP `createdAt` (0 boundary issues); reported `hours` = `round(exact span, 2)` within ±0.0051h in every row (verified by recomputation) — the only numeric discrepancy class is the inherent 2-decimal hours rounding (e.g. 9.31s → 0.00h), identical to the A206 re-gate accepted baseline.
- **Terminal closure:** DMS-380 final `Закрыт` and WMB-30000 final `Закрыт` intervals = 0.0s ending at the closure timestamp (2026-09-17T10:51:55.273 / 2026-07-28T08:58:09.990) — **not** extended to current time.
- **Open final interval:** DMS-399 `На исправлении` (progress) extends only to current time, offset-aware.
- **Status revisit:** WMB-30000 two separate `Escalated` intervals preserved (875701.49s and 679080.32s oracle spans) with exact labels.
- No negative intervals; transitions sorted by authoritative timestamp.

## Phase 5 — person/status + ordinary controls (retained, GREEN)

Fresh oracle (Garanin DMS: 8 active, 3 terminal DMS-248/262/36; DMS 423 rows: 87 open, 143 terminal; DMS-SPRNT-3: 65 tasks).

- `Открытые задачи Родиона Гаранина в DMS` ×5: **5/5** terminal call carries `status=not_completed` — 4× `task.search(assignee=Garanin.R.V, space=DMS, status=not_completed)` + **1× the new `task.search_assignee(reference, space=DMS, status=not_completed)`** (owner's status-carrying assignee path exercised live); **8/8 exact** active-key parity every run; **zero** terminal leakage.
- `Активные задачи Родиона Гаранина в DMS` ×3: 3/3 `status=not_completed`, 8/8 exact.
- `Все задачи Родиона Гаранина в DMS` ×2: 2/2 `task.search_assignee` **without** status, 11 tasks = full unfiltered collection (terminal tasks correctly included — this is the unfiltered case, not a constraint drop).
- `Открытые задачи в DMS`: **87/87 exact**.
- `Закрытые задачи в DMS`: **143/143 exact** = full terminal set (terminal semantics, self-consistent).
- `Покажи список задач в текущем спринте DMS и их статусы`: **65/65 exact** (DMS-SPRNT-3, `sprint.current`→`task.search_sprint`).

## Phase 6 — architecture / plugin safety (GREEN)

- Local factual `GET /api/v1/tasks` reads during the whole run: **0** (task-api access log).
- History fetched only from live REAL AS21/MCP: **33** live `swtr-read/tasks/{code}/history` hits (P2 3 + P3 15 + P4 15); no fake/frozen/cache timeline.
- dummy-55 / plugin gate: **13/13** passed.
- No Agent Core skill/status hardcode (diff audit); label preservation is generic (owner tests prove arbitrary/custom labels survive without per-status constants).

---

## Decision

The owner's generic label-preservation fix (source `from_name`/`to_name` carried through `StatusTransition` and rendered via `display_*`) is **fully verified end-to-end**:

- exact source labels: 50/50 history pairs, 0 Unknown cells, all 7 mandatory labels present from live source;
- exact durations: boundary timestamps µs-exact, terminal closure at closure (not now), open extension to now only, revisit preserved;
- retained history/API parity 3/3; retained status filtering (person+status 10/10 with the new assignee status path exercised; controls 87/87, 143/143, 65/65);
- plugin architecture intact, 0 local factual reads.

**Verdict:** `AGENT_CORE_V4_HISTORY_STATUS_LABELS_GREEN`
**Next:** `PROCEED_TO_WAVE_S_APPROVAL_WITH_RELEASE_SEARCH_HELPER` (awaiting explicit approval).

QA artifacts (untracked, repo root): `qa_206b_p2_parity.py`, `qa_206b_oracle_intervals.py`, `qa_206b_e2e.py`, `qa_206b_verify.py`, `qa_206b_restart_agent.sh`, `qa_206b_p2_results.json`, `qa_206b_oracle.json`; raw/API payloads `/tmp/qa206b_{raw,api}_{task}.json`, oracle intervals `/tmp/qa206b_oracle_intervals_{task}.json`; logs `/tmp/qa206b_{p2,oracle,e2e}.log`, agent `/tmp/qa206b_agent.log`.
