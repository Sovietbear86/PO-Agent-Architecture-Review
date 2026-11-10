# P3.2 — SberProject release catalog MVP (implementation contract)

## Status
Owner implemented a **safe vertical UI/API skeleton**, not yet a verified live integration. It is **SOURCE_UNAVAILABLE** until an approved corporate read-only connector is deployed. It does not execute local GigaCode skills, reuse browser cookies, or publish fabricated release membership. GigaCode independent QA is still required. Core V4 not modified.

## REST paths
- UI → Agent: `GET /api/v1/sberproject/releases?product=OLP|DMS&offset=0&limit=20`
- Agent → Task API: `GET /api/v1/sberproject-read/versions` (same bounded params).
- Task API → **operator-provisioned corporate HTTPS read endpoint**: configure `SBERPROJECT_CATALOG_READ_URL` and `SBERPROJECT_READ_ACCESS_TOKEN` through approved runtime secrets manager / process environment (never commit to git; no password or browser token capture). HTTPS certificate verification ON. Redirects OFF. A real maintained Keycloak/OIDC token provider will be needed for production renewal; a static runtime token is not a permanent deployment solution. The endpoint must be implemented by an approved SberProject connector using **registered permitted source queries**. This repo currently does not contain that connector and must not invent a GraphQL hash.
- Task API rejects auth absence, insecure URL, bad fields, pagination unknown, >20 rows; reports a typed source failure to UI. The Agent proxy strips upstream diagnostics. No fallback to AS21.

### Approved normalized endpoint response (not a claim about native SberProject schema)
```json
{
  "results": [{
    "id": "OLP.78",
    "versionNumber": "1.9.0",
    "workflowStatus": "RELEASED",
    "beginDate": "2026-07-30",
    "endDate": "2026-10-14",
    "releaseDate": "2026-10-14",
    "owner": null
  }],
  "meta": { "has_more": true, "total": 69, "next_offset": 20 }
}
```
This shape is a **connector contract example only**; numbers/records above are examples from previously reported catalog, not live data used by code. Do not expose issueKey/percentDone until source relationships are established. On unknown membership the UI displays **«Состав задач: источник не подтверждён»**.

## Independent QA acceptance
1. Static: expected files task-api/app/routers/sberproject_read.py, task-api/main.py, agent api/v1/__init__.py, frontend client + Pages.tsx and task-api tests. Check V4 frozen 6/6, no secret literals, no AS21 fallback, no hardcoded product data.
2. Run contract offline tests for unconfigured/auth error, unsafe endpoint rejection, partial-page and empty/not-empty semantics. Validate FastAPI routes mounted and agent proxy uses correct Task API. Verify full V4 regression + frontend build and baseline-diff Task API tests.
3. Browser: verify product switch OLP/DMS, refresh, pagination, error-state without false "0 tasks", selected release dates/status, no stale cross-product cards. **Without an approved connector**, a typed source-unavailable state is expected, not a UI green live-catalog.
4. One bounded source test only **if an approved managed connector+runtime secret provider already exists**. Do not build a DIY adapter to bypass corporate auth/TLS or copy tokens from the GigaCode CLI. If connector unavailable, verdict `CATALOG_CONTRACT_GREEN_LIVE_BLOCKED` — not `P32_READY`.
5. All code changes by owner, not GigaCode. Report once, STOP. No task membership A/B yet; SberProject data owner must confirm bridge `task.plan.accountingObject`→version internal GUID and AS21 identity.
