# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_197_V4_EXISTING_CATALOG_FULL_REGRESSION_REGATE`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.

Do NOT modify production/frontend/plugin/test/config/architecture code. Do not start Wave S. If a defect is found, classify/report only.

## Context
A196 executed all 27 currently exposed V4 skills and found:
- 18 GREEN;
- 4 SOURCE_CONDITIONAL;
- 5 RED caused by two bounded implementation classes:
  1. `task.aging` and `task.similar` used unscoped tenant-wide scans;
  2. `task.search_excel/pdf/msg` performed unbounded per-task attachment N+1 scans for space-wide requests.

Owner fixes since A196:
- `60933ca3687df8038bac179342b8aa23720237ea` — bounded live handlers for aging/similar + bounded attachment fan-out;
- `01cc11df7ea63459b65f449598d5c003beafe9cd` — plugin bindings moved aging/similar off legacy tenant-wide handlers;
- `ff02bd6c89d9cd73c37da304b4aa94aa5027001a` — live task-query preserves source timestamps for aging/flow analytics;
- `088d6f74ec1594cc84190956bc38c671ef3373d9` — task.quality UIContract;
- `eb13bfe35a600a45299e57145173f32eb6e44b33`, `f01f27ffd648a3079798ee797923b752bcb8bed4` — refreshed/focused tests.

Important attachment semantics:
- exact-task and bounded person-scoped attachment queries remain supported;
- if a broad space-only query exceeds the bounded fan-out limit and AS21 exposes no batch attachment-search surface, the handler must fail closed quickly as SOURCE_UNAVAILABLE/SOURCE_CONDITIONAL;
- it must never launch thousands of per-task file calls or fabricate a partial/empty complete result.

Permanent rollback:
`0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188`.

## Mission
Re-run the **complete 27-skill regression**, prove that A196 D1/D2 are closed or correctly source-conditional, and reject any new regression before Wave S.

## Phase 0 — start / architecture audit
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record exact START_HEAD; tracked worktree clean.
3. Read A196 report + owner diff after A196.
4. Confirm:
   - no Agent Core/planner/completion business-skill edit;
   - aging/similar fixes live in plugin/source boundary;
   - attachment wide-query guard is bounded/fail-closed, not timeout masking;
   - zero local `/api/v1/tasks` truth;
   - Hermes/plugin dummy-55 extensibility remains intact.

Any violation => RED.

## Phase 1 — automated suites
Run:
```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_agent_core_v4*.py -v
python -m pytest tests/test_v4*.py -v
```

Run relevant Task API tests too.

Specially confirm:
- refreshed task-catalog tests no longer assert stale pre-A195D capability composition;
- new bounded aging/similar/attachment tests pass;
- task.quality UI contract is registered.

Record exact totals.

## Phase 2 — fresh REAL AS21 Oracle
Refresh the same Oracle classes as A196:
- DMS-380 + assignee;
- WMB-30000 and known Excel/PDF attachment tasks;
- DMS current sprint and complete sprint task set;
- DMS open set;
- identity cases from A195D;
- release/history source availability;
- source timestamps availability for aging.

Do not reuse A196 counts without refresh.

## Phase 3 — mandatory D1/D2 focused re-gate

### D1 task.aging
Run at least 3x:
- `Застоявшиеся открытые задачи в DMS`
Require:
- actual loaded skill `task.aging`;
- bounded live `task-query?space=DMS` provenance;
- no tenant-wide `search_tasks("")`;
- deterministic count/keys against fresh Oracle built from live DMS rows and source timestamps;
- no fabricated age when source timestamp is absent.

### D1 task.similar
Run at least 3x:
- `Похожие на DMS-380`
Require:
- actual loaded skill `task.similar`;
- source task resolved through live bounded route;
- candidate corpus restricted to DMS/source task space;
- no tenant-wide scan;
- deterministic top matches/method;
- completion under a practical bounded latency.

### D2 attachments
Run each at least 3x:
- exact task attachment lookup (WMB-30000);
- bounded person-scoped Excel search using a source-proven person;
- broad `Excel-вложения в WMB`;
- broad `PDF-вложения в WMB`;
- broad `MSG-вложения в WMB`.

Expected semantics for broad space-only cases:
- if AS21 still has no certified batch attachment-search surface and candidate count exceeds the configured bound, classify `SOURCE_CONDITIONAL` only if it fails closed quickly with a typed source-unavailable result and **zero unbounded N+1 fan-out**;
- a >200s/300s timeout is RED;
- partial scan presented as complete/empty is RED.

## Phase 4 — full 27-skill API matrix
Repeat all 27 exposed V4 skills from A196. No row may be skipped.

For each:
- NL query;
- expected/actual skill;
- trajectory;
- status;
- completion mode;
- source provenance;
- exact Oracle parity where factual;
- evidence;
- UIContract;
- final classification.

Allowed row classifications:
- GREEN_SOURCE_SUPPORTED
- SOURCE_CONDITIONAL
- RED

Overall GREEN requires zero RED rows.

## Phase 5 — retained high-risk regression
Repeat:
- DMS-380 -> assignee tasks 5x;
- full-name assignee 5x;
- non-team unique identity;
- ambiguous surname -> clarification -> option continuation;
- invented identity;
- person+sprint 5x;
- current sprint 3x;
- WMB-30000 attachments 3x;
- clarification continuation;
- zero stale `AS21 вернул некорректные данные` for normal ambiguity/not-found.

## Phase 6 — Browser C
Cover current result shapes, including:
- task_detail;
- task_table;
- attachment_table;
- task_analysis (**task.quality must now render via UIContract, not raw trace JSON**);
- dependencies;
- history/source-unavailable;
- similar-task list;
- sprint summary/list/health;
- release clarification/source conditional;
- identity clarification continuation;
- safe not-found/source-unavailable.

## Phase 7 — plugin/extensibility
Re-run A190 dummy-55 gate. No core edit may be needed.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_GREEN`
- `AGENT_CORE_V4_EXISTING_CATALOG_REGRESSION_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires:
- 27/27 skills tested;
- zero RED rows;
- D1 closed;
- D2 either source-supported GREEN or explicitly SOURCE_CONDITIONAL with fast bounded fail-closed semantics;
- exact Oracle parity for factual GREEN rows;
- Browser C / identity / clarification / plugin gates GREEN;
- zero local-store truth.

If GREEN, recommendation:
**Freeze A197 as the clean pre-Wave-S checkpoint and proceed to owner Wave S #23–32 through the existing plugin surface.**

## Output
Commit/push only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_FULL_EXISTING_CATALOG_REGRESSION_197.md`

## Service keepalive
Leave current-HEAD UI/backend/Task API/MCP running after QA and return URLs, ports, PIDs, health and exact START_HEAD. Then stop.
