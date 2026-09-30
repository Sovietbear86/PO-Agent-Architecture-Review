# GigaCode — Current Action

## ACTIVE: Assignment A227R3 — P3-B re-gate, then resume P4-P7

Role: QA/adversarial tester only. Do not modify code.

Owner remediation is plugin/declarative only. Stable Core must remain zero diff vs A227 baseline.

### P0 — focused integrity
1. Pull current branch and record START_HEAD.
2. Prove zero diff vs A227 baseline for stable Core/LLM files.
3. Run focused tests for:
   - text + person plugin search;
   - task status normalization;
   - attachment composition;
   - retained task-search/plugin tests.
4. Run full V4 blast-radius.
5. Any unexplained failure => RED STOP.

### P3-B — 5/5 mandatory
Query:
`Задачи Семавина по рискам`

Build a fresh independent REAL AS21 oracle immediately before runs.

Require all 5:
- planner selects `task.search_text` as the text/phrase skill;
- no separate `member.resolve` planner hop is required before the terminal capability;
- call preserves `phrase + reference` and any explicit space if present;
- person identity is resolved source-backed inside the capability;
- terminal result is source-backed task collection / REAL_EMPTY;
- exact source parity;
- zero robust bounded-repair failures;
- zero tenant-wide scans.

If any run fails, preserve the full planner trajectory and first invalid provider response if available, then STOP.

### Retained P3 controls
Do one control each:
- P3-A open Kalachanov + attachments in WMB;
- P3-C in-progress September DMS;
- P3-D sprints in DMS.

No need to repeat full matrices unless a control regresses.

### P4–P7
If P3-B is 5/5 GREEN and retained controls stay GREEN:
- P4 task cards/persistence. Use the latest UI commit: Sprint page must have exactly one Predictability widget; when baseline is absent it shows `н/д` with explicit source-baseline reason.
- P5 Quality refresh isolation.
- P6 fresh Aging exact parity for DMS >7 and >15.
- P7 retained regression/source audit.

## Verdict
Exactly one:
- `AGENT_CORE_V4_PO_ACCEPTANCE_GREEN_A227R3`
- `AGENT_CORE_V4_PO_ACCEPTANCE_RED_A227R3`

If GREEN recommend checkpoint `checkpoint/v4-po-acceptance-green-a227r3` and release hardening next.
Learning Reviewer 2.0 remains blocked.

If RED preserve first failing evidence and STOP.
