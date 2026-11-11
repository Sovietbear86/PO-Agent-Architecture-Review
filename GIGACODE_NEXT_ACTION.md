# A230R3.50 — Single-release read-only linked-task adapter QA

GigaCode is QA ONLY. Do not edit sources, install packages, commit, deploy, restart, or read more source data.

## Owner changes
- `task-api/app/services/sberproject/release_task_adapter.py`: dependency-injected adapter for ONE exact release, max 100 composition rows and AS21 point reads; checks source/identity/complete pagination.
- `task-api/tests/test_release_task_adapter.py`: narrow mocked tests.
- This is NOT wired to live routes/UI. The complete=True check refers only to SberProject composition page coverage, NOT exhaustive AS21 reverse membership. Response is explicitly PARTIAL_SOURCE_PROVEN; all release-wide KPIs remain null.

## Exactly one QA run
From repository root, in existing environment:
`python3 -m pytest -q task-api/tests/test_release_membership_contract.py task-api/tests/test_release_task_adapter.py`

Report count PASS/RED; on RED show FIRST failing boundary and compact root cause. Check Core V4 unchanged against baseline with read-only git diff (no re-run full regression). STOP. No live data reads, no real SberProject/AS21 requests.

## Owner continuation
Review existing task-api AS21 point-read and SberProject searchTaskCr interfaces in local working copy. Bind actual read-only callbacks (including authorized, verified AS21 UUID lookup) and create one selected-release API after proving bounded source complete. Then wire scrollable release card and independently QA it. Never fabricate release-wide completeness or readiness.
