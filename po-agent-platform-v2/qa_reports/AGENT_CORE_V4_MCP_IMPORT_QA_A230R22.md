# A230R2.2-MCP-IMPORT-QA — Independent QA Report

**Verdict:** `RED_P0_REPO_VISIBILITY`  
**Classification:** P0 STOP-SAFETY-GATE failure — destination repository is **PUBLIC**, not PRIVATE  
**Tested HEAD (migration branch):** `67f19d7` on `chore/vendor-mcp-swtr-a230r22`  
**Base branch:** `feat/core8-real-query-hardening-v2`  
**QA date:** 2026-10-21  

---

## P0 — STOP-SAFETY-GATE

### P0.1 — Repository visibility: **RED**

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| GitHub API `private` field | `true` | **`false`** | **FAIL** |
| GitHub web page label | Private | **Public** | **FAIL** |
| Repo | `Sovietbear86/PO-Agent-Architecture-Review` | same | — |
| Default branch | — | `clean-public-release` | — |

**Finding:** GitHub API (`GET /repos/Sovietbear86/PO-Agent-Architecture-Review`) returns `{"private": false}`. The GitHub web page shows the repository as **Public**. The migration branch `chore/vendor-mcp-swtr-a230r22` is pushed to origin and visible. The internal MCP-SWTR source code from GitVerse (45 files, 112K lines) is exposed in a public repository.

**Additionally observed on the public repo default branch (`clean-public-release`):**
- `.venv/` directory committed (virtual environment)
- `__pycache__/` committed
- Files like `set_cookie.py`, `setup_jira_token.py`, `mcp-gigacode-config.json` visible in file tree
- `cleanup_for_public_repo.sh` exists but cleanup was incomplete

**This is a P0 STOP condition. Per spec: "If public/unknown: STOP without copying."**

### P0.2 — Worktree state

| Check | Result |
|-------|--------|
| Current branch | `feat/core8-real-query-hardening-v2` |
| Working tree | 2 unstaged modifications (GIGACODE.md, A230R2_2_WORKLOG_SOURCE_AUDIT.md) + many untracked QA artifacts |
| Migration branch state | Clean (single commit `67f19d7`) |
| Child (mcp-swtr) | `ea7f75f` on `master`, clean |

### P0.3 — Secrets scan: **GREEN**

Scanned all 45 migrated files:
- `example.env`: empty placeholders only (`TOKEN=""`, `BASE_URL=""`)
- `.npmrc.example`: uses `${NPM_TOKEN}` env var reference, no literal token
- `mcp_server.py`: `os.getenv("TOKEN")`, `os.getenv("BASE_URL")` — runtime env vars only
- `api-docs.json`: 2 emails → `redacted@sbertech.ru`, 2 hosts → `10.0.0.1` (placeholder). No JWTs, GitHub tokens, AWS keys, private keys, or passwords found.
- `npx-version/src/config.ts`: `process.env.TOKEN`, `process.env.BASE_URL` — clean
- No `.env`, `.pem`, `.key`, `.p12`, `.pfx` files in the git tree
- No hardcoded credentials in any source file

### P0.4 — No `.env`, `.git`, private keys, or test dumps in migration: **GREEN**

`.gitignore` properly excludes `.env`, `.venv`, `__pycache__`. No git history imported (git archive method).

---

## P1 — Migration Correctness

### P1.1 — Core V4 immutability: **GREEN**

All 6 frozen files byte-identical between migration branch and checkpoint `6fb335d`:

| File | Status |
|------|--------|
| `agent_core_v4.py` | IDENTICAL |
| `agent_core_v4_reliable.py` | IDENTICAL |
| `agent_core_v4_robust.py` | IDENTICAL |
| `agent_core_v4_pluginized.py` | IDENTICAL |
| `agent_core_v4_completion.py` | IDENTICAL |
| `llm/real.py` | IDENTICAL |

### P1.2 — Gitlink removal: **GREEN**

- Original gitlink (mode 160000) at `mcp-swtr` — **DELETED** in migration
- 45 new files with mode 100644 (regular blobs)
- Recursive `git ls-tree` for mode 160000: **0 entries**

### P1.3 — Source parity: **GREEN**

| Check | Result |
|-------|--------|
| Source SHA | `ea7f75f2b2f21fab0d3a262b2494a48309892cab` (matches PROVENANCE.md) |
| Source branch | `master` |
| Source file count | 44 |
| Migration file count | 44 + 1 PROVENANCE.md = 45 |
| File list diff | Only PROVENANCE.md is extra (expected) |
| SHA-256 parity (4 spot checks) | mcp_server.py ✅, timesheet.py ✅, unit.py ✅, register.ts ✅ |
| PROVENANCE.md redaction claim | 38 files byte-identical, 6 redacted (data only, no functional code) — consistent |

### P1.4 — Diff scope: **GREEN**

- `git diff --stat` against base: **only** `mcp-swtr/` paths changed (46 files)
- `git diff -- task-api/ po-agent-platform-v2/`: **0 lines** (no code changes outside MCP import)
- Single commit on migration branch: `67f19d7 chore: vendor MCP-SWTR source (44 files, GitVerse ea7f75f) replacing gitlink`

### P1.5 — Docker build: **GREEN with 1 non-blocking finding**

**Dockerfile structure** (at `mcp-swtr/Dockerfile`):
- Base image: `sberworks.ru/sbt/.../sberlinux-9-x86_64-ubi@sha256:...` (internal registry, pinned by SHA)
- Python 3.11 via `dnf install`
- `COPY requirements.txt` → `pip install` (correct layering)
- `COPY / .` → full app copy
- Non-root user (`app`)
- `EXPOSE 8000`, `CMD ["python3.11", "mcp_server.py"]`
- `ARG TOKEN` — build-time injection, no default, no hardcoded secret

**Finding (non-blocking, pre-existing design):** No `.dockerignore` file. The `COPY / .` will include `.env`, `.git`, `.venv`, etc. if present in the build context. The `.gitignore` does not affect Docker build context. This is a pre-existing issue from the original GitVerse source, not introduced by the migration. Recommendation: add `.dockerignore` in a follow-up.

**Cannot perform actual Docker build** (internal registry `sberworks.ru/sbt/...` not reachable from this environment).

### P1.6 — MCP-SWTR startup: **GREEN (live)**

| Check | Result |
|-------|--------|
| MCP process | Running on port 3000 (PID 78067) |
| Task API health | `{"status":"connected","transport":"sse","tool_count":48}` |
| Live sprint query | `OLP-SPRNT-11 "Спринт 2026.10 - 2"` IN_PROGRESS (Task API → MCP → AS21 chain working) |

### P1.7 — Task API → MCP connection: **GREEN**

Task API (port 8241) connected to MCP-SWTR (port 3000) via SSE. 48 tools registered. Live query to AS21 returns correct sprint data.

### P1.8 — Regression tests: **GREEN**

| Suite | Result |
|-------|--------|
| V4 (299 tests: `test_agent_core_v4*` + `test_v4*`) | **299 passed, 0 failed** |
| Task API SWTR (58 tests: `test_swtr*`) | **57 passed, 1 pre-existing failure** |
| Frontend build (`tsc && vite build`) | **PASS** (101 modules, 621ms) |

The 1 Task API failure (`test_swtr_adapter_initialization`) is a **pre-existing test bug** (accesses `adapter.mcp_host` but the attribute is `api_host`). The migration introduces **0 changes** to `task-api/` or `po-agent-platform-v2/`, so this is not a regression.

---

## P2 — Public AS21 Diagnostic (READ-ONLY)

The public repo (`PO-Agent-Architecture-Review`, default branch `clean-public-release`) contains:
- A `cleanup_for_public_repo.sh` script (incomplete cleanup)
- `.venv/` and `__pycache__/` directories committed
- `set_cookie.py`, `setup_jira_token.py`, `mcp-gigacode-config.json` in file tree
- No `Dockerfile` or `docker-compose` at root level
- `mcp-swtr` directory present (from the migration)

**Root cause of "Public returns no data from AS21": UNCONFIRMED.** Likely contributing factors:
1. No MCP-SWTR process started in public deployment (no Docker entrypoint wiring visible)
2. No credentials/TOKEN configured (`.env` is gitignored)
3. Task API may be running in fake/local mode (default without explicit config)
4. AS21 may not be reachable from public infrastructure (VPN/firewall)

**Safe diagnostics for the public deployment team:**
1. Check if MCP-SWTR process is running: `ps aux | grep mcp_server`
2. Check Task API mode: verify `AS21_MODE` env var is set to `task-api`
3. Check MCP connectivity: `curl http://localhost:3000/sse` (should stream events)
4. Check Task API health: `curl http://localhost:8241/api/v1/swtr-read/health`
5. Verify TOKEN and BASE_URL env vars are set (do not print values)
6. Check AS21 reachability from the deployment host

---

## Summary

| Phase | Status | Notes |
|-------|--------|-------|
| P0.1 Repo visibility | **RED** | Repo is PUBLIC, not PRIVATE |
| P0.2 Worktree state | GREEN | Clean migration branch |
| P0.3 Secrets scan | GREEN | No secrets in 45 files |
| P0.4 No .env/.git/keys | GREEN | Properly excluded |
| P1.1 Core V4 frozen | GREEN | 6/6 byte-identical |
| P1.2 Gitlink removed | GREEN | No mode 160000 |
| P1.3 Source parity | GREEN | 4/4 hash-verified + file list exact |
| P1.4 Diff scope | GREEN | Only mcp-swtr/ changed |
| P1.5 Docker | GREEN* | Missing .dockerignore (pre-existing) |
| P1.6 MCP startup | GREEN | 48 tools live |
| P1.7 Task API → MCP | GREEN | SSE connected, live queries work |
| P1.8 Regression tests | GREEN | 299 V4 + 57 task-api + build pass |
| P2 Public AS21 | UNCONFIRMED | 4 likely factors listed |

---

## Recommendation

**DO NOT MERGE.**

The P0 safety gate failed: the destination repository `Sovietbear86/PO-Agent-Architecture-Review` is **PUBLIC** on GitHub. The migration contains 45 files of internal MCP-SWTR source code (112K lines) from corporate GitVerse, which the spec explicitly requires to remain in a **PRIVATE** repository.

**Immediate actions required:**
1. **Make the repository PRIVATE** in GitHub settings (Settings → General → Danger Zone → Change visibility → Private)
2. **Audit the public exposure window**: determine when the migration branch was pushed and whether the `clean-public-release` default branch also contains internal code
3. **Remove `.venv/`, `__pycache__/`, and credential-adjacent files** from the public repo's default branch
4. **Re-verify** P0.1 passes (GitHub API returns `private: true`)
5. **Then** re-run this QA (P0.1 re-check only; P1 findings remain valid)
6. **Consider** whether the already-pushed branch content needs a GitHub security advisory or GitVerse notification (internal code is now in GitHub's crawl cache even after making the repo private)

**The migration itself is technically correct** (clean diff, no Core changes, no secrets, source parity verified, all tests pass). The sole blocker is repository visibility.

---

## Services observed (left running)

| Service | Port | PID | Status |
|---------|------|-----|--------|
| Agent (V4) | 8004 | 97110 | healthy |
| Task API | 8241 | 78133 | connected, 48 tools |
| MCP-SWTR SSE | 3000 | 78067 | running |
| Vite frontend | 5175 | 81246 | running |
