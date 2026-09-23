# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_206B_HISTORY_STATUS_LABEL_FINAL_REGATE`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT start Wave S.
Do NOT add new skills.

## Context
A206 post-fix re-gate proved the owner history/status fixes are correct:
- Task API history parity 3/3 exact;
- task.history 15/15 completed;
- task.time_in_status 15/15 completed with correct terminal closure and status revisits;
- person+status 10/10 deterministic;
- ordinary status controls exact;
- local factual reads = 0;
- plugin gate GREEN.

The sole remaining RED was **agent-side status label loss**:
the generic `TaskStatus` enum projected source statuses like `Открыт`, `На исправлении`, `Закрыт`, `Escalated` to `Unknown`, even though REAL AS21 history supplied the authoritative names correctly.

Owner fix is deliberately generic and does **not** expand a hardcoded status map:
- `StatusTransition` now carries optional authoritative `from_name` / `to_name`;
- adapter keeps the normalized enum for generic logic but also preserves exact source names;
- history and time-in-status rendering use source names when present;
- generic enum fallback remains for legacy/fake transitions;
- tests prove arbitrary/custom source labels survive without adding per-status constants.

Owner commits:
- `884ec661c7b95aab25ee54cd6fedd7c61721ad0c`
- `a18f161b13721de4fd3581a6f017ea16f358b2f1`
- `7c04eef04f3dcb78e733ce79343fdba1533d8b5d`
- `4fc978607c43a313fc946be8f85f4ca0ce7a38f8`
- `5ac98b010bc9627b53a8db956d78e47a65b0e78a`

A205 rollback checkpoint remains:
`checkpoint/v4-a205-green@1fd519105ba6612f535ad98a55cb1302f387ca43`.

## Mission
Run a **narrow final A206B re-gate** proving exact authoritative source status labels survive end-to-end, while retaining the already-green history/status behavior.

## Phase 0 — pull / diff
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record START_HEAD; tracked worktree clean.
3. Diff from previous A206 re-gate START `128edd2bf2681c377181a48c0fc15c5bf3398d4b`.
4. Confirm new production delta is limited to:
   - `StatusTransition` source label fields/display properties;
   - adapter population of those labels;
   - history/time-in-status rendering;
   - focused tests/docs.
5. Explicitly confirm no per-status hardcode was added for `Открыт`, `На исправлении`, `Закрыт`, `Escalated`.

Any architecture drift => RED.

## Phase 1 — focused automated tests
Run:
```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_domain_models.py -v
python -m pytest tests/test_task_api_as21_adapter.py -v
python -m pytest tests/test_harness_task_intelligence.py -v
python -m pytest tests/test_agent_core_v4*.py -v
```

Zero unexplained failures.

## Phase 2 — source/API parity retained
For DMS-380, DMS-399, WMB-30000:
- live MCP `get_task_history`;
- Task API `/api/v1/swtr-read/tasks/{task}/history`.

Require retained exact parity:
- event count;
- order;
- timestamps;
- field_code;
- actor;
- source status values.

## Phase 3 — exact history labels
Run 5x each:
- `покажи историю статусов задачи DMS-380`
- `покажи историю статусов задачи DMS-399`
- `покажи историю статусов задачи WMB-30000`

Require timeline labels exactly reflect source names where source supplies them.

Mandatory examples if still present in live source:
- `Открыт`
- `На исправлении`
- `Закрыт`
- `Escalated`
- `В работе`
- `Тестирование`

No source-supplied status name may render as `Unknown`.

The normalized enum may remain UNKNOWN internally for an unmapped custom workflow state, but presentation/evidence must retain the authoritative source label.

## Phase 4 — time-in-status labels + durations
Repeat representative queries for DMS-380, DMS-399, WMB-30000.

Require:
- labels match source status names exactly;
- durations remain exact vs raw timestamps;
- terminal final interval = closure, not now;
- open final interval = now;
- repeated status visits preserved.

## Phase 5 — retained person/status + ordinary controls
Run:
- `Открытые задачи Родиона Гаранина в DMS` ×5 fresh;
- `Активные задачи Родиона Гаранина в DMS` ×3;
- open DMS;
- closed DMS;
- current sprint + statuses.

Require exact fresh Oracle parity, no dropped status constraint.

## Phase 6 — architecture/plugin safety
Require:
- local factual `/api/v1/tasks` reads = 0;
- no fake/frozen/cache history;
- dummy-55/plugin gate GREEN;
- no Agent Core skill/status hardcode;
- authoritative source label preservation is generic for future custom statuses.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_HISTORY_STATUS_LABELS_GREEN`
- `AGENT_CORE_V4_HISTORY_STATUS_LABELS_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires:
- exact source labels;
- exact durations;
- retained history/API parity;
- retained status filtering;
- plugin architecture intact.

If GREEN:
recommend exactly:
`PROCEED_TO_WAVE_S_APPROVAL_WITH_RELEASE_SEARCH_HELPER`

If RED:
STOP. Do not start Wave S. Return first exact root cause.

## Output
Commit/push only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_HISTORY_STATUS_LABEL_FINAL_REGATE_206B.md`

Leave UI/backend/Task API/MCP running.
Return verdict, START_HEAD, report commit, exact label parity, duration parity, service health.
Then stop.
