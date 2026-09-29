# GigaCode — Current Action

## ACTIVE: Assignment 226R2 — text-search scale + final UX re-gate

QA only. Do not modify code.

Prior verdict: `AGENT_CORE_V4_UI_POLISH_SNAPSHOT_RED_A226R`.
First RED: `RED_P3_UNSCOPED_TEXT_SEARCH_SOURCE_SCALE`.

Owner fixes under test:
- task-api isolates per-space failures for unscoped phrase search and returns `incomplete_spaces` + `source_complete=false`;
- task.search_text propagates completeness metadata/warning;
- Tasks UI has only 5 modes: Текстовый поиск / Исполнитель / Статус / Спринт / Релиз;
- Text search has explicit space selector, default WMB;
- AI launcher hidden while task drawers are open;
- snapshot timestamps use ru-RU date+time;
- page refresh leaves loading after max ~65s and preserves stale snapshot on timeout;
- unchanged Aging refresh forces live re-read;
- all LOCAL-NNNN/local-task fixes retained.

### P0 Build/diff
Prove no Agent Core/planner/runtime drift. Run focused task-api/task-search/aging/local-task tests, tsc and vite build.

### P1 Text search blocker
Browser: Tasks -> Text -> WMB -> `БП 2027` -> Найти.
Require exact current WMB oracle parity, including description matches, with no reads of other spaces from this scoped request.
Away/back = 0 POST. Page Refresh re-runs same WMB+text criteria.

Direct unscoped task-api phrase probe:
- healthy-space matches remain available if STS/CRPV hit bounds;
- `source_complete=false`;
- failed spaces listed in `incomplete_spaces`;
- no fake exactness/zero.

RED here => STOP.

### P2 Tasks UX
Visible modes exactly 5: Text, Assignee, Status, Sprint, Release.
No attachment/Excel/PDF/MSG buttons.
Smoke:
- Text WMB / БП 2027
- Assignee Kalachanov.V.V
- live status
- Sprint DMS-SPRNT-3
- valid release identity
No tenant-wide fallback scan.

### P3 Local drawer overlap
At 1440x900 open local-task drawer and click center of Создать/Сохранить.
Require AI launcher hidden/not hit-testable while local or AS21 task drawer is open.
LOCAL-NNNN, deadline, tags, priority, edit/reload remain GREEN.
0 AS21 writes.

### P4 Overview refresh
Press Обновить on populated Overview.
Old data stays visible; loading ends within ~65s plus small tolerance.
Timestamp format must be ru-RU date+time.
Failure/timeout preserves stale snapshot and shows error.
Away/back = 0 unwanted reread.

### P5 Quality Aging
DMS + 15. Press Aging Обновить again with identical criteria.
Require a live re-read with same DMS/15 criteria and exact source parity.

### P6 Sprint forensic
Use exact valid id `DMS-SPRNT-3` (NOT DMS-DPRNT-3).
Verify exact source parity for Scope, Completed, Velocity, Throughput, WIP, Risk Queue, Predictability/readiness.
Previous live baseline was about 74 / 22 / 22 / 1.571 / 32 / 29.7%, risk queue ~37; source drift allowed only if independently proven.
For predictability prove the source-backed baseline. If historical source is insufficient, typed SOURCE_CONDITIONAL is acceptable; no fabrication.
Unexpected NEEDS_CLARIFICATION/FAILED for valid sprint id => RED.

### P7 Releases forensic
Use release.search / source directory; do not judge only stale default WMB-2024-Q3.
Test source-backed ids such as `1.6.0` and `24Q1` (or current equivalents).
Verify Scope/Progress/Blockers/Dependencies/Risk Queue separately.
If release-to-task membership is absent, typed SOURCE_CONDITIONAL/UNAVAILABLE is expected; never fake zero or pseudo forecast.
Valid release identity must not become generic NEEDS_CLARIFICATION solely because membership is absent.

### P8 Retained smoke/audit
Recheck Platform V, OLAP+DataMarts only, rich Daily Brief, Team actual utilization, team Aging, 6 backgrounds, 1440+480 no overflow, cached revisit 0 POST, 0 mutations, 0 local factual fallback.

Verdict exactly:
- `AGENT_CORE_V4_UI_POLISH_SNAPSHOT_GREEN_A226R2`
or
- `AGENT_CORE_V4_UI_POLISH_SNAPSHOT_RED_A226R2`

GREEN -> recommend `checkpoint/v4-ui-polish-snapshot-green-a226r2`.
RED -> preserve first failing evidence and STOP.
