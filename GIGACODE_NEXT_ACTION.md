# GigaCode — CURRENT NEXT ACTION

## A230R2.2-PUBLIC-MCP-QA — Independent installation/release gate for Public PR #2

**STRICTLY QA/forensics only.** GigaCode must NOT change production, tests, docs, config, Git history, Core V4 or PR code; no merge, publish, force-push or write-capable MCP tools. At RED record first failing boundary and stop. Only non-sensitive QA report may be committed to its own working-review report branch if necessary.

### Target
- Public repo: `Sovietbear86/PO-Agent-Architecture-Public`, **draft PR #2** `feat/public-bundled-mcp-swtr-a230r22` -> `main`.
- Initial tested candidate `cee2ba2e670fa57ea24c63f1661949df338076e6`; fetch and record **current HEAD** before testing.
- Source provenance: sanitized Review merge `c91f8ed`; GitVerse `ea7f75f`; 12 tracked source files, Python runtime-only, plus community README/PROVENANCE and 3 updated deployment/config docs (17 changed files).
- Public source publication explicitly approved subject to no secrets.
- Prior working Review Core V4 and A230R2.1 GREEN are not modified. Compare Public core blobs to `main` before and after; never compare across different distribution branches as though identical.

### P0 — Security and packaging
1. Run `python scripts/prepublish_scan.py` against the full PR checkout AND independent whole-tree secret/JWT/token/PII scanner (including commit diff, lock/config/docs). Report only filenames and classifications, NEVER sensitive values; zero permitted actual leaks.
2. Validate no `.env`, credential-bearing files, corporate personal identifiers, internal production hosts, private IPs or raw GitVerse history; inspect Python MCP source descriptions and `pyproject.toml` sanitized fields.
3. Validate `.dockerignore` deny-by-default, Dockerfile no build-time secrets, Python >=3.13. If Docker exists test build with a dummy sentinel local .env (no real tokens) and confirm it is not included in the image; otherwise mark Docker build NOT TESTED.
4. Verify absence of read/write boundary inversion: bundled raw MCP-SWTR includes write tools, **only Task API facade is exposed to browser**. No direct public SSE exposure.

### P1 — Fresh-clone install (do not rely on old local checkout)
1. Make an isolated temp clone of Public PR HEAD (exclude existing local `mcp-swtr` and GitVerse checkout). Confirm all required `mcp-swtr/mcp_server.py`, `models/*`, `requirements.txt` exist and no mode 160000 gitlink.
2. Install Python 3.13 MCP venv exactly per `DEPLOYMENT.md`; Task API venv and frontend. Test `mcp-swtr-wrapper.sh` without token/base URL (must fail with safe actionable error), then with authorized values passed only from environment. No source edits.
3. In local stdio mode prove Task API `GET /health` and `GET /api/v1/swtr-read/health`, MCP 48 tools (unless documented variation), agent `/api/v1/health`, browser query. Record all HTTP codes and timings. If authorized network and token available, perform ONE bounded read with AS21 independent oracle A/B; never claim source GREEN without live evidence.
4. Negative cases: absent token, wrong BASE_URL, no VPN/AS21 network, MCP import path unavailable, bad Python runtime, sse mode with missing server. Must return explicit error rather than fabricated 0 tasks.
5. Validate that `SWTR_MCP_SERVER_DIR` is optional and wrapper uses bundled folder, env path/docs consistent; no user workstation-specific paths.

### P2 — Regression and handoff
- Full public V4 tests + relevant Task API/SWTR tests; frontend TypeScript build. Record exact executed counts and preexisting baseline failures. Core untouched.
- Report actual specific first failing boundary for colleague deployments is **UNCONFIRMED until their logs are supplied**; this PR only removes missing-source barrier.
- Separately remind owner: the JWT previously published on Review default branch was removed from current tip but must be revoked/rotated and historical exposure remediated; do not print or reuse it.
- Output `A230R2_2_PUBLIC_MCP_QA.md` report with TESTED_HEAD, per-gate GREEN/RED, missing checks, command classifications, and PR #2 merge recommendation. Report only, no implementation.
- **Do not consider person/date worklog capability implemented**; `member.worklogs_period` remains separately OPEN.

### Short command
Run A230R2.2-PUBLIC-MCP-QA from GIGACODE_NEXT_ACTION.md. Independent QA only on the exact Public PR #2 HEAD; build from clean checkout, verify AS21 path and secret safety; no code edits or merges.
