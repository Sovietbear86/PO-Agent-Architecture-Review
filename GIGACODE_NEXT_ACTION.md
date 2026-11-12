# A230R3.50 — read-only release adapter, one bounded QA (updated)

## Roles
ChatGPT develops. GigaCode is ONLY independent QA. NO code edits/commits, no deploy/restart, no Core V4 changes.

## Source-proven discovery
OLP.78 SberProject release composition: 7 entries, 5 issueKey + source=swtr and 2 internal without AS21 key. All 5 linked AS21 point reads have matching fix_version_s UUID. This proves the five links, NOT exhaustive version membership. AS21 reverse query release=<uuid> returned zero; cannot use it to calculate readiness.

## Owner delta to verify
- Release adapter `task-api/app/services/sberproject/release_task_adapter.py`.
- Source completeness now requires `complete is True`, `has_more is False`, and source `total == len(tasks)` BEFORE AS21 point reads. This certifies only pagination of SberProject composition.
- Any whole-release Scope/Completed/WIP/Readiness/Forecast stays null. No invented '0 tasks'.
- Narrow tests in `task-api/tests/test_release_task_adapter.py` and `test_release_membership_contract.py`.

## QA one pass
Execute once from repo root:
`python3 -m pytest -q task-api/tests/test_release_membership_contract.py task-api/tests/test_release_task_adapter.py`.
Inspect only if RED, report first failure boundary. Verify Core V4 files untouched with git diff; no full regression. STOP.

## Next owner integration stage (do NOT implement as QA)
ChatGPT must bind two real local-only read-only APIs: SberProject exact-version composition (including explicit total/cursor) and AS21 point-read via issueKey, with independent AS21 version UUID identity. These local skill bridge files are not in remote repo. Do not invent a callback or expose an endpoint before real binding. Owner can use a single bounded local export if necessary; no tenant-wide scan. After binding, wire visible scrollable release task card and perform ONE end-to-end browser smoke.
