# GigaCode — NEXT ACTION / EXTERNAL BLOCKER

## A230R3.40 — SberProject auth decision & IT handoff (NO new QA cycle)

### State as of 2026-11-10
A230R3.39 server connector implemented locally with verdict `CONNECTOR_IMPLEMENTED_PENDING_APPROVAL` (owner reported commits `da571cc`, `620a1e4`; do NOT assume pushed). Subsequent GigaCode report `P32_SBERPROJECT_INTERACTIVE_OIDC_FEASIBILITY.md`, commit `c9f7008`, verdict `CAPABILITY_PRESENT_LOCAL_USER_PATH_BLOCKED`: SberProject public user client supports authorization code+refresh token but its redirect URI is tied to `https://project.sbertech.ru/` with no localhost PKCE registration; password flow would put personal AD credentials into the app and is NOT authorized. Real host TLS currently fails CA validation in Node/Python (corporate `SberTech AD Subordinate Certification Authority` chain not in approved runtime trust), and no approved confidential service client has been provisioned. Core V4 unchanged. Existing local GigaCode skill login is **NOT** permission to transfer keychain credentials/tokens into the application.

### PO decision
**STOP implementation and repetitive testing pending external IT/security decision.** GigaCode must not change auth settings, probe grant types, bypass TLS, copy credentials, or try to reuse an existing browser session. No speculative workarounds. Do not put secrets/CA private keys in repo.

### Exact IT request / decision (send by human, not automate)
Request a documented read-only SberProject integration for local/single-user PO Agent:
1. Preferred: dedicated OIDC confidential service client under SBT-TNT, scoped only to registered `productVersionListByPage` query for OLP/DMS release versions, with secure client credential issuance, refresh/rotation and approved usage policy. Or confirm whether a public PKCE client with **explicit localhost loopback redirect registration** is permitted for single-user desktop use. Do **not** ask for enabling resource-owner-password credentials grant.
2. Provide official corporate SberTech AD CA chain and instructions for Node/Python trust; mandatory TLS verification stays enabled.
3. Confirm endpoint/origin, required `x-dspc-tenant: SBT-TNT` / GraphQL registered operation headers, read scopes, limits, and who operates the secret provider, plus process for future token expiry/rotation.

### Trigger to resume
Only after IT issues the documented approval and approved non-secret connection metadata: configure the already-built connector, one real bounded OLP+DMS catalogue read, then one UI smoke, one independent QA. Any user credentials or certificates installed only via corporate-approved mechanisms, **never** shared in chat/Git. If no authorization is granted, keep releases UI typed `SOURCE_UNAVAILABLE` rather than fabricated catalogue. Release↔AS21 membership remains separate `DATA_OWNER_REQUIRED`.

**GigaCode action now: HOLD / STOP.** No tests or commits until approval arrives.
