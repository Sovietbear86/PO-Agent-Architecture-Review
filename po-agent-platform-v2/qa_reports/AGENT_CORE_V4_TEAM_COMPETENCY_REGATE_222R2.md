# AGENT CORE V4 — Competency Signal Plumbing Re-Gate (A222R2)

**Verdict:** `AGENT_CORE_V4_TEAM_COMPETENCY_GREEN_A222R2`
**Classification:** both skills `team.competency_match` + `team.assignee_recommendation` = SOURCE_READY

| Field | Value |
|---|---|
| START_HEAD | `17fdacbc60856c5f587e1a33c2f88da770d66c5f` |
| Owner fix | `16c0d77` (map SWTR label+sber_component in canonical mapping), `bd3c81c` (hardened point-read mapper), `f9fb159` (decode raw attributes in mapper), `66cfa5a` (plumbing regression test) |
| A222R baseline | `AGENT_CORE_V4_TEAM_COMPETENCY_RED_A222R` (sole blocker D-A222R-1) |
| Test agent | 8212, fresh process PID 29982 @ `17fdacb` |
| Date | 2026-09-27 |

## Phase summary

| Phase | Result |
|---|---|
| P0 diff/tests | **PASS** — production delta is **adapter plumbing only**: `hardened_production_task_api.py` (+5) and `task_api.py` (+51) map source `label`→`Task.labels` and `sber_component`→`Task.components` via a new shape-tolerant `_string_list`; no Agent Core/planner/runtime/session/completion/registry changes. Tests 225 passed / 0 failed, incl. new `test_agent_core_v4_task_signal_plumbing.py` (2) which drives the REAL `_map_raw_unit` and `_map` mappers with realistic raw shapes (not a fake Task). |
| P1 source parity | **PASS** — canonical Task (via production `EvidenceValidatedProductionTaskApiAS21Adapter.get_task`) now carries the real source labels/components for all 4 focus tasks, matching independent raw point reads (DMS-408 `['AQA','DataMarts server']`+`['dmts']`; OLP-3339 `['qa','Backend']`+`['OLAP']`; OLP-3079 `[]`+`['OLAP']`; DMS-380 `['Lineager','AQA']`+`['dmts']`). OLP-3339 label strings are whitespace-stripped (`'qa '`→`'qa'`) — value-preserving normalization, not data loss. |
| P2 signal re-gate | **PASS 14/14 — D-A222R-1 CLOSED.** DMS-408 3/3, OLP-3339 3/3, OLP-3079 3/3, DMS-344 2/2, DMS-380 3/3 → all COMPLETED. The A222R score deltas close: **DMS-408 12 × score 7 (was 6)**, **OLP-3339/OLP-3079 10 × score 4 (was 3)**. `task_signals` now reflects source (e.g. `L='AQA DataMarts server' C='dmts'`). `matched_by_field` cites the real source field: DMS-408 `labels:['DataMarts']`, OLP-3339/3079 `components:['OLAP']`. Weights held (label/component=4, title=3, description=1). Exact candidate set + scores + competencies vs independent Oracle B source-view on all 7 focus tasks. No competence from assignee (DMS-344 assignee Dolgovskoy absent; only Garanin via Rust title). |
| P3 retained regressions | **PASS** — zero-overlap DMS-335 3/3 + DMS-432 3/3 (COMPLETED, empty, `task_signals` now populated but 0 matches, no fabrication); DMS-380 recommendation 5/5 with **84/84 candidate load/WIP/blocked rows exact** vs Oracle B; team workload 54/19/5 (13), wip 31, blocked [DMS-352, DMS-379], bottlenecks 9, distribution 73/13, member.time_spent 94.0h/12 (A222R parity). capacity typed fail-closed (estimates guard). |
| P4 Browser C | **PASS 4/4** — B1 label-driven DMS-408 (mc=12, `L='AQA DataMarts server'`), B2 component-driven OLP-3339 (mc=10, `C='OLAP'`), B3 zero-overlap DMS-335 (mc=0), B4 recommendation DMS-380 (cc=12, rec=Kalachanov.V.V, real load). Structured result + declared-competency evidence + load all rendered; no generic V4 ERROR, no "no competency source" text, no leak. (B1 first run was a response-capture false positive — backend COMPLETED + full UI table; clean on re-run. Screenshots `qa_222r2_browser_c/`.) |
| P5 audit | **PASS** — window 13131–13446: local factual reads=0, tenant scans=0, mutations=0, task-query=0, bounded point reads=22 (all task-scoped), sprint-collection=44 (space-scoped), versions=0. Label/component facts only from bounded REAL AS21 point reads; competency facts only from repository `team_members.yaml`. |

## D-A222R-1 status (was sole blocker)

**CLOSED.** The production point-read mapper now maps `label`→`Task.labels` and `sber_component`→`Task.components`. Live proof vs the A222R source-truth oracle (which is now also what production sees):

| Task | Source signal field | A222R (agent) | A222R2 (agent) | Oracle B source-view | matched_by_field |
|---|---|---|---|---|---|
| DMS-408 | label "DataMarts server" | 12 × 6 | **12 × 7** | 12 × 7 ✓ | `labels:['DataMarts']` |
| OLP-3339 | component "OLAP" | 10 × 3 | **10 × 4** | 10 × 4 ✓ | `components:['OLAP']` |
| OLP-3079 | component "OLAP" | 10 × 3 | **10 × 4** | 10 × 4 ✓ | `components:['OLAP']` |
| DMS-344 (control) | title "Rust" | 1 × 3 | 1 × 3 (unchanged) | 1 × 3 ✓ | `title`/`description` |
| DMS-380 (control) | description "DataMarts" | 12 × 1 | 12 × 1 (unchanged) | 12 × 1 ✓ | `description` |
| DMS-335/432 (zero) | — | 0 | 0 (unchanged) | 0 ✓ | — |

The matcher logic was already faithful (A222R proved byte-exact parity on title/description-only tasks); the only gap was the adapter dropping label/component before the canonical Task. That plumbing is now fixed and proven end-to-end against live REAL AS21.

## Non-blocking findings

- **F1:** OLP-3339 source labels `'qa '`/`' Backend'` are whitespace-stripped to `'qa'`/`'Backend'` by `_string_list` — value-preserving, expected.
- **F2:** Browser C B1 first run missed the structured payload in the response listener (backend COMPLETED, UI rendered the full 12-row table) — a QA harness capture flake (same class as A217D), clean on re-run; not a product defect.
- **F3:** DMS-344 label `dms-devops` / component `dmts` correctly do NOT match any declared competency token (e.g. "DevOps/Kubernetes" requires both `devops`+`kubernetes`), so it stays title-driven — faithful token-subset semantics.

## A222R defect status

| Defect | Status |
|---|---|
| D-A222-1 (zero-overlap step-budget) | CLOSED (A222R, retained here 6/6) |
| D-A222-2 (load join case mismatch) | CLOSED (A222R, retained here 84/84) |
| D-A222R-1 (label/component plumbing) | **CLOSED** |

## Safety

0 local factual reads, 0 tenant-wide scans, 0 mutations across the full window. Zero fabrication in every run. No numeric competency levels. No employee-performance language (score is task-to-competency relevance; method `declared_competency_match_on_title_description_labels_components_v1`). No competence inferred from assignee/history (DMS-344 control).

## Recommendation

**GREEN.** Recommend a small immutable **competency-source checkpoint** on `17fdacb` (canonical-54 unaffected; adapter plumbing is the only production change). Both team-competency skills classify **SOURCE_READY**. Next owner phase = **UI widget/state/lineage remediation**.

## Services

- agent 8212 (PID 29982 @ `17fdacb`), task-api 8241 (PID 81954), MCP-SWTR 3000 (PID 29268), UI 5175 `[::1]` (PID 47416) — left running.

## QA artifacts

- `qa_artifacts/a222r2_p1_parity.json` — P1 canonical Task vs raw source parity (4 focus tasks)
- `qa_artifacts/a222r_oracle.json` — refreshed Oracle B (production-view + source-view) for 7 focus tasks
- `qa_artifacts/a222r2_live.json` — 29 live P2/P3/P4 probe payloads
- `qa_artifacts/a222r_load_oracle.json` — Oracle B current-sprint load/wip/blocked
- `qa_artifacts/a222r2_p3_team.json` — P3 retained team regression payloads
- `qa_artifacts/a222r2_p4_browser.json` — P4 Browser C results (+ `qa_222r2_browser_c/` screenshots)
- `qa_artifacts/a222r2_source_audit.json` — P5 audit window data
- Runners (repo root, uncommitted): `qa_222r2_p1_parity.py`, `qa_222r2_live.py`, `qa_222r2_p3_team.py`; reused `qa_222r_oracle.py`, `qa_222r_load_oracle.py`
