# A230R2.2-MCP-IMPORT-QA-R2 — Independent QA Re-gate (Public Allowed)

**Verdict: GREEN — PR #3 safe to merge**
**TESTED_HEAD:** `11de894` (origin/chore/vendor-mcp-swtr-a230r22)
**Date:** 2026-10-23
**QA scope:** NO code changes. Read-only verification + tests only.

---

## Executive Summary

Publication of MCP-SWTR source in a public repository is **officially authorized**. The PR introduces 47 files under `mcp-swtr/` (replacing the orphan gitlink) with 3 security-hardening commits over the initial import. All safety, functional, and regression gates pass. No secrets, no internal credentials, no Core V4 modifications, no Docker build-time credential persistence.

**Merge recommendation: YES**

---

## P0 — Public-source safety (BLOCKING)

### P0.1 — Full secrets scan (all 46 files, entire PR tree)

**Method:** Automated regex scan (JWT, TOKEN_ASSIGN, PRIVATE_KEY, INTERNAL_HOST, PRIVATE_IP, EMAIL, SWTR_TOKEN, BEARER, CREDENTIAL_URL) across every file in `mcp-swtr/` on PR HEAD.

**Result: CLEAN — 0 actual secrets found.**

54 raw regex hits, all classified as false positives:

| Category | Count | Classification |
|----------|-------|----------------|
| `SWTR_TOKEN` (regex `swtr[0-9a-zA-Z_-]{16,}`) | 36 | API path segments: `swtr_task_tracker_plugin`, `swtr_wiki_migrator_plugin` — plugin name identifiers in REST paths, not token values |
| `EMAIL` / `INTERNAL_HOST` | 14 | All emails redacted to `redacted@sbertech.ru` per PROVENANCE.md; `sberbank.ru` domain appears once in api-docs.json schema example |
| `PRIVATE_IP` (10.0.0.1) | 2 | Schema example in api-docs.json line 64088/64113 — CI profiler response example with placeholder host, not a real internal IP |
| Lock file `10.` matches | 4 | Version numbers (10.0.1, 10.4.0, 4.10.0) in uv.lock / package-lock.json |

**Lock file registry audit:**
- `uv.lock`: all URLs from `files.pythonhosted.org` (public PyPI) — no internal registry
- `package-lock.json`: all URLs from `registry.npmjs.org` (public npm) — no internal registry

### P0.2 — Tracked file hygiene

| Check | Result |
|-------|--------|
| `.env` files tracked | Only `example.env` with empty placeholders (`TOKEN=""`, `BASE_URL=""`, `PORT=8000`) |
| `.git` metadata | None |
| Certificates/keys | None |
| Test dumps/credentials | None |
| GitVerse history | None (clean import, PROVENANCE.md documents source SHA) |
| Gitlink mode 160000 | **None** — `mcp-swtr` is a regular tree (confirmed via `git ls-tree`) |

### P0.3 — Dockerfile security

```dockerfile
FROM python:3.13-slim          # Public-safe base, no internal registry
ARG PORT=8000                  # Only port arg, no TOKEN/SECRET args
# Explicit COPY only:
COPY requirements.txt ./requirements.txt
COPY mcp_server.py ./mcp_server.py
COPY models/ ./models/
# Non-root user
RUN useradd --system ... && USER app
CMD ["python", "mcp_server.py"]
```

**Checks:**
- No `ARG TOKEN` / `ARG SECRET` / `ENV TOKEN=` — ✅
- No `COPY .` or `COPY / .` — ✅ (explicit files only)
- No build-time credential persistence — ✅
- Non-root user — ✅
- Public base image (`python:3.13-slim` from Docker Hub) — ✅

### P0.4 — .dockerignore

```
**                    # Deny-by-default
!Dockerfile
!requirements.txt
!mcp_server.py
!models/
!models/*.py
```

**Verification:** Only 4 file types sent to build context. `.env`, `.git`, `api-docs.json`, `npx-version/`, `uv.lock`, `PROVENANCE.md`, `README.md`, `example.env`, `pyproject.toml`, `.gitignore` all excluded from Docker build. ✅

### P0.5 — Source parity and provenance

- `PROVENANCE.md` documents source SHA `ea7f75f`, 6 files redacted (PII emails → `redacted@sbertech.ru`), 38 byte-identical
- 3 intentional changes: `Dockerfile` (hardened), `.dockerignore` (new), `README.md` (Docker runtime auth docs)
- No frozen Core edits in PR diff

**P0 verdict: GREEN**

---

## P1 — Functional isolation and smoke

### P1.1 — Core V4 immutability

6 Core V4 files compared (PR HEAD vs main branch / PR base):

| File | SHA-256 (first 16) | Status |
|------|-------------------|--------|
| `harness/agent_core_v4.py` | `5d1c73f60179b42b` | IDENTICAL |
| `harness/agent_core_v4_reliable.py` | `a90c4c3fb2f5ae73` | IDENTICAL |
| `harness/agent_core_v4_robust.py` | `88b71ea0ac4b...` | IDENTICAL |
| `harness/agent_core_v4_pluginized.py` | `597740876d8f6275` | IDENTICAL |
| `llm/real.py` | `fc8241cd5ab4ba1e` | IDENTICAL |
| `api/v1/__init__.py` | `2f109403ce4f00ed` | IDENTICAL |

**6/6 IDENTICAL to PR base.** PR diff touches **zero** `po-agent-platform-v2/src/po_agent/` paths (confirmed by `git diff --name-only` between base and PR HEAD, filtered to `po-agent/` = empty).

Note: `api/v1/__init__.py` has evolved from checkpoint `6fb335d` due to 6 legitimate main-branch commits (goal-coverage, synthesis elision, continuation) — the MCP import did not modify it.

### P1.2 — MCP tool registry

Running service (Task API 8241 → MCP 3000 SSE): **48 tools** — matches certified baseline.

### P1.3 — Service health

| Service | Port | Status |
|---------|------|--------|
| Agent V4 | 8004 | 200 healthy |
| Task API | 8241 | 200 healthy, SSE connected, 48 tools |
| MCP-SWTR | 3000 | SSE connected |

### P1.4 — Full regression

| Suite | Result |
|-------|--------|
| V4-focused (`test_agent_core_v4*.py` + `test_v4*.py`) | **297/297 passed** |
| Task API SWTR (`test_swtr_*.py`) | **57/57 passed** |
| Frontend build (`tsc && vite build`) | **exit 0** (101 modules, 282 KB JS) |
| Full po-agent suite | 1609 passed, 23 failed (pre-existing), 11 errors (live LLM integration) |

The 23 failures + 11 errors are pre-existing on the main branch (require live LLM endpoints, specific environment state, or test-logic issues documented in prior assignments). **Zero new failures from the MCP import.**

### P1.5 — Person+period worklog tool

**CONFIRMED NOT IMPLEMENTED.** MCP source worklog tools:
- `create_work_log`, `create_work_log_range` (CRUD)
- `get_work_log(work_log_id)`, `update_work_log`, `delete_work_log` (by ID)
- Per-unit report: `report/{unit_code}`, `report/{unit_code}/sum`

No tool accepts a person/user parameter + date range for filtered worklog querying. A230R2.2 feature remains unimplemented as expected.

**P1 verdict: GREEN**

---

## P2 — Public deployment diagnostics (read-only)

### P2.1 — Current public distribution state

| Branch | `mcp-swtr` state |
|--------|-----------------|
| `origin/main` | **Absent** (no entry) |
| `origin/clean-public-release` (default) | Orphan gitlink (mode 160000, commit `c1a6b79`, **no .gitmodules**) — unusable |
| `origin/chore/vendor-mcp-swtr-a230r22` (PR #3) | 47 vendored source files (this PR) |

**Conclusion:** Current public rollout requires separately configured MCP via stdio/SSE (the gitlink is broken without .gitmodules). PR #3 will resolve this by providing actual source files.

### P2.2 — Deployment documentation

- No `DEPLOYMENT.md` exists on any branch
- `s21-task-agent/.env.example` on public branch is for a different component (S21, placeholder URLs)
- `mcp-swtr/README.md` (in PR) provides correct local setup: `example.env` → `.env`, Docker build/run instructions

### P2.3 — Colleague symptoms diagnosis

No actual logs available. **Hypothesis (not proven):** The orphan gitlink on `clean-public-release` means colleagues cloning the public repo get an empty/broken `mcp-swtr/` directory, requiring them to source MCP from a separate GitVerse checkout. PR #3 merge will eliminate this dependency.

### P2.4 — Safe diagnostic commands (for colleagues)

```bash
# 1. Check if mcp-swtr is a gitlink (broken) or real files
git ls-tree HEAD -- mcp-swtr
# 160000 = gitlink (broken), 040000 = real directory

# 2. Check if MCP is reachable
curl -s http://127.0.0.1:3000/sse | head -1
# Expect: "event: endpoint" or connection

# 3. Check Task API MCP connection
curl -s http://127.0.0.1:8241/api/v1/swtr-read/health
# Expect: {"status":"connected","tool_count":48,...}
```

**P2 verdict: GREEN (diagnostic only, no changes made)**

---

## Audit — Remaining potential leaks

| Area | Status |
|------|--------|
| Docker build context | Deny-by-default `.dockerignore`, only 4 whitelisted paths |
| Docker image layers | `--no-cache-dir` pip install, no `COPY .`, no ARG secrets |
| Git history (branch) | Linear from main + 4 import commits, no rebased secrets |
| api-docs.json (102K lines) | Schema documentation only; example IPs are placeholders; no real endpoints beyond AS21 REST paths |
| uv.lock / package-lock.json | Public registry URLs only (PyPI, npmjs.org) |
| npx-version/.npmrc.example | Uses `${NPM_TOKEN}` env var placeholder |
| npx-version/src/config.ts | Reads `process.env.TOKEN` and `process.env.BASE_URL` at runtime only |
| PROVENANCE.md | Documents redactions, no actual PII |
| .gitignore in mcp-swtr/ | Excludes `.env`, `__pycache__`, `.venv` |

**No additional leak vectors identified.**

---

## Summary

| Gate | Verdict |
|------|---------|
| P0.1 Secrets scan | GREEN |
| P0.2 File hygiene | GREEN |
| P0.3 Dockerfile | GREEN |
| P0.4 .dockerignore | GREEN |
| P0.5 Parity/provenance | GREEN |
| P1.1 Core V4 | GREEN (6/6 identical) |
| P1.2 MCP tools | GREEN (48 tools) |
| P1.3 Services | GREEN (all healthy) |
| P1.4 Regression | GREEN (297+57+build) |
| P1.5 Worklog tool | GREEN (confirmed absent) |
| P2.1 Public state | GREEN (diagnostic) |
| P2.2 Docs | INFO (no DEPLOYMENT.md, README adequate) |
| P2.3 Symptoms | HYPOTHESIS (no logs) |
| Audit | GREEN (no leak vectors) |

**Overall: GREEN — all gates pass.**

---

## Recommendation

**MERGE PR #3: YES**

Evidence:
1. Zero secrets in 46 tracked files (full automated scan + manual review)
2. Docker configuration is production-safe (no credential baking, deny-by-default context)
3. Core V4 untouched (6/6 byte-identical, zero po-agent/ paths in diff)
4. All functional tests pass (297 V4 + 57 task-api + frontend build)
5. 48 MCP tools operational via live SSE
6. Publication explicitly authorized by owner

**Post-merge actions (owner):**
- Update `clean-public-release` or `main` to include the vendored source
- Optionally add `DEPLOYMENT.md` with MCP setup instructions for public consumers
- Remove the orphan gitlink from `clean-public-release`

---

## Services left running

| Service | Port | PID |
|---------|------|-----|
| Agent V4 | 8004 | 97110 |
| Task API | 8241 | 78133 |
| MCP-SWTR | 3000 | 78067 |
| Vite frontend | 5175 | 81246 |
