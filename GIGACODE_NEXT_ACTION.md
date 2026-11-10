# GigaCode — CURRENT NEXT ACTION

## A230R3.38-P32-SBERPROJECT-LIVE-CONNECTOR-HANDOFF

### Starting point (10.11.2026)
A230R3.37 independently **PASSED all 7 contract gates**, TESTED_HEAD `3b987ba`, verdict **CATALOG_CONTRACT_GREEN_LIVE_BLOCKED**. Offline source façade, agent proxy, frontend OLP/DMS, pagination/typed errors, no fake AS21 membership, V4 frozen all pass. GigaCode report: `po-agent-platform-v2/qa_reports/P32_CATALOG_VERTICAL_CONTRACT_QA.md`. Do NOT repeat this QA.

### Objective
Unblock **real authorised** read-only sbeproject version catalogue connection in running PO Agent. Do not fabricate a local mock or another preflight series. Existing GigaCode local skill `.gigacode/skills/sbt-project` can authenticate/read `versions OLP`, but published agent must not depend on executing a personal GigaCode CLI or leaking its sessions.

### Bounded task — ONE pass
1. Inspect existing `sbt-project` skill **locally** and the approved corporate environment docs for a supported **server-side read-only SberProject connector/OIDC token provider**, including registered GraphQL operation contract and official TLS CA trust. Reuse a current approved adapter if one exists; **do not** build guessed query hashes or bypass SSO/TLS.
2. Compare observed local live `versions OLP` return with expected normalized REST schema in `po-agent-platform-v2/docs/P32_SBEPROJECT_CATALOG_CONTRACT.md`. Record exact safe field mapping for `id/versionId/versionNumber/workflowStatus/beginDate/endDate/releaseDate/owner`, `meta.has_more/next_offset/total`; distinguish display code `OLP.78` and internal ID. Do not export raw auth/session data.
3. If an already approved, deployable HTTPS connector **exists** with proper OIDC renewal and strict CA verification, supply its documented integration method to the owner (service URL as non-secret reference, config names, required permissions, operator steps). User secrets must be entered via approved secure provider, never chat/log/repo. Do not silently configure credentials.
4. If no approved connector exists, give `CONNECTOR_REQUIRED` and ONE concrete implementation contract for a small read-only adapter: existing registered operation(s), secure OIDC, company CA, 20-row pagination + scalar-only normalized DTO; identify which internal team/service owner must authorize it. **Do not present the existing frontend/API as live.**
5. The release membership linkage remains `DATA_OWNER_REQUIRED`; not part of this task. Do not run broader task graph scans or re-open AS21 parity.

### Output / exit
Write exactly one untracked `po-agent-platform-v2/qa_reports/P32_LIVE_CONNECTOR_DECISION.md` with verdict `CONNECTOR_READY` (actual approved endpoint identified, not simply that CLI works) or `CONNECTOR_REQUIRED` (who must provision what). No code edits, no commits, no service restarts, no Core V4 changes. One short report then STOP. Next owner action: actual connector/secret-provider implementation, followed by ONE live end-to-end check. **No more independent diagnostic loops.**
