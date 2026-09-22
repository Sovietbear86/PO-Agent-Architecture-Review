# GigaCode — Current Action

## Status
`ACTIVE_QA_A205_PREFLIGHT_RUNTIME_INTERFACE_AND_SMOKE`

## Role lock
GigaCode is **QA/adversarial tester + service operator only**.
Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT start Wave S.
Do NOT run the full 27-skill A205 yet.
Do NOT overwrite the A205 full-regression report.

## Context
Two A205 attempts failed before meaningful skill regression because the new generic `session_context` Harness argument was not propagated through every production wrapper:

1. Attempt 1: `RobustSkillNativePlannerV4.next_decision()` had the old signature.
   Owner fixed in:
   - `66549adac0d6efa3bbc7b04df6c944147131ecab`
   - `0a6db2a1ceb62b3d775659904106952134be40d2`

2. Attempt 2: `PluginizedRobustReliableAgentCoreV4Runtime._validate_call_literals()` had the old signature and did not forward `session_context`.
   Owner fixed in:
   - `93720693c8b97462624f6ea47d159173a0aca13d`
   - `ca0847735269189576242fa6e011dc02d704c7f1`

The second commit adds an interface-parity contract across production runtime wrappers.

This preflight exists to stop peeling interface failures one layer at a time. Only after it is GREEN should the full A205 be rerun.

Permanent rollback:
`checkpoint/v4-pre-wave-s-a202@e580489950e5a149a6a740cb8779dfdb0351d471`.

## Phase 0 — pull / diff / static interface sweep
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record exact START_HEAD; tracked worktree clean.
3. Diff from the second A205 report commit `fbf4745e928cbe9d0c92d1946ebc59434437b10b` to START_HEAD.
4. Confirm the owner diff is limited to:
   - pluginized session_context forwarding;
   - interface-parity regression tests;
   - docs/spec.
5. Audit the complete production inheritance chain:
   - `AgentCoreV4Runtime`
   - `ReliableAgentCoreV4Runtime`
   - `RobustReliableAgentCoreV4Runtime`
   - `PluginizedRobustReliableAgentCoreV4Runtime`
   - `RobustSkillNativePlannerV4`
6. For every overridden method involved in query planning/call validation, compare signatures with the base method and prove generic Harness args are not dropped.

Any incompatible override => RED, report, stop.

## Phase 1 — focused interface tests
Run:
```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_agent_core_v4_plugin_registry.py -v
python -m pytest tests/test_agent_core_v4_robust_protocol.py -v
python -m pytest tests/test_agent_core_v4.py -v
python -m pytest tests/test_v4_browser_api_contract.py -v
```

Mandatory:
- robust planner accepts + forwards session_context;
- base/reliable/pluginized literal guards all expose compatible session_context parameter;
- pluginized guard forwards validated context to super;
- plugin/dummy-55 tests remain GREEN;
- no new test regression.

## Phase 2 — production-chain smoke before any broad regression
Restart current-HEAD Agent and keep Task API/MCP/UI live.

Run fresh sessions, concurrency 1:

1. `покажи задачу DMS-380`
2. `задачи Калачанова в WMB`
3. `Покажи список задач в DMS-SPRNT-3 и их статусы`
4. `найди задачи без исполнителя в текущем спринте OLP`
5. typed clarification case: `задачи Гаранина в сентябрьском спринте` -> choose a real space
6. completed-turn context pair:
   - `Какой спринт в DMS идёт в сентябре?`
   - same session: `Покажи список задач в этом спринте и их статусы`
7. person attachments control.

For every case capture:
- loaded skills;
- capability calls;
- session_context received by planner/validator where applicable;
- completion/failure;
- source route.

Hard requirement:
- **zero TypeError / signature mismatch / unexpected keyword / positional-argument errors**;
- at least one real capability must execute in every supported factual case;
- no local factual reads;
- no false success.

If any framework/interface crash occurs => RED and STOP. Do not run full A205.

## Phase 3 — plugin extension sanity
Run dummy-55 once through registry/binding/completion/UI contract.
Must remain GREEN with zero core business edits.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_A205_PREFLIGHT_GREEN`
- `AGENT_CORE_V4_A205_PREFLIGHT_RED`

GREEN requires:
- interface chain compatible;
- focused tests GREEN;
- smoke reaches real skill/capability execution;
- zero framework TypeErrors;
- plugin gate GREEN.

If GREEN:
recommend exactly:
`PROCEED_TO_FULL_A205_RERUN`
but **do not start it automatically**.

If RED:
return the first exact incompatible method/signature/root cause and stop.

## Output
Commit/push only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_A205_PREFLIGHT_RUNTIME_INTERFACE_SMOKE.md`

Leave services running and return START_HEAD, report commit, test totals, smoke matrix, URLs/PIDs/health.
Then stop.
