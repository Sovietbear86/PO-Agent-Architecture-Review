# GigaCode — CURRENT NEXT ACTION

## A230R2.2-MCP-IMPORT-QA — Independent QA of PR #3 (NO CODE CHANGES)

**QA ONLY. GigaCode may NOT modify production, tests, Docker, configuration, Core, or the PR. On RED report first failing boundary and STOP.** Read-only test reports are allowed, but no code fixes, merges, force pushes, or Public changes.

### Scope & target
- Repository `Sovietbear86/PO-Agent-Architecture-Review`, PR #3: `chore/vendor-mcp-swtr-a230r22` → `feat/core8-real-query-hardening-v2`.
- Initial import `67f19d7` (GitVerse snapshot `ea7f75f`), owner security hardening subsequently committed:
  - `53fdab4` safer Dockerfile: Python 3.13, runtime-only creds, explicit copy paths, no internal base-image registry.
  - `c0a725c` restrictive `mcp-swtr/.dockerignore`.
  - `11de894` README Docker runtime auth and Python version.
- First record **current exact PR HEAD** via fetch; previous SHA is not the final target.
- All six frozen Core V4 files MUST remain byte-identical to checkpoint `6fb335d`.
- Previous A230R2.1 GREEN and source-audit GREEN stay independent.

### P0 — Public-source safety (blocking)
1. Scan **full changed PR tree, not just GitVerse snapshot**, for tokens, passwords, JWTs, credential URLs, email PII, private IPs, real internal hostnames and sensitive metadata. Report classification without actual secrets; specifically inspect Dockerfile, api-docs.json, source, uv.lock and npm lockfile, docs, examples, transitive auth values and provenance.
2. Verify no `.env`, `.git`, certificates, test dumps or local credentials tracked; no GitVerse history; imported code hash parity with documented exceptions ONLY, plus intentional Dockerfile/.dockerignore/README hardening.
3. Check Dockerfile contains no build-time TOKEN/ARG secret persistence, no `COPY .` or `COPY / .`; `.dockerignore` excludes `.env` (including .env.*, nested dirs) and all other source-unneeded files. Validate by inspecting actual Docker build context; if Docker available, run a safe no-credential build and prove secret sentinel file outside image. No real tokens during test.
4. Verify public-safe base image and Python >=3.13; if Docker build unavailable, mark build as NOT VERIFIED and do not claim green for packaging.
5. Confirm import is tracked normal files; no mode-160000 gitlink at mcp-swtr; provenance accurate; no frozen Core edits.

### P1 — Functional isolation and smoke
- If accessible, execute bounded non-mutating MCP startup/tool registry check on PR HEAD **with no real credential written into repo**; compare existing tool names/counts to certified baseline (48 tools, changes only if explained).
- Task API 8241, agent 8004, frontend health (read-only); no changes to working running services without controlled isolation. Full V4 tests, relevant Task API/SWTR tests, frontend build; record counts or reason not run. Only source oracle for existing, safe read calls, never worklog mutations.
- Confirm the new person+period worklog tool is STILL NOT implemented. Do not call A230R2.2 feature GREEN.

### P2 — Public deployment diagnostics (read-only)
- Recheck `PO-Agent-Architecture-Public` source/distribution: `mcp-swtr` absent in Public main; current rollout still requires separately configured MCP via stdio/SSE.
- Diagnose whether missing MCP source explains *specific* colleague symptoms only if actual logs available; otherwise label hypothesis, not proven root cause.
- Audit Public `DEPLOYMENT.md` and provided `.env.example` for correct paths, token, AS21 endpoint, transport mode, port/proxy, agent AS21_MODE, Task API response. Give exact safe commands to identify first failing connection boundary (no tokens echoed).
- Do not publish MCP to Public and do not change configuration as part of this QA.

### Deliverable & stop
Produce `po-agent-platform-v2/qa_reports/A230R2_2_MCP_IMPORT_QA.md` if safe, with TESTED_HEAD, P0-P2 GREEN/RED per gate, hash/mode manifest, build/tests, first failing boundary and safe fix recommendations. You may commit only QA report to its own report branch if needed, not the migration PR. For RED stop and do not self-fix. Explicit recommendation PR #3 merge YES/NO with evidence; no merge action.
