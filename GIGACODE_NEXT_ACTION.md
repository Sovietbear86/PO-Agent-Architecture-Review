# GigaCode — CURRENT NEXT ACTION

## A230R3.37-P32-CATALOG-VERTICAL-CONTRACT-QA

### Scope / gate
Owner has committed first P3.2 **catalog-only vertical** on Review `feat/core8-real-query-hardening-v2` (task-api bounded facade → Agent REST proxy → frontend `ReleasesPage` and typed client; tests + doc). **NOT a certified live SberProject integration**: underlying corporate read-only HTTPS connector `SBERPROJECT_CATALOG_READ_URL` and managed bearer access are not provisioned in this repository. Initial expected result on regular local stack is `SOURCE_UNAVAILABLE`, NOT fabricated version rows. Verified source-catalog discovery remains independent evidence from local skill, but do not invoke this skill in shipped runtime.

### Independent QA only — ONE bounded pass
1. Sync Review origin, record HEAD, validate delta only files for P3.2 including `task-api/app/routers/sberproject_read.py`, `task-api/main.py`, `po-agent-platform-v2/src/po_agent/api/v1/__init__.py`, `frontend/src/api/client.ts`, `frontend/src/recovery/Pages.tsx`, `task-api/tests/test_sberproject_catalog_contract.py` and docs.
2. Core V4 checkpoint `6fb335d`: **all 6 byte-identical**. No hardcoded fake release IDs / AS21 inferred counts / secrets / browser credential capture / `verify=False` / `-k` / no write routes.
3. Run offline typed catalog tests; verify `task-api/main.py` imports and mounts route; minimal FastAPI TestClient for `/api/v1/sberproject-read/versions`: missing configuration ⇒ 503 typed, invalid product/limit/offset ⇒ 400/422, unsafe endpoint fails, valid normalized fixture with `has_more` obeys max 20, `issueKey` and `percentDone` not projected. Do not use real credentials.
4. Verify Agent proxy `/api/v1/sberproject/releases` maps upstream unavailable to `SOURCE_UNAVAILABLE` with `membership_status=SOURCE_UNVERIFIED`, no raw AS21 payload or internal URL, no fake 0 tasks.
5. Frontend `npm run build`; browser/DOM verify `Релизы` OLP/DMS switch, selection and dates, pagination next/back respecting `has_more`/next_offset, refresh, source-unavailable state. Use **mocked, contract-shaped** data only for UI test (explicit MOCK, not business live evidence); no stale cross-product data, no XSS/raw JSON. Existing running user services must remain untouched.
6. Run focused V4 regression and Task API baseline-diff; classify known unrelated 25 Task API baseline failures properly, not blanket all-green. No full unfocused marathon. Check design against `po-agent-platform-v2/docs/P32_SBEPROJECT_CATALOG_CONTRACT.md`: need an **approved corporate registered-query HTTPS connector** + credential refresh before LIVE_GREEN. Do not write this connector as QA or copy the local GigaCode skill into production.
7. Report `po-agent-platform-v2/qa_reports/P32_CATALOG_VERTICAL_CONTRACT_QA.md` untracked. Verdict `CATALOG_CONTRACT_GREEN_LIVE_BLOCKED`, `CATALOG_LIVE_GREEN` only if real approved connector actually proven, or `RED` with exact first boundary. Do not claim release task membership; it still requires SberProject data owner. Core and user services intact, NO code changes, NO commits/pushes, STOP.

Owner patches any RED. One QA pass before moving to source provisioning or other evolution tasks.
