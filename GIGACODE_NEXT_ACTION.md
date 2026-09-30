# GigaCode — Current Action

## ACTIVE: A227 UI parity pre-gate R2

Role: **QA/tester only. Do NOT modify production/frontend/backend/plugin/test/config code.**

Owner has reconciled stable Core to A227 baseline `db5e35f`.
Before live UI checks, prove that reconciliation independently.

### P0 — build + Core integrity

1. Pull current `feat/core8-real-query-hardening-v2`; record START_HEAD and clean tracked worktree.
2. Verify exact zero diff vs `db5e35f1b378b6ffde0c10085af8b68e4bf1e6b5` for:
   - `src/po_agent/harness/agent_core_v4.py`
   - `src/po_agent/harness/agent_core_v4_reliable.py`
   - `src/po_agent/harness/agent_core_v4_robust.py`
   - `src/po_agent/llm/real.py`
   - `tests/test_agent_core_v4_reliable.py`
   - `tests/test_agent_core_v4_robust_protocol.py`
3. Run frontend `tsc --noEmit` and `vite build`.
4. Run focused tests:
   - attachment skill/plugin tests;
   - sprint predictability tests;
   - release forecast tests;
   - retained reliable/robust tests.
5. Run full V4 blast-radius: `tests/test_agent_core_v4*.py tests/test_v4*.py`.
6. Any unexplained failure => RED STOP.

### P1 — Tasks UI parity with direct PO Agent

Use exactly:
`Найди открытые задачи Калачанова с вложениями в пространстве WMB`

First run it in a fresh direct PO Agent dialogue and record trace/result.

Then on **Задачи**:
- same raw text must go to normal `/api/v1/query`;
- first Find => exactly one POST;
- compare factual status/answer/evidence with direct Agent;
- if attachments exist but open intersection is empty, show the grounded empty/intersection answer, not generic error;
- press Find again unchanged => exactly one new POST + fresh trace;
- navigate away/back => zero automatic POSTs, snapshot preserved;
- Refresh => exactly one repeat of last submitted raw query.

No client-side phrase/person/space router. No direct AS21 frontend call.

### P2 — Sprint Predictability

Use a valid source-backed sprint, preferably `DMS-SPRNT-3` if still present.

Require:
- request goes through `/api/v1/query`;
- terminal skill/capability = `sprint.predictability`;
- if committed baseline exists: UI displays `predictability * 100` and exact `completed / baseline_committed`;
- if baseline is absent: explicit SOURCE_CONDITIONAL/SOURCE_UNAVAILABLE;
- blank metric despite valid payload = RED;
- current scope must never substitute for committed baseline.

### P3 — Release Forecast integration

Use a source-backed release identity.

Require:
- Releases page invokes normal Agent query for forecast;
- terminal capability = `release.forecast` when source supports it;
- sufficient history => source-backed forecast;
- insufficient history/membership => explicit SOURCE_CONDITIONAL/SOURCE_UNAVAILABLE;
- no fabricated date/percentage;
- no updated_at-as-completion proxy.

### P4 — architecture audit

Require:
- six reconciled Core/Core-test files have zero diff vs A227 baseline;
- Tasks raw query is unchanged;
- attachment status extension remains plugin-owned;
- zero phrase-specific routers;
- zero direct AS21 calls from frontend;
- zero local-store factual reads;
- zero tenant-wide scans introduced by these UI fixes.

## Verdict

Exactly one:
- `AGENT_CORE_V4_UI_PARITY_GREEN_A227_PRE_GATE_R2`
- `AGENT_CORE_V4_UI_PARITY_RED_A227_PRE_GATE_R2`

If GREEN: resume A227R P3-P7.
If RED: preserve first failing evidence and STOP.

Do not modify code.
