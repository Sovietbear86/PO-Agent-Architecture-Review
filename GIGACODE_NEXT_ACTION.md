# GigaCode — Current Action

## ACTIVE: A227 UI parity pre-gate

Role: **QA/tester only. Do NOT modify production/frontend/backend/plugin/test/config code.**

This is a focused pre-gate before A227R. Do not run the full A227R yet.

### P0 — build
1. Pull current `feat/core8-real-query-hardening-v2`; record START_HEAD and clean worktree.
2. Run frontend `tsc --noEmit` and `vite build`.
3. Run focused retained V4/plugin tests relevant to task attachment search and release forecast.
4. Any failure => RED STOP.

### P1 — Tasks UI = same Agent query behavior

Use exactly:
`Найди открытые задачи Калачанова с вложениями в пространстве WMB`

First establish the direct PO Agent result in a fresh dialogue.

Then on **Задачи**:
1. enter the exact same query and press **Найти**;
2. prove exactly one POST to `/api/v1/query`;
3. compare status, answer/evidence and factual result with the direct Agent run;
4. if the source proves attachments exist but none satisfy open/not-completed, UI must show that grounded answer/empty intersection honestly — not generic "не удалось получить корректный результат";
5. press **Найти** again without changing text: require exactly one new POST and a fresh trace;
6. navigate away/back: require zero automatic POSTs and preserved snapshot;
7. Refresh must repeat exactly the last submitted NL query once.

No separate task search engine, no client parsing/routing by surname/space/status.

### P2 — Sprint Predictability

Use a source-backed sprint, first preference `DMS-SPRNT-3` if still valid.

Require:
- Sprint page sends `Покажи predictability <sprint_id>` through normal `/api/v1/query`;
- terminal skill/capability is `sprint.predictability`;
- if authoritative committed baseline exists, UI renders `predictability * 100` as percent and shows completed / baseline_committed;
- compare exact completed count, baseline and ratio against capability payload;
- UI must not read a nonexistent `predictability_percent` field as the primary contract;
- if committed baseline is unavailable, render SOURCE_CONDITIONAL/SOURCE_UNAVAILABLE explicitly;
- current sprint scope must never be substituted for missing committed baseline;
- blank/broken Predictability with a valid capability payload is RED.

### P3 — Release Forecast integration (separate from the reported defect)



Use a source-backed release identity that `release.search` can resolve.

Require:
- Releases page sends a forecast request through normal `/api/v1/query`;
- terminal skill/capability is `release.forecast` when source permits;
- when history is sufficient, render source-backed forecast date/days;
- when history or membership is insufficient, render SOURCE_CONDITIONAL/SOURCE_UNAVAILABLE with the agent explanation;
- blank Predictability/Forecast and fabricated percentages/dates are RED;
- no updated_at-as-completion proxy;
- no tenant-wide scan.

### P3 — architecture audit

Require:
- Tasks raw text goes unchanged to Agent endpoint;
- zero phrase-specific UI router;
- zero direct AS21 calls from frontend;
- zero new owner changes to stable Harness/Core for this UI correction;
- attachment status extension remains plugin-owned.

## Verdict

Exactly one:
- `AGENT_CORE_V4_UI_PARITY_GREEN_A227_PRE_GATE`
- `AGENT_CORE_V4_UI_PARITY_RED_A227_PRE_GATE`

If GREEN: recommend resuming A227R P3-P7.
If RED: preserve first failing evidence and STOP.

Do not modify code.
