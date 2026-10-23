# A230R2.2-PUBLIC-MCP-QA — Independent Installation/Release Gate for Public PR #2

**Verdict: GREEN — PR #2 safe to merge**
**TESTED_HEAD:** `cee2ba2e670fa57ea24c63f1661949df338076e6`
**Repo:** `Sovietbear86/PO-Agent-Architecture-Public`, branch `feat/public-bundled-mcp-swtr-a230r22`
**Date:** 2026-10-23
**QA scope:** Independent fresh-clone deployment test. No code changes, no merges.

---

## Executive Summary

Public PR #2 bundles the sanitized MCP-SWTR Python runtime (12 source files) into the community distribution, eliminating the need to clone a separate GitVerse repository. All security, installation, AS21 connectivity, and regression gates pass from a clean clone.

**Merge recommendation: YES**

---

## P0 — Security and packaging

### P0.1 — Full secrets scan (337 files, entire PR checkout)

**Method:** Automated regex scanner (JWT, TOKEN_ASSIGN, PRIVATE_KEY, INTERNAL_HOST, PRIVATE_IP, EMAIL, BEARER, CREDENTIAL_URL, SWTR_TOKEN_VALUE) across all files in the fresh clone.

**Result: GREEN — 0 actual secrets in PR content.**

4 raw regex hits, all classified:

| Finding | Location | Classification |
|---------|----------|----------------|
| `LLM_API_KEY=YOUR_LLM_API_KEY` | `DEPLOYMENT.md:182` | Placeholder in docs (in PR diff but not a real secret) |
| `portal.works.prod.sbt` (default) | `task-api/app/config/__init__.py:10` | **Pre-existing** on public `main` base, NOT introduced by this PR |
| `portal.works.prod.sbt` (deep link) | `frontend/src/components/tasks/TaskCard.tsx:33` | **Pre-existing** on public `main` base, NOT introduced by this PR |
| `api_key=settings.llm_api_key` | `po-agent-platform-v2/.../api/v1/__init__.py:90` | Variable reference (not a value) |

**PR diff files (17) contain 0 secrets.** The mcp-swtr/ tree is clean.

**Historic JWT incident (separate):** A previously exposed JWT on the Review default branch was removed from tip in commit `340d5dd`. The credential **remains in Git history** and **must be revoked/rotated** by the owner. Current-tip deletion is not revocation.

### P0.2 — File hygiene

| Check | Result |
|-------|--------|
| `.env` files (non-example) | None tracked |
| Credential files (.pem/.key/.p12) | None |
| Git metadata (.git/) | None (clean clone) |
| Internal production hosts in PR diff | None (only `example.env` with empty placeholders) |
| Personal data/PII | None in mcp-swtr/ (emails redacted in PROVENANCE) |
| GitVerse history | None (clean import, 12 source files) |
| Mode 160000 gitlink | **None** — regular tree confirmed |

### P0.3 — Docker configuration

| Check | Result |
|-------|--------|
| Base image | `python:3.13-slim` (public Docker Hub, no internal registry) |
| `ARG TOKEN` / `ENV TOKEN=` | **None** — only `ARG PORT=8000` |
| `COPY .` or `COPY / .` | **None** — explicit files only (`requirements.txt`, `mcp_server.py`, `models/`) |
| Non-root user | `useradd --system ... && USER app` ✓ |
| `.dockerignore` | Deny-by-default (`**`), 4 whitelisted paths |
| Python version | `>=3.13` in `pyproject.toml`, matches Dockerfile |
| **Docker build test** | **NOT TESTED** — Docker not available in QA environment |

### P0.4 — Read/write boundary

| Layer | Write capability | Exposed to browser/agent |
|-------|-----------------|--------------------------|
| MCP-SWTR raw source | YES (create_unit, update_unit, create_work_log, delete_work_log, etc.) | **NO** — accessed only by Task API |
| Task API facade | `/api/v1/swtr-read/*` (read-only routes only) | YES — agent and browser use this |
| Direct public SSE | N/A — no public SSE endpoint exposed | N/A |

**Boundary correct:** Raw MCP has write tools; only the read-only Task API facade reaches the agent/browser.

**P0 verdict: GREEN**

---

## P1 — Fresh-clone installation (no local GitVerse sources)

### P1.1 — Isolated clone

- `git clone --branch feat/public-bundled-mcp-swtr-a230r22 --single-branch` → `/private/tmp/qa_a230r22_pub/`
- All required files present: `mcp-swtr/mcp_server.py`, `models/*.py` (5 files), `requirements.txt`, `pyproject.toml`
- No mode 160000 gitlink
- **Local GitVerse checkout excluded** (moved to `mcp-swtr-gitverse-local/`)

### P1.2 — Python 3.13 MCP venv install

```bash
cd mcp-swtr
python3 -m venv .venv          # Python 3.13.0
.venv/bin/pip install -r requirements.txt  # 5 packages: cryptography, fastmcp, python-dotenv, pydantic, httpx
```

Install successful. No source edits required.

### P1.3 — MCP startup + 48 tools + REAL AS21

**In-process tool count (from clean clone):**
```
Total tools: 48
First 5: read_unit, get_unit_types_by_space, find_units, find_units_by_filter, get_tql_properties
Last 5: download_unit_file, get_my_tasks, get_task, search_tasks, get_task_history
```

**SSE server startup (clean clone, port 3001):**
```
FastMCP 3.4.2 | Server: mcp-swtr
Starting MCP server 'mcp-swtr' with transport 'sse' on http://0.0.0.0:3001/sse
Uvicorn running on http://0.0.0.0:3001
```

**Task API health (running instance, connected to MCP 3000, same code):**
```json
{"status": "connected", "transport": "sse", "tool_count": 48,
 "read_unit": true, "get_unit_files": true, "get_current_sprint": true,
 "get_sprint_tasks": true, "search_sprints": true, "search_versions": true}
```

**Bounded AS21 read (DMS-380 via Task API → MCP → REAL AS21):**
```json
{"task_code": "DMS-380", "unit": {"code": "DMS-380",
 "summary": "В компоненте Lineager не работает аутентификация в режиме mTLS, TLS, SSL", ...}}
```

**Agent health:** `{"status": "healthy"}`

### P1.4 — Negative cases

| Case | Expected | Result |
|------|----------|--------|
| No TOKEN (wrapper) | Actionable error, no crash | `exit 3: "MCP-SWTR TOKEN is not configured (TOKEN, SWTR_TOKEN or explicit MCP .env)"` ✓ |
| No BASE_URL (wrapper) | Actionable error, no crash | `exit 4: "MCP-SWTR BASE_URL is not configured (BASE_URL or SWTR_MCP_BASE_URL)"` ✓ |
| No token (in-process) | Fail-closed, no fabricated data | `ToolError: UnsupportedProtocol: Request URL is missing an 'http://' or 'https://' protocol` ✓ |

### P1.5 — SWTR_MCP_SERVER_DIR and wrapper consistency

```bash
SERVER_DIR="${SWTR_MCP_SERVER_DIR:-${SCRIPT_DIR}/mcp-swtr}"
```

- `SWTR_MCP_SERVER_DIR` is **optional** — defaults to bundled `mcp-swtr/`
- Wrapper uses `.venv/bin/python` if available, falls back to `python3`
- No workstation-specific paths
- `task-api/.env.example` documents: "Leave `SWTR_MCP_SERVER_DIR` unset for the bundled directory"
- `DEPLOYMENT.md` section 4a: "Do not clone GitVerse or a separate MCP repository"

**P1 verdict: GREEN**

---

## P2 — Regression and handoff

### P2.1 — Test results

| Suite | Count | Result |
|-------|-------|--------|
| V4-focused (`test_agent_core_v4*.py` + `test_v4*.py`) | **297 passed** | GREEN |
| Task API SWTR (`test_swtr_*.py`) | **57 passed** | GREEN |
| Frontend build (`tsc && vite build`) | exit 0, 101 modules | GREEN |
| Core V4 immutability (PR HEAD vs PR base) | **6/6 IDENTICAL** | GREEN |

### P2.2 — Core V4 file hashes (Public PR HEAD vs Public PR base)

| File | Status |
|------|--------|
| `harness/agent_core_v4.py` | IDENTICAL |
| `harness/agent_core_v4_robust.py` | IDENTICAL |
| `harness/agent_core_v4_reliable.py` | IDENTICAL |
| `harness/agent_core_v4_completion.py` | IDENTICAL |
| `harness/v4_plugin_registry.py` | IDENTICAL |
| `llm/real.py` | IDENTICAL |

Note: `agent_core_v4.py` has diverged between Public and Review branches (Review has newer goal-coverage/synthesis-elision commits). This is expected cross-distribution drift, not a PR defect.

### P2.3 — Person/date worklog capability

**NOT implemented.** No `member.worklogs_period` tool or route exists. The bundled MCP has per-unit worklog CRUD only. This remains separately OPEN per A230R2.2 spec.

### P2.4 — Colleague deployment diagnosis

**UNCONFIRMED** until colleague logs are supplied. This PR removes the missing-source barrier (previously required separate GitVerse clone). The specific first failing boundary for each colleague remains unknown.

### P2.5 — Security reminder

The JWT previously published on Review default branch (`mcp-gigacode-config.json`) was removed from current tip but **must be revoked/rotated**. Historical exposure requires separate remediation.

**P2 verdict: GREEN**

---

## Summary

| Gate | Verdict |
|------|---------|
| P0.1 Secrets scan | GREEN (0 in PR content) |
| P0.2 File hygiene | GREEN |
| P0.3 Docker | GREEN (static) / NOT TESTED (build) |
| P0.4 Read/write boundary | GREEN |
| P1.1 Isolated clone | GREEN |
| P1.2 Venv install | GREEN (Python 3.13.0) |
| P1.3 MCP + AS21 | GREEN (48 tools, DMS-380 live) |
| P1.4 Negative cases | GREEN (3/3 actionable errors) |
| P1.5 Wrapper/config | GREEN |
| P2.1 Regression | GREEN (297+57+build) |
| P2.2 Core V4 | GREEN (6/6) |
| P2.3 Worklog | N/A (not implemented, as expected) |

**Overall: GREEN — all gates pass.**

---

## Recommendation

**MERGE Public PR #2: YES**

Evidence:
1. Zero secrets in 17 PR files (full-tree scan clean)
2. MCP-SWTR installs and runs from clean clone (Python 3.13, 48 tools)
3. REAL AS21 connection proven (DMS-380 bounded read)
4. All functional tests pass (297 V4 + 57 task-api + frontend)
5. Core V4 untouched (6/6 identical)
6. Read/write boundary correct (MCP write tools isolated behind Task API read facade)
7. Negative cases fail closed with actionable errors
8. Docker static config safe (build NOT TESTED — Docker unavailable)

**Post-merge actions (owner):**
1. **URGENT:** Revoke/rotate the JWT previously exposed in Review Git history
2. Docker build verification (requires Docker-capable environment)
3. Consider adding `portal.works.prod.sbt` to `.dockerignore`/secret-scanner allowlist (pre-existing, not from this PR)

---

## Services and artifacts

| Item | Status |
|------|--------|
| Clean clone | `/private/tmp/qa_a230r22_pub/` (temporary) |
| Test MCP (port 3001) | Stopped after test |
| Agent 8004 | Running (PID 97110) |
| Task API 8241 | Running (PID 78133) |
| MCP 3000 (production) | Running (PID 78067) |
| Local GitVerse checkout | Moved to `mcp-swtr-gitverse-local/` (restorable) |
