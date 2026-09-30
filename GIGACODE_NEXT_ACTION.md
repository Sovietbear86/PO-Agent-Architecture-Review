# GigaCode — Current Action

## ACTIVE: Assignment A227R — PO acceptance re-gate

Role: **QA/adversarial tester only. Do NOT modify production/frontend/backend/plugin/test/config code.**

A227 stopped at first RED in P3. Preserve P0-P2 GREEN evidence. Owner has fixed production code; GigaCode only re-gates.

### Owner fixes under test

- repeated identical provider/schema failure no longer consumes four identical retries;
- repeated failure switches to constrained action-only recovery;
- deterministic recovery is allowed only for one unambiguous pending governed capability and binds only prior typed observations + conservative status enum;
- recovery can never synthesize READY;
- attachment task skills now preserve optional status together with person/space/sprint;
- `В работе` / `In Progress` is a typed REAL AS21 `status_type=progress` predicate;
- no phrase-specific routing, no hardcoded people/spaces, no local factual fallback, no tenant-wide scan.

## P0R — focused preflight

1. Pull current `feat/core8-real-query-hardening-v2`; record START_HEAD; clean worktree.
2. Run focused Python regressions:
   - `test_agent_core_v4_robust_protocol.py`
   - `test_agent_core_v4_task_search_source_status.py`
   - `test_agent_core_v4_attachment_sprint_scope.py`
   - `test_agent_core_v4_task_catalog.py`
   - relevant retained V4 composition/plugin suites.
3. Run frontend `tsc --noEmit` + `vite build`.
4. Any unexplained regression => RED STOP. No code edits.

## P3R — natural-language composition

For every collection case build an independent live REAL AS21 oracle first. Run each browser case **5 times**.

### A
`Открытые задачи Калачанова с вложениями в пространстве WMB`

Require:
- WMB + person + open/not_completed + attachments all preserved;
- source-backed person resolution;
- bounded reads;
- exact task-key/count parity;
- source-proven empty is valid if oracle is empty;
- 0 planner robust-bounded-repair failures;
- 0 tenant-wide scans.

### B
`Задачи Семавина по рискам`

Require:
- source-backed Semavin identity;
- correct compositional task/risk path;
- no invented risk rows;
- 5/5 terminally correct;
- no repeated ValidationError repair loop.

### C
`Задачи в работе в сентябрьском спринте по DMS`

Require:
- period resolves the source-backed September DMS sprint;
- terminal capability is a task collection, not sprint identity;
- task call preserves `space + sprint_id + status`;
- status is evaluated as typed `status_type=progress`;
- exact source task-key/count parity;
- **false zero is RED** if the oracle contains rows.

### D retained control
`Спринты в DMS`

Require grounded non-task rich result. Do not render fake task-empty state.

If any P3 case is RED, preserve first failing trajectory/oracle and STOP.

## P4 — task cards / persistence

After P3 GREEN:
- task collection => real cards + Task Details;
- non-task result => grounded rich answer;
- away/back => 0 new POST and exact result retained;
- edit input without submit => existing submitted result unchanged;
- Refresh => exactly one repeat of last submitted NL query.

## P5 — Quality refresh isolation

- top Quality Refresh => quality/missing/acceptance only;
- task Проверить => task-quality group only;
- Aging must not fire from either action;
- stale quality snapshot preserved while refreshing;
- no false timeout before 120s.

## P6 — Aging exact live parity

Refresh independent REAL AS21 oracles immediately before testing:
- DMS > 7 days
- DMS > 15 days

Do **not** assume old A227 values 77/68 are still current.

Require:
- team-scoped bounded assignee reads;
- exact keys/count vs fresh oracle;
- Aging button fires Aging only;
- same criteria Refresh performs a live re-read;
- rows contain key/title/assignee/status/age_days;
- SOURCE_UNAVAILABLE/CONDITIONAL is never rendered as zero;
- 0 tenant-wide scans.

## P7 — retained regression/audit

Recheck:
- local-task CRUD;
- Platform V + OLAP/DataMarts top bar;
- Sprint DMS-SPRNT-3;
- honest Release source limitation;
- Team utilization;
- six backgrounds + 1440/480 overflow;
- 0 local-store factual reads;
- 0 unauthorized mutations;
- 0 tenant-wide scans.

## Verdict

Exactly one:
- `AGENT_CORE_V4_PO_ACCEPTANCE_GREEN_A227R`
- `AGENT_CORE_V4_PO_ACCEPTANCE_RED_A227R`

If GREEN:
- recommend checkpoint `checkpoint/v4-po-acceptance-green-a227r`;
- next owner phase = release hardening: restart/recovery, latency, security, rollback rehearsal;
- **Learning Reviewer 2.0 remains blocked.**

If RED: preserve first failing evidence and STOP. Do not modify code.
