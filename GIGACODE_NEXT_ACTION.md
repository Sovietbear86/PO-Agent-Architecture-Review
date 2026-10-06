# GigaCode — Current Action

## ACTIVE: Assignment A229U1 — Task details drawer UI re-gate

Role: QA/browser tester only. Do not modify code.

A229R1 latency verification is temporarily PAUSED because owner made a frontend-only usability correction after the latency assignment was issued.

Scope is exactly the Tasks detail drawer.

## P0 — integrity/build

1. Pull current `feat/core8-real-query-hardening-v2`; record START_HEAD and clean worktree.
2. Prove Agent Core/planner/plugin/Task API production files are unchanged by A229U1.
3. Run frontend TypeScript/build.
4. Run focused retained frontend tests if present.
5. Run full V4 blast-radius to prove no backend regression.

Any build/backend regression => RED STOP.

## P1 — source-backed description

Use a REAL AS21 task known to have a non-empty description, preferably the manual PO example DMS-330 if still available.

Steps:
1. Find/open the task from the Tasks search result collection.
2. Observe initial drawer state.
3. Capture network calls and Agent trace.

Require:
- drawer issues one exact source-backed task lookup for the selected task key;
- while it is pending, description area visibly says `Загружаю описание из AS21…`;
- after completion, description matches the authoritative exact task read;
- `Описание отсутствует` may appear only when the exact source-backed task really has no description;
- switching intelligence tabs does not re-run the exact task lookup unnecessarily;
- no frontend direct AS21/MCP request.

## P2 — readable intelligence rendering

For the same task, test all four tabs:
- Резюме;
- Качество;
- Что не хватает;
- История.

Require:
- Agent answer markdown/bold/list/table formatting is rendered readably, not shown with raw `**` syntax;
- raw JSON blocks are absent;
- `_agent_core_v4`, trajectory, source_data and other internal payload fields are not displayed;
- structured scalar data appears as readable key/value rows;
- arrays of records render as tables where applicable;
- scalar arrays render as lists;
- long data remains scrollable and does not overflow the drawer.

## P3 — loading feedback / stale-data guard

For each tab transition:
1. click another tab;
2. capture UI immediately before response;
3. capture final UI.

Require:
- active tab changes immediately;
- previous tab's result is cleared immediately and is NOT shown as if it belongs to the new tab;
- visible spinner/progress line appears;
- text `Обновляю данные…` is visible while request is pending;
- intelligence container has loading/busy state;
- successful response replaces loader with the new tab content;
- failed request shows explicit error and never reuses stale previous content.

Run at least 8 transitions across the four tabs, including back-and-forth transitions.

## P4 — request cardinality

Require:
- opening a task: exactly one exact task lookup + one initial Summary intelligence request;
- each tab switch: exactly one intelligence request for the selected tab;
- no duplicate POST from React/state effects;
- closing/reopening may issue fresh source reads, which is acceptable;
- no background polling introduced.

## P5 — retained Tasks UX

Require:
- natural-language Tasks search still works;
- task cards still open;
- local task CRUD unaffected;
- drawer closes correctly;
- Agent launcher remains hidden while task drawer is open;
- dark/glass design remains consistent and responsive.

## Verdict

Exactly one:
- `AGENT_CORE_V4_TASK_DETAILS_UI_GREEN_A229U1`
- `AGENT_CORE_V4_TASK_DETAILS_UI_RED_A229U1`

If GREEN:
- recommend checkpoint `checkpoint/v4-task-details-ui-green-a229u1`;
- owner may sync the UI-only delta to public/community repo;
- resume A229R1 latency verification on the new certified HEAD.

If RED:
- preserve first failing boundary and STOP.

Do not modify code.
