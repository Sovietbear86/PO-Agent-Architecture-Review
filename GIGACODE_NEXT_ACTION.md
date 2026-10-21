# GigaCode — CURRENT NEXT ACTION

## A229M2.2B1 — Bounded Missing Goal Executor, Independent Regression Gate

**QA / source oracle / browser forensics only. NEVER change production code, tests, runtime, config, Core or planner.**
**ZERO modifications to Agent Core V4 are permitted.**
**If RED: record first failing boundary and STOP. Do not self-fix.**

### Owner delta under test
- New `api/v1/missing_goal_execution.py`: bounded, sequential governed `v4_runtime.process(HarnessRequest)` for independently missing *typed* goals.
- API seam opt-in under **three** flags:
  `PO_AGENT_V4_GOAL_COVERAGE_GUARD=true`,
  `PO_AGENT_V4_GOAL_CONTINUATION=true`,
  `PO_AGENT_V4_MISSING_GOAL_EXECUTION=true`.
- Local loopback API requests ONLY. All defaults remain **false**.
- Maximum three independent goals; at most two extra goal calls total; shared 110-second budget; each governed call timeout <=100 seconds.
- No direct MCP/handler bypass. Prior validated observations are credit-only (not injected into public current-turn results). Source facts must be REAL_AS21.
- COMPLETED only when all detected goals have matched terminal evidence and a source-backed answer; otherwise typed PARTIAL, never false success. Full original free-form LLM synthesis is NOT reused for merging because it could contain unsupported assertions.
- New `test_v4_missing_goal_execution.py` includes 7 targeted offline acceptance cases.
- Scope remains exactly the conservative goal kinds already recognized by `detect_goals`, not universal English/comparison/multi-intent.
- AUTH/SESSION OWNERSHIP remains an explicit release blocker. NO remote/multi-user rollout.
- No checkpoint until independent GREEN.

### P0 — MANDATORY FIRST: frozen Core + focused tests
1. Pull branch, record TESTED_HEAD; check clean tracked worktree.
2. Compare hashes of 6 frozen files byte-for-byte against `checkpoint/v4-complex-task-clarification-green-a229f3r@6fb335d`:
   `agent_core_v4.py`, `agent_core_v4_robust.py`, `agent_core_v4_reliable.py`, `agent_core_v4_completion.py`, `v4_plugin_registry.py`, `llm/real.py`. Any diff = RED STOP.
3. Run `tests/test_v4_missing_goal_execution.py`, `test_v4_goal_coverage.py`, `test_v4_browser_api_contract.py`, `test_v4_synthesis_elision.py` and config/runtime-factory tests. ZERO FAILED.
4. Run full V4 blast (`test_agent_core_v4*.py` + `test_v4*.py`), relevant full Task API SWTR suite and frontend build. ZERO FAILED.
5. **All new regression tests remain mandatory after EVERY owner code fix and BEFORE any new GREEN.** Do not use previously green results for a new HEAD. Record actual counts and exact TESTED_HEAD.
6. Ensure retained A229M2.2AR2/ A229F3R/ A229R2UR2 tests still pass. Preserve test-to-source parity, planner clarification, typed provider errors, period/type/hierarchy, Overview KPI/cards, and task drawer.

### P1 — exact owner implementation safety audit
- Verify branch delta restricted to new executor + API/config/tests/spec; no Core/planner/plugin handler changes.
- Check `HarnessRequest` receives typed single goal, same V4 governed registry checks, session + validated prior where relevant.
- Verify no direct handler/MCP bypass, no hardcoded person/task routing, no explicit feature defaults on, no global source scans, no unauthorized writes or local factual fallback.
- Verify MAX 3 goals, ≤2 extra calls TOTAL, one at a time, global wall deadline, cancellation and no recursive loop.
- Verify after every call that terminal args/data match immutable goal and REAL_AS21, do not trust mere `COMPLETED`.
- Verify public current-turn `data.results` contains only executed source operations; prior observations stay private.
- Check PARTIAL behavior and presentation in UI. Missing goal is agent incompletion, not invented user ambiguity.
- Scrutinize answer assembly: no unsupported negative hierarchy claims, no false counts, no dropped prior verified content, no raw SWTR cards.

### P2 — flag OFF rollback and isolation
- Run all 3 goal flags OFF => exact A229M2.2AR2 baseline parity.
- GOAL_COVERAGE only ON, CONTINUATION OFF, EXECUTOR OFF => unchanged A229M2.1 behavior.
- GOAL_COVERAGE+CONTINUATION ON, EXECUTOR OFF => exact A229M2.2AR2 behavior.
- Executor ON but prerequisites OFF => no executor activation.
- Remote client cannot activate executor even if flags ON; flag default still false.
- In every OFF state verify zero extra process calls.

### P3 — REAL AS21 A/B oracle (local isolated ON only)
Generate fresh independent oracles at start AND end. Counts are dynamic, no hardcoded expected 173/175.
Minimum 3 clean attempts each:
- M1: K WMB tasks + Semavin DMS tasks; both distinct source-proven collections.
- M2: DMS-267 lookup + hierarchy; actual parent DMS-253. No duplicate lookup read.
- M4: lookup + hierarchy + person K WMB (3 goals); all goals proven.
- C5: lookup + related tasks; relationships only when hierarchy/relations governed evidence proves it.
- Negative lookup DMS-380; do not infer missing parent based on missing card property.
- C1/C3/C4 composed filters are ONE goal, never split; comparison M5 outside detector remains OPEN (do not incorrectly mark multi-intent GREEN).
For every case: exact key/count/fact oracle parity, source reads, executed capabilities and args, LLM calls, p50/p90 time; output and public cards match proven facts.

### P4 — fail closed and adversarial testing
- Invalid/partial/LOCAL source response, provider 429/timeout, source 502, wrong capability, wrong person/space/task, stale prior, >6 prior, >8192 B, cross-session client injection, concurrent same-session requests, expired clarification, one-shot token, restart.
- No false COMPLETED, zero unsupported answer/evidence, no source-unavailable interpreted as REAL_EMPTY, no duplicate rereads of proved goals, no data mutation/local reads/tenant wide scans.
- Confirm 110s shared deadline is genuinely enforced; cancellation stops source work; global LLM/source budgets are not silently reset per subprocess. If existing V4 API cannot prove budget, RED or explicitly stop before calling it a bounded guarantee.
- Confirm protocol statuses and Web UI show PARTIAL correctly without making incomplete answer look fully successful.
- Authenticated session ownership STILL OPEN: this is local QA ONLY. Never claim release-ready auth.

### P5 — verdict and mandatory artifacts
GREEN only if P0-P4 pass (including 3-goal exact REAL AS21, regression, and no false COMPLETED). Otherwise RED with exact first failing boundary and STOP.

Return one:
`AGENT_CORE_V4_BOUNDED_MISSING_GOAL_EXECUTION_GREEN_A229M22B1`
`AGENT_CORE_V4_BOUNDED_MISSING_GOAL_EXECUTION_RED_A229M22B1`.

Commit QA REPORT ONLY:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_BOUNDED_MISSING_GOAL_EXECUTION_A229M22B1.md`.

Report TESTED_HEAD, REPORT_COMMIT, hashes 6/6, exact suite pass/fail counts, real AS21 oracle matrix, OFF/ON parity, source reads/LLM calls/latency, payload samples, browser evidence, security OPENs.

**AUTOMATIC RULE AFTER ANY FUTURE CODE CHANGE:** full focused suite + full V4 blast + Task API SWTR + frontend build + real A/B oracle regression are MANDATORY before checkpoint or public promotion. Re-record and compare immutable TESTED_HEAD every time. No silent waivers or 'already tested in earlier run'.
