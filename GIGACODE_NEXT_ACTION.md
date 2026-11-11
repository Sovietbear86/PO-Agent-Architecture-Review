# A230R3.49 — release linkage subset: QA only

Owner: ChatGPT; GigaCode must NOT change code, patches, scripts, config or commits.

### Source findings from completed A230R3.48
- OLP.78 (SberProject version 1.9.0) SberProject release composition has 7 rows.
- 5 rows have source=swtr + issueKey; five AS21 point reads independently show matching fix_version_s linked to the AS21 version UUID.
- 2 rows lack issueKey (internal SberProject tasks).
- AS21 reverse query via release=<version-uuid> returned 0: this is NOT an exhaustive enumerator for the fix_version_s link.
- Therefore MEMBERSHIP_UNVERIFIED for whole release; do not produce Scope, Completed, WIP, ready%, Delivery Forecast, or assert there are only 5/7 tasks in the total release population.

### New owner pure code
`task-api/app/services/sberproject/release_membership_contract.py`: `verified_partial_links` verifies source-issued issueKey + source=swtr + AS21 key + explicit fix_version_s UUID. It returns PARTIAL_SOURCE_PROVEN and complete=False; no live API integrated.

### One bounded QA action
Run only `python3 -m pytest -q task-api/tests/test_release_membership_contract.py`, inspect resulting tests (no edits), summarize PASS/RED + failure reason and STOP. No live data reads, no full regression, no deployment.

### Owner next integration decision
A separate read-only adapter must fetch a SINGLE selected release's SberProject composition and point-read the linked AS21 task IDs, returning a bounded list. Do not confuse the linked subset with exhaustive membership. To unlock aggregate metrics, source owner must confirm an authoritative exhaustive version-to-task contract (including internal-only rows) and explicit version identity binding. Do not infer from version name/number.
