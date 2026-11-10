# GigaCode — NEXT ACTION

## A230R3.39-P32-SBERPROJECT-CONNECTOR-IMPLEMENTATION

### Starting point
A230R3.38 verdict **CONNECTOR_REQUIRED** (10.11.2026), independent report `po-agent-platform-v2/qa_reports/P32_LIVE_CONNECTOR_DECISION.md` in owner's local workspace (untracked). There is **no approved production server connector yet**. The local personal `sbt-project` skill v0.3.0 proves one bounded real `versions OLP` read (69 total, 50 page; `has_more=true`) but is not runtime-deployable as an app service. GigaCode has identified the existing registered `productVersionListByPage` operation and exact source fields; **no newly invented persisted/hash query**. Existing Review code has catalog-only UI + Agent → Task API → configured corporate read-only HTTPS facade. A230R3.37 all 7 contract gates GREEN, Core V4 frozen.

### Objective: ONE implementation change set, not another discovery/QA marathon
Develop a minimal **maintainable, read-only, server-side SberProject connector** that can be deployed *after* the security/IT owner approves the identity and source access. Prioritize a safe, operator-configurable connector, with **no dependency on invoking the local GigaCode skill in production**. GigaCode may implement application source code per owner's current direction. Avoid appending diagnostic scripts or asking user to paste passwords into chat.

### Engineering steps (owner change, one vertical)
1. First read the current Review code + `po-agent-platform-v2/docs/P32_SBEPROJECT_CATALOG_CONTRACT.md` + local `.gigacode/skills/sbt-project` for **the exact registered operation** `productVersionListByPage`, GraphQL transport headers and response shape. Use **only** the verified registered operation syntax/hash from skill; no guessed operation hash, secret, domain fallback or tenant scan. Treat `OLP.78` as the canonical displayed ID, not an invented UUID.
2. Implement the smallest HTTPS adapter endpoint meeting the existing `SBERPROJECT_CATALOG_READ_URL` contract. A maintained operator-approved OIDC confidential service identity **must** be provisioned by SberTech IT/security. Where that has not yet happened, implement only a **disabled-by-default config path and typed `AUTH_REQUIRED`/source-unavailable state**; never simulate a working source. Make OIDC token acquisition/renewal modular, with credentials from a secure runtime provider (not Git, `.env.example`, browser, shared-keychain, command args or logs). TLS verification on and corporate CA approved by IT. No `verify=False`, `-k`, bypass SSO/MFA or raw cookie reuse.
3. Normalize only `id/versionNumber/workflowStatus/beginDate/endDate/releaseDate/owner`; page size <=20, paginate using verified source capabilities and preserve total/has_more/next_offset, never claim full catalog from first page. If source cannot reliably paginate, return typed INCOMPLETE instead of truncation-as-complete. OLP/DMS only, bounded requests, read-only. No issueKey/percentDone/membership until the SberProject data owner confirms the bridge.
4. Connect adapter to existing Task API via the already defined facade, and provide a short operator runbook with non-secret configuration **names** and a precise corporate IT approval checklist (approved service client/permissions/CA/endpoints). Confirm the running 8004/8241 stack cannot claim source-ready before actual approval.
5. Targeted unit/contract tests and frontend build + baseline-aware regression **once**, no unlimited test loop; frozen Core V4 6/6. Single commit or small cohesive commit series only if code/tests are GREEN; leave unrelated dirty/untracked files untouched. Do not push secrets. One report `po-agent-platform-v2/qa_reports/P32_SERVER_CONNECTOR_IMPLEMENTATION.md` and STOP.

### Acceptance / stops
- **`CONNECTOR_IMPLEMENTED_PENDING_APPROVAL`** is valid if adapter+tests work with *safe controlled fixtures* but real OIDC service identity/CA/access is not provisioned. This is not LIVE_GREEN.
- **`LIVE_GREEN`** only after an approved authorized service credential provider is present, **one** bounded REAL OLP and DMS HTTP check succeeds (not synthetic), and the normal running UI shows real source-grounded version rows, dates, statuses, paging.
- If API contract requires undocumented operation not in local skill or corporate policy disallows service integration, stop with precise `IT_APPROVAL_REQUIRED`, identify the single decision/approval needed, do not invent a workaround.
- Never change Core V4, never claim membership link as proven or show zero tasks because no AS21 issueKey exists.

**After delivery: one independent QA on the committed owner change, then move to data-owner linkage request. Do not re-run A230R3.31–38.**
