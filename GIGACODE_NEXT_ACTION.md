# GigaCode — Current Action

## ACTIVE: Assignment A229U1R — Task details drawer UI re-gate

Role: QA/browser tester only. Do not modify code.

Previous A229U1 RED was build-only:
- `String.replaceAll` was incompatible with the project's ES2020 TypeScript lib target;
- owner replaced it with behaviorally equivalent `split('_').join(' ')`;
- no tsconfig change;
- browser phases P1-P5 were never started.

## P0 — integrity/build

1. Pull current `feat/core8-real-query-hardening-v2`; record START_HEAD and clean worktree.
2. Prove A229U1R production delta vs previous A229U1 RED is exactly the one frontend line plus docs/assignment.
3. Prove 0 Agent Core/planner/plugin/Task API changes.
4. Run:
   - `npm run build` — must exit 0;
   - `npx tsc --noEmit` — 0 errors;
   - full V4 blast-radius — retain 242/242.
5. Any build/backend regression => RED STOP.

## P1 — source-backed description

Use a REAL AS21 task known to have non-empty description, preferably DMS-330 if still available.

Require:
- opening task issues one exact source-backed task lookup;
- description area visibly shows `Загружаю описание из AS21…` while pending;
- final description equals authoritative exact task read;
- `Описание отсутствует` only when exact source task truly has no description;
- switching intelligence tabs does not re-run exact task lookup unnecessarily;
- frontend never calls AS21/MCP directly.

## P2 — readable intelligence tabs

Test:
- Резюме
- Качество
- Что не хватает
- История

Require:
- markdown-like answer is rendered readably;
- no raw `**` markers where formatting should apply;
- no raw JSON block;
- no visible `_agent_core_v4`, trajectory, source_data or internal payload;
- scalar structured data -> readable key/value rows;
- arrays of records -> table when applicable;
- scalar arrays -> list;
- long output remains scrollable without drawer overflow.

## P3 — loading/stale-data guard

Run at least 8 transitions between the four tabs.

For every transition require:
- active tab switches immediately;
- previous tab result disappears immediately;
- spinner/progress indicator appears;
- `Обновляю данные…` visible while request is pending;
- intelligence container has busy/loading state;
- success replaces loader with new content;
- failure shows explicit error and never reuses stale content.

## P4 — request cardinality

Require:
- first task open = exactly 1 exact task lookup + 1 Summary intelligence request;
- each tab switch = exactly 1 intelligence request for selected tab;
- no duplicate POST caused by effects/render;
- exact task lookup is not repeated on simple tab switches;
- no new polling.

## P5 — retained Tasks UX

Require:
- NL search still works;
- task cards open;
- local task CRUD unaffected;
- drawer closes correctly;
- Agent launcher hidden while task drawer open;
- dark/glass design remains consistent/responsive.

## Verdict

Exactly one:
- `AGENT_CORE_V4_TASK_DETAILS_UI_GREEN_A229U1R`
- `AGENT_CORE_V4_TASK_DETAILS_UI_RED_A229U1R`

If GREEN:
- recommend checkpoint `checkpoint/v4-task-details-ui-green-a229u1r`;
- owner may sync UI-only delta to public/community repo;
- resume A229R1 latency verification on the new certified HEAD.

If RED:
- preserve first failing boundary and STOP.

Do not modify code.
