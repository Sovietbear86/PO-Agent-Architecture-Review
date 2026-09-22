# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_203_V4_TEST_ONLY_COMPATIBILITY_CHECK`

## Role lock
GigaCode is **QA only**.

Do NOT modify production code, frontend, plugins, config, architecture, or tests.
Do NOT start Wave S.
Do NOT add new skills.

## Context
A202 is GREEN and frozen at:
`checkpoint/v4-pre-wave-s-a202`
commit:
`e580489950e5a149a6a740cb8779dfdb0351d471`

After A202, owner made only two test-compatibility fixes:
- `a914977b0fb753e52f3fd5b1980ea4723184a380` — finish 2->3 tuple migration in stale clarification owner tests;
- `6152d807f5c2fbb759966280eab77ca127c88286` — complete health-test readiness mock with `available_facts`.

No runtime/source/plugin behavior changed after the A202 checkpoint.

## Mission
Prove the post-A202 test suite is internally clean before starting any new skill work.

## Phase 0 — diff audit
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
2. Record exact START_HEAD; tracked worktree clean.
3. Diff `e580489950e5a149a6a740cb8779dfdb0351d471..START_HEAD`.
4. Confirm that product/runtime changes after A202 are zero; only test/docs/spec changes are present.

Any production behavior change => RED.

## Phase 1 — focused tests
Run:
```bash
cd po-agent-platform-v2
source .venv/bin/activate
python -m pytest tests/test_v4_owner_fix_contracts.py -v
python -m pytest tests/test_v4_browser_api_contract.py -v
python -m pytest tests/test_agent_core_v4_completion_contract.py -v
python -m pytest tests/test_agent_core_v4_plugin_registry.py tests/test_agent_core_v4_task_catalog.py -v
```

Require zero failing tests.

## Phase 2 — minimal runtime sanity
Do NOT run a full catalog campaign.
Only confirm the currently running services still expose:
- UI 200;
- Agent /live 200;
- Agent /health 200 and no unscoped task scan;
- Task API swtr-read/health 200;
- MCP connected.

Run one supported factual query and one clarification continuation as a sanity check only.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_POST_A202_TEST_COMPAT_GREEN`
- `AGENT_CORE_V4_POST_A202_TEST_COMPAT_RED`

GREEN requires:
- diff is test/docs only;
- focused tests all pass;
- minimal runtime sanity passes;
- no new regression.

If RED: stop, report only.
If GREEN: recommend **Wave S may begin only after explicit owner/user approval**.

## Output
Commit/push only:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_POST_A202_TEST_COMPAT_203.md`

Leave services running and return START_HEAD, report commit, test totals and service health. Then stop.
