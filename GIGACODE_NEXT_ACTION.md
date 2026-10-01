# GigaCode — Current Action

## ACTIVE: Assignment A228 — Release Hardening: Restart / Recovery

Role: QA/adversarial tester only. Do not modify production/frontend/backend/plugin/test/config code.

Baseline:
- A227R3 = GREEN;
- checkpoint = `checkpoint/v4-po-acceptance-green-a227r3`;
- functional behavior is frozen;
- stable Core must remain unchanged.

## P0 — preflight / baseline integrity

1. Pull current `feat/core8-real-query-hardening-v2`; record START_HEAD.
2. Verify tracked worktree clean.
3. Verify checkpoint branch exists and points to the certified A227R3 state.
4. Run:
   - frontend `tsc --noEmit`;
   - frontend `vite build`;
   - full V4 blast-radius tests.
5. Record active service PIDs/ports and liveness before restart tests.

Any unexplained failure => RED STOP.

## P1 — Agent-only restart

With task-api + MCP + frontend left running:
1. stop Agent process only;
2. prove UI/query path reports a typed temporary failure or unavailable state — never stale factual success as a fresh response;
3. restart Agent from current START_HEAD with the production V4 env;
4. verify liveness;
5. run smoke:
   - `Задачи Семавина по рискам`;
   - `Задачи в работе в сентябрьском спринте по DMS`;
   - `Спринты в DMS`;
6. compare factual result to fresh REAL AS21 oracle;
7. prove no warm in-memory state is required.

## P2 — Task API restart

Leave Agent/MCP/frontend available:
1. stop task-api only;
2. issue one factual query while unavailable;
3. require typed SOURCE_UNAVAILABLE/ERROR behavior — no local DB/cache fallback and no false zero;
4. restart task-api;
5. verify Agent reconnects without restart if supported; otherwise document the required recovery boundary;
6. rerun factual smoke and exact source parity.

## P3 — MCP-SWTR restart / reconnect

1. stop MCP-SWTR while Agent + task-api remain alive;
2. run one bounded factual query;
3. require source failure to fail closed, with 0 local factual fallback;
4. restart MCP-SWTR;
5. verify task-api reconnect/recovery;
6. rerun exact factual query and compare to fresh oracle.

## P4 — Frontend restart

1. stop/restart Vite/frontend only;
2. open a fresh browser session;
3. verify all six routes load;
4. verify no factual result is fabricated from frontend-local cache;
5. local user-created tasks may persist only according to their documented localStorage contract;
6. run one Tasks query and one Sprint page refresh.

## P5 — Full cold-stack restart

Stop all four components:
- Agent;
- task-api;
- MCP-SWTR;
- frontend.

Then start from cold state in dependency order and record time-to-ready for each.

Require:
- no manual data repair;
- no persisted runtime-session dependency;
- no stale process/port conflict;
- first factual queries after cold start match fresh source oracle;
- no hidden warm cache required;
- no unauthorized writes.

## P6 — snapshot/recovery behavior

Browser:
1. obtain a valid source-backed Tasks result and Sprint snapshot;
2. stop Agent or task-api;
3. press Refresh;
4. stale previously labelled snapshot may remain visible, but UI must clearly show refresh failure/stale state;
5. must not relabel stale data as freshly updated;
6. restore backend;
7. Refresh again and require a new trace + fresh timestamp + source parity.

## P7 — session isolation across restart

1. create session A with resolved entity context;
2. restart Agent;
3. create fresh session B;
4. prove B does not inherit A transient context;
5. if A continuation is intentionally unsupported across restart, require explicit reset/clarification rather than silent reuse;
6. no cross-session factual leakage.

## P8 — final restart/recovery source audit

Across all phases require:
- 0 local-store factual fallback;
- 0 unauthorized AS21 mutations;
- 0 tenant-wide scans;
- 0 secret leakage in logs/UI;
- no process started from a commit other than START_HEAD;
- no skipped RED hidden by retry/restart.

## Verdict

Exactly one:
- `AGENT_CORE_V4_RELEASE_HARDENING_GREEN_A228`
- `AGENT_CORE_V4_RELEASE_HARDENING_RED_A228`

If GREEN:
- recommend checkpoint `checkpoint/v4-release-recovery-green-a228`;
- next owner phase = latency hardening;
- do not start Learning Reviewer 2.0.

If RED:
- preserve first failing evidence and STOP.
- Do not modify code.
