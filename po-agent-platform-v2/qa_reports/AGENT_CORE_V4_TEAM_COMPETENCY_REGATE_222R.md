# AGENT CORE V4 — Repository-Backed Team Competency Re-Gate (A222R)

**Verdict:** `AGENT_CORE_V4_TEAM_COMPETENCY_RED_A222R`
**Classification:** RED_SOURCE_SIGNAL_PLUMBING (label/component signals structurally absent from the production task view)

| Field | Value |
|---|---|
| START_HEAD | `e11bf7d50a27fe254fa108aff353e1115f1a25a2` |
| Owner remediation | `b1d0341` (fix: title/description/tags/components matching + scalar completion + casefold join), `3c436b3` (tests), `2e770bf` (retire stale test) |
| A222 baseline | `AGENT_CORE_V4_TEAM_COMPETENCY_RED_A222` (report `AGENT_CORE_V4_TEAM_COMPETENCY_222.md`) |
| Retained checkpoint | `checkpoint/v4-full-functional-green-a221r3@84b0ae2` |
| Test agent | 8212, fresh process @ `e11bf7d` (old A222 process killed) |
| Date | 2026-09-27 |

## Phase summary

| Phase | Result |
|---|---|
| P0 diff + architecture | **PASS with P0.6 violation** — production delta limited to `wave_batch3.py` (+ tests/docs); zero Core/planner/runtime/session-context changes; zero tenant-scan paths. **P0.6 FAIL:** `labels`/`components` are canonical `Task` model fields (models.py:89) but are **never populated by the production adapter** (`hardened_production_task_api.py::_map_raw_unit` maps only title/description) → not source-backed in production. |
| P1 tests | **PASS** — focused 12/12 (incl. 3 new source tests); full V4 regression **223 passed, 0 failed** (stale A222 test retired by owner in `2e770bf`). |
| P2 zero-overlap completion | **PASS 12/12** — A222 D-A222-1 CLOSED: DMS-335 3/3 + DMS-432 3/3 match, DMS-335/DMS-432 rec 3/3+3/3 → all COMPLETED in 4.5–16.6s (was step-budget FAILED), `match_count=0`/`candidates=[]`/`candidate_count=0`/`recommendation=null`, zero fabrication, bounded point read only. Non-blocking: typed warnings `no_declared_competency_match` / `insufficient_declared_competency_evidence` are set at CapabilityResult level (owner unit test proves) but NOT surfaced in the API payload (top-level `warnings=[]`; no warnings key in capability data) — pre-existing capability-warnings boundary (A207 F1 / A219 F-A219-1 class). |
| P3 task-signal matching | **RED — first failing boundary.** A (title) 2/2 EXACT, B (description) 3/3 EXACT, **C (label) + D (component) FAIL**: agent `task_signals.labels`/`components` are always `""` (adapter drops source `label`/`sber_component`), so on source-backed label/component signals the agent under-scores every member and `matched_by_field` cannot identify the correct source field (D-A222R-1). |
| P4 mixed-signal ranking | **PARTIAL (blocked by D-A222R-1)** — deterministic ordering (relevance → match_count → active → wip → blocked → login) verified EXACT on all 3 live recommendation payloads (36/36 rows sorted per documented key); "tag/component outranks description" NOT observable in production (fields never populated); score semantics clean (task relevance only, no numeric competency levels, no employee-performance language). |
| P5 load join re-gate | **PASS — A222 D-A222-2 CLOSED.** DMS-380 rec 5/5 fresh sessions; **36/36 candidate rows exact parity** vs Oracle B (production-adapter current-sprint read, casefolded logins): e.g. Agataeva (8,6,0), Moiseev excluded (no DataMarts match), Kalachanov/Kryukov (0,0,0) → rec=Kalachanov.V.V; DMS-408 12/12 (Kryukov 0 → rec); OLP-3339 10/10 (Goncharov (22,11,0) last). Lowercase AS21 logins join camelCase YAML logins everywhere. |
| P6 product/identity safety | **PASS** — DMS tasks return DMS-profile-only members (12 of 14; OLP-only Reshetnik/Goncharov excluded); OLP-3339 returns OLP-profile-only (10 incl. Reshetnik.A, Goncharov.A.O); DMS-999999 → typed `v4_capability_unavailable` "REAL AS21 did not expose task DMS-999999" (both skills, 3.7s/6.5s); no-competency-from-assignee proven: DMS-344 assignee Dolgovskoy.E.N (5 declared competencies) is NOT a candidate (only Garanin via Rust title match); no numeric levels anywhere. |
| P7 Browser C | **PASS 4/4** — B1 non-empty match (12-row table with declared competencies), B2 zero-overlap (honest "совпадений не найдено", COMPLETED, no generic error), B3 recommendation with real load ("Текущая нагрузка: 0 активных…" for rec + candidate data), B4 OLP component case (10-row table). No "SOURCE_CONDITIONAL because no competency source", no generic V4 ERROR, no leaks. Screenshots `qa_222r_browser_c/`. |
| P8 retained Team regression | **PASS 7/7 (A221R3/A222 parity)** — workload 54/19/5 (13 members), wip 31 (31 keys), blocked [DMS-352, DMS-379], capacity typed fail-closed (estimates guard), bottlenecks 9, distribution 73/13, member.time_spent 94.0h/12 (DMS-411 32, DMS-267 22, DMS-408 16, DMS-390/403/430 8 — exact A222 parity). |
| P9 audit | **PASS** — window 12810–13129: local factual reads=0, tenant scans=0, mutations=0, task-query=1 (space-scoped), bounded point reads=10, sprint-collection=51 (all space-scoped), work-log=146 (P8), files=37, versions=0. Competency facts from repository `team_members.yaml` (config read, not in task-api log by design). |

## D-A222R-1 (sole blocking defect): label/component signals missing from the production task view

**Source truth (proven by point reads):**
- DMS-408: `label = ['AQA', 'DataMarts server']`, `sber_component = [dmts]`
- OLP-3339: `label = ['qa ', ' Backend']`, `sber_component = [OLAP]`
- OLP-3079: `sber_component = [OLAP]`
- DMS-380: `label = ['Lineager', 'AQA']`, `sber_component = [dmts]`
- DMS-344: `label = ['dms-devops']`

**Production chain:** `team.competency_match`/`team.assignee_recommendation` → `_ground_task` → `runtime.adapter.get_task(key)` → `HardenedProductionTaskApiAS21Adapter._map_raw_unit` (hardened_production_task_api.py:166-207) constructs `Task(...)` with `title` + `description` **only**; `labels`/`components` keep the model default `[]` (models.py:89). The legacy `TaskApiAS21Adapter._map` (task_api.py:417) has the same gap. The matcher (`wave_batch3._task_signal_fields`, weights labels=4/components=4/title=3/description=1) therefore always sees empty label/component text.

**Live proof (agent vs independent oracles, faithful mirror of the production algorithm):**

| Case | Source field signal | Agent (live) | Source-truth oracle | Delta |
|---|---|---|---|---|
| DMS-344 (title, P3-A) | Rust @ title | Garanin 3 | Garanin 3 | EXACT ✓ |
| DMS-380 (desc, P3-B) | DataMarts @ description ×12 | 12 × score 1 | 12 × score 1 | EXACT ✓ |
| DMS-408 (label, P3-C) | DataMarts @ label "DataMarts server" | 12 × score 6, `labels:""` | 12 × score 7 (DataMarts via label, weight 4) | **12 members under-scored, matched_by_field lacks `labels`** |
| OLP-3339 (component, P3-D) | OLAP @ sber_component | 10 × score 3, `components:""` | 10 × score 4 (OLAP via components, weight 4) | **10 members under-scored, matched_by_field lacks `components`** |
| OLP-3079 (component, P3-D) | OLAP @ sber_component | 10 × score 3 | 10 × score 4 | same |

On title/description-only tasks (DMS-344/380, zero-overlap DMS-335/432) the agent is byte-exact vs the source-truth oracle (set/fields/scores/competencies all equal) — the matcher logic itself is faithful and deterministic; the defect is purely the missing adapter plumbing.

**Why owner tests mask it:** `test_agent_core_v4_team_competency_source.py::test_competency_match_uses_title_description_labels_and_components` sets `adapter.target.labels = ["Go"]` / `components = ["C++"]` directly on the fake Task object — bypassing the adapter mapping that production goes through (same masking class as A222 D-A222-2).

**Impact:** (1) relevance_score under-counts on any task whose signal lives in `label`/`sber_component`; (2) `matched_by_field` cannot identify the correct source field for C/D cases (spec P3 requirement); (3) the "tag/component outranks description" ranking property (spec P4) is unobservable in production; (4) `task_signals` in the API payload misrepresents the task (empty fields the source actually populates).

**Owner fix (proposed, not implemented):** in the production point-read mapper (`hardened_production_task_api.py::_map_raw_unit`, and for parity `task_api.py::_map`), map source attribute `label` (list of strings) → `Task.labels` and `sber_component` names → `Task.components`; add a non-mocked regression that point-reads a task with real source label/component values (e.g. OLP-3339 → `components` contains "OLAP"; DMS-408 → `labels` contains "DataMarts server") and asserts `matched_by_field`/`relevance_score` include the label/component contribution. Secondary (non-blocking): surface capability-level typed warnings (`no_declared_competency_match`, `insufficient_declared_competency_evidence`) into the API `warnings` array (A207 F1 / A219 boundary class).

## Non-blocking findings

- **F1:** typed zero-overlap warnings not surfaced in API payload (P2) — capability level correct; presentation boundary, pre-existing class.
- **F2:** source homoglyph note: DMS-344 title "С++" uses Cyrillic С (U+0421) so Latin "C++" competency correctly does NOT match (only Rust matches) — faithful source behavior, not a defect.
- **F3:** the sprint-collection route exposes only 2 attributes per row (no `label`/`sber_component`), so label/component signal discovery requires bounded point reads; the P3-C case DMS-408 IS current-sprint (its `label = ['AQA', 'DataMarts server']` matches the DataMarts competency).
- **F4:** `description` is the raw ProseMirror JSON string (pre-existing A222 behavior); text tokens are embedded and match correctly; JSON-structure tokens are inert (no declared competency token appears in JSON scaffolding).

## A222 defect status

| A222 defect | A222R status |
|---|---|
| D-A222-1 (zero-overlap step-budget) | **CLOSED** — 12/12 COMPLETED, scalar `match_count`/`candidate_count` completion, 0 rejections, 0 fabrication |
| D-A222-2 (load join case mismatch) | **CLOSED** — 36/36 candidate rows exact, casefold join verified on production casing |
| (new) D-A222R-1 (label/component plumbing) | **OPEN — blocking** |

## Safety

0 local factual reads, 0 tenant scans, 0 mutations across the full window. Zero fabrication in every run. No competency inferred from assignee history (DMS-344 control). No numeric competency levels. No employee-performance language (score is explicitly task-to-competency relevance, `method=declared_competency_match_on_title_description_labels_components_v1`).

## Recommendation

**STOP** at first failing boundary (P3 C/D; root at P0.6 adapter plumbing). Do not proceed to the competency-source checkpoint.

Re-gate (A222R2) after owner fix:
1. Map `label`/`sber_component` → `Task.labels`/`Task.components` in the production mappers + non-mocked point-read regression.
2. Re-probe P3-C DMS-408 (expect 12 × score 7 with `matched_by_field.labels` containing DataMarts) and P3-D OLP-3339/OLP-3079 (expect 10 × score 4 with `matched_by_field.components` containing OLAP) ≥3 fresh sessions each.
3. Re-confirm P2 (12/12), P5 (≥5 DMS-380 + Oracle B parity), P6, P7, P8, P9.
4. Optionally fold in the typed-warnings surfacing fix and re-assert P2 warning visibility.

## Services

- agent 8212 (fresh process @ `e11bf7d`), task-api 8241 (PID 81954), MCP-SWTR 3000, UI 5175 `[::1]` (PID 47416) — left running.

## QA artifacts

- `qa_artifacts/a222r_scan.json` — current-sprint title/label/sber_component signal scan (73 DMS + 74 OLP rows)
- `qa_artifacts/a222r_oracle.json` — per-task source fields + production-view & source-view expected rows
- `qa_artifacts/a222r_live.json` — 28 live P2–P5 probe payloads
- `qa_artifacts/a222r_load_oracle.json` — Oracle B (production-adapter current-sprint load/wip/blocked)
- `qa_artifacts/a222r_p6_support.json` — not-found probes
- `qa_artifacts/a222r_p7_browser.json` — Browser C results (+ `qa_222r_browser_c/` screenshots)
- `qa_artifacts/a222r_p8_team.json` — retained Team regression payloads
- `qa_artifacts/a222r_source_audit.json` — P9 audit window data
- Runners (repo root, uncommitted): `qa_222r_scan.py`, `qa_222r_oracle.py`, `qa_222r_live.py`, `qa_222r_load_oracle.py`, `qa_222r_p8_team.py`
