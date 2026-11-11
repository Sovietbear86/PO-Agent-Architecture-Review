# A230R3.48 — Releases membership source audit (QA only)

Owner: ChatGPT. GigaCode is an independent QA tester: NO code edits, NO commits, NO deployments, NO source modifications.

## Confirmed state
- User confirmed live /Releases pagination works, OLP 69 versions in four pages.
- SberProject provides version catalogue. AS21/SWTR task data exists, but release→task identity has NOT been proven.
- ChatGPT added the pure source-proven release membership contract and narrow unit tests under task-api/app/services/sberproject/ and task-api/tests/. These are NOT wired to live UI, must not be described as an operational release analytics feature.

## One bounded QA review
1. Execute ONLY: `python3 -m pytest -q task-api/tests/test_release_membership_contract.py` from repo root, in the existing environment. If dependencies are missing, report BLOCKED, do not install anything.
2. Read-only inspect ONE real OLP version (OLP.78) and at most TEN task records in AS21 through existing configured read-only skills; establish which field actually links version ID to task IDs. Do NOT infer from display version number, no tenant-wide scan, no secrets or token/log output.
3. Return one concise report with: source field name, raw *field names only* of the SberProject and AS21 objects, match-count if provable, and explicit verdict SOURCE_PROVEN / MEMBERSHIP_UNVERIFIED.
4. STOP. Do not implement any change, do not re-run full regressions, do not claim fake scope, completion or forecast.

If source interface unavailable, state unavailable; no invented results.
