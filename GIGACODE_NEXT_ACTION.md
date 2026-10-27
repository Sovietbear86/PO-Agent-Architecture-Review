# GigaCode — CURRENT NEXT ACTION

## A230R3.6-PUBLIC-SYNC-PREFLIGHT — independent release-delta audit

**QA / AUDIT ONLY.** No product code edits, merges, force pushes, branch rewrites, Public writes, commits or AS21 mutations. Leave existing dirty files alone. Verify fresh remote HEAD for all compared branches. Report and STOP. Agent Core V4 six frozen files must remain byte-identical to checkpoint `6fb335d`.

### Inputs / frozen evidence
- Working Review: `Sovietbear86/PO-Agent-Architecture-Review`, branch `feat/core8-real-query-hardening-v2`. Latest A230R3.5 independent GREEN at TESTED_HEAD `ceac9fe` (use actual remote HEAD and do not hardcode).
- The integrated gate was **conditionally** GREEN: all observed critical bounded A/B comparisons match REAL AS21, V4 81 + blast 297, Task API SWTR 69, frontend build 0, UI six scenarios, Core 6/6 unchanged. Four further E2E cases were **blocked by LLM 429**, not verified; several separately open pre-existing issues remain.
- Public: `Sovietbear86/PO-Agent-Architecture-Public`, `main` currently contains bundled sanitized MCP-SWTR via merged PR #2.
- Public PR #3 `feat/gigacode-public-deploy-health-skills` is still OPEN/DRAFT and **not merged**: it contains rewritten DEPLOYMENT.md, GigaCode deploy and health-check skills, offline health tool/tests, CI. Avoid overwriting, duplicating or unintentionally merging untested PR #3.
- Permission to publish **sanitized** MCP-SWTR source exists, not permission to expose credentials, corporate identifiers, raw worklogs or employee data.

### Audit gates
1. Independently confirm remote Git HEADs/branches, working tree status and PR #3. Enumerate precise Review delta relevant to A230R3.1–R3.4 since last Public sync, and all related new tests/skills/Task API, MCP changes. Differentiate application production code vs sanitized Public-specific config/docs. Do not just merge entire Review history.
2. Scan all proposed files + cumulative Public target history for tokens/private keys/JWT, .env, real host/IP, corporate PII, unsafe endpoints and internal auth/session artifacts. Do not print secret values; redact evidence. Inspect Public current `clean-public-release` vs Public `main`; no direct cherry-pick if it would include private content.
3. Prepare exact **sanitized file-level patch plan** (paths, operations, source SHA, target refs, deidentification needed) for owner. Identify conflicts between Review code and Public PR #3, especially `mcp-swtr/mcp_server.py`, requirements, skill discovery, `DEPLOYMENT.md`, `GIGACODE.md`, health-check expectations (48 → 49 tools).
4. Check that all A230R3.1–R3.4 live code paths are present in the public target plan without hidden GitVerse path, old gitlink or missing imports. Core V4 6/6 must stay frozen; do not copy local secrets or QA reports with sensitive source facts.
5. Outline independent tests for the future Public migration PR: Python/runtime build, MCP tools count, Task API, Agent V4, UI, sanitizer, Docker (mark NOT TESTED if unavailable), fresh-clone REAL AS21 A/B, GigaCode skills and all relevant regression suites.
6. Distinguish resolved functional changes from **four 429-blocked E2E scenarios** (release condition, not GREEN); open issues: LLM stability; creation-date grammar; unfinished all-date sprint totals; QualityPage JSON; session auth/ownership if still applicable. Never claim these closed.
7. Deliver report IN CHAT ONLY: exact HEADs, compare matrix and security verdict, conflicts, stepwise implementation sequence, release blockers vs explicitly conditional follow-ups, exact verification requirements. No code changes. STOP.

### Short command
Run A230R3.6-PUBLIC-SYNC-PREFLIGHT from GIGACODE_NEXT_ACTION.md: QA-only file-by-file delta/security/PR #3 conflict audit, no code edits or merges. Return sanitized migration plan and STOP.
