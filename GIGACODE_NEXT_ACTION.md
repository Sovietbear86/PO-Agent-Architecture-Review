# GigaCode — CURRENT NEXT ACTION

## A230R2.2-MCP-IMPORT-QA-R2 — Corrected public-permission gate & fresh PR QA

**GigaCode is QA-ONLY.** No app, Docker, test, Core, configuration, Git history, or PR code edits. No merge, no force-push, no deletion, no token printing. May commit a report only on its own report branch if no sensitive information is included.

### CRITICAL product decision (supersedes stale P0)
**THE OWNER EXPLICITLY AUTHORIZED PUBLIC PUBLICATION OF SANITIZED MCP-SWTR SOURCE.** Both Review and Public repos may remain PUBLIC. It is a QA ERROR to mark RED merely because GitHub API returns `private=false`. The correct P0 gate is **NO SECRET / NO SENSITIVE UNREDACTED CONTENT**, plus source safety and runtime viability.

### Separate existing credential incident
A pre-existing public default-branch file `mcp-gigacode-config.json` contained a long, structurally valid JWT under `TOKEN`. Owner has deleted it from the latest `clean-public-release` tree in commit `340d5dd`; **the credential remains in Git history and caches until revoked and separately remediated**. Do not copy, display, decode into logs, or make the token appear in any QA report. Owner must revoke/rotate it independently. Audit and classify any other exposed credential-adjacent files or history using redacted metadata only. History rewrite is OUT OF SCOPE.

### QA R2
1. Fetch current PR #3 head `chore/vendor-mcp-swtr-a230r22` and base `feat/core8-real-query-hardening-v2`; record full SHA and ensure tests run on THAT head, not original `67f19d7`. Previous report `AGENT_CORE_V4_MCP_IMPORT_QA_A230R22.md` tested the old import SHA and used an obsolete PRIVATE-only instruction: **superseded**.
2. Check full PR staged-tree content for credential tokens, JWTs, passwords, secret-bearing URLs, corporate PII, real production hosts/IP, personal data, Docker/image-build secret leaks, `.env`, and private files (no secret values in report). Verify GitVerse only provided tracked clean snapshot and provenance. Compare original source hashes, note documented redactions AND subsequent owner changes.
3. Validate newest hardening files and functionality: `mcp-swtr/Dockerfile` Python >=3.13, no build-time token ARG/ENV, no `COPY .`, public-safe base image; `mcp-swtr/.dockerignore` deny-by-default, copied paths; README runtime-only auth. If Docker exists, perform safe Docker build and sentinel exclusion check WITHOUT real tokens. If Docker unavailable report NOT_VERIFIED, not GREEN.
4. Confirm 6/6 EXACT frozen Core files by byte hash vs `6fb335d` (canonical list: agent_core_v4.py, agent_core_v4_robust.py, agent_core_v4_reliable.py, agent_core_v4_completion.py, v4_plugin_registry.py, llm/real.py). No unauthorized application changes.
5. Run focused MCP startup/48-tool inventory; Task API SWTR tests + full V4 regression and frontend build if environment permits. State exact executed counts; classify pre-existing failures separately. Do not mistake old still-running MCP process for proof of Docker newly built from PR head.
6. Public colleague AS21 deployment read-only diagnostics: `PO-Agent-Architecture-Public` currently omits MCP source; analyze actual setup path vs `SWTR_MCP_SERVER_DIR`/SSE URL, `SWTR_TOKEN`, reachability, `AS21_MODE=task-api`, health endpoint and dependency/runbooks. Root cause UNKNOWN without colleague logs; do not infer a confirmed cause. Do not change Public.
7. Separate exposure audit (redacted only): confirm latest default branch no longer tracks `mcp-gigacode-config.json`, flag historic JWT exposure and need for immediate rotation, inspect other default-branch credential-adjacent paths `set_cookie.py`, `setup_jira_token.py`, tracked `.venv`/`__pycache__`, never print their values or commit confidential content.

### Output
Issue new report `po-agent-platform-v2/qa_reports/A230R2_2_MCP_IMPORT_QA_R2.md` with exact TESTED_HEAD, P0-P2 case verdicts, build & test evidence, blocking findings and recommendation PR #3 MERGE YES/NO. **Do not mark RED solely for public visibility.** Existing exposed JWT is separately an urgent security incident; explain that current-tip deletion is not revocation/history cleanup. Do NOT merge.

### Short command
Run corrected A230R2.2-MCP-IMPORT-QA-R2 from this file. QA only, source publication public is authorized, stop for exposed secrets, not for repository visibility. Use latest PR head. Report; no fixes.
