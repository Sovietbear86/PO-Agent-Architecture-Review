# GigaCode — CURRENT NEXT ACTION

## A230R2.2-MCP-IMPORT + PUBLIC-AS21-DIAG — One-time authorized repository migration

**EXCEPTION TO QA-ONLY RULE:** The user explicitly authorized importing MCP-SWTR from corporate GitVerse into the private working GitHub repo and asked GigaCode to perform the mechanical migration because the owner agent cannot access the local checkout. This exception permits **only source import, provenance documentation, and migration-related smoke checks**. It does **NOT** permit GigaCode to implement/refactor worklogs, alter Core V4, change agent behavior, fix public AS21 integrations, or publish MCP source in Public.

### Required inputs
- Read `docs/assignments/A230R2_2_MCP_SWTR_SOURCE_IMPORT.md` in full.
- Known nested checkout: `PO_Agent_Harness/mcp-swtr`, separate GitVerse Git repo, `master`, clean at A230R2.2-LOCATE-MCP audit.
- Working private repo: `Sovietbear86/PO-Agent-Architecture-Review`, base branch `feat/core8-real-query-hardening-v2`.
- Public repo: `Sovietbear86/PO-Agent-Architecture-Public` (READ-ONLY diagnostic only).
- Six frozen Core files must remain byte-identical to checkpoint `6fb335d`.

### P0 — STOP-SAFETY-GATE
1. Confirm current **destination GitHub repo is PRIVATE** using authoritative GitHub metadata. If public/unknown: STOP without copying.
2. Confirm tracked worktree state in both checkouts, current branch, child SHA, gitlink mode 160000, and whether gitlink matches child HEAD; on mismatch or unexpected modifications STOP and report.
3. Inventory source tracked files using `git -C mcp-swtr ls-files`; archive tracked files only. Scan full contents (not just filenames) for tokens, secrets, credentials, private keys, personal data and restricted material. Explicit user IP permission is granted for PRIVATE destination only. Never add `.env`, `.git`, `.config`, token-bearing configs, private certificates, local caches, logs, or test dumps. If uncertain STOP.
4. Do not disclose sensitive values in logs or reports. No force push or git history rewrites.

### P1 — MECHANICAL IMPORT, ONLY IF P0 GREEN
1. Create a separate migration branch from the up-to-date working branch, e.g. `chore/vendor-mcp-swtr-a230r22`.
2. Create safe external backup of nested checkout and its `.git` state; do not destroy original checkout or running credentials.
3. Replace index gitlink with reviewed ordinary tracked MCP-SWTR source at `mcp-swtr/` using a tracked-only archive from exact source HEAD; keep paths (mcp_server.py, models/timesheet.py, api-docs.json, dependencies, tests and scripts) without source behavior changes. Preserve executable bits. Add a short provenance document with GitVerse repo name, original commit SHA and date (no credentials).
4. Validate staged manifest includes **no mode 160000** and **no secrets**; staged diff limited to MCP import + provenance. Hash-compare all migrated files with the source checkout.
5. Commit/push the migration branch to the PRIVATE GitHub repository and open a PR against `feat/core8-real-query-hardening-v2`; **DO NOT MERGE** and **DO NOT CHANGE PUBLIC**. Do not modify frozen Core V4 files or any other application functionality. If push/PR unavailable, report exactly what succeeded and stop without destructive retries.

### P2 — INDEPENDENT PUBLIC AS21 DIAGNOSTICS (READ-ONLY)
Colleagues report that Public deployment returns no data from AS21. This MAY relate to missing MCP checkout, but do not assume cause. Inspect PUBLIC repository deployment README, setup scripts, env examples, MCP-SWTR startup, Task API wiring, port mappings, health/config probes, feature flags, and how REAL_AS21 mode is enabled. Distinguish:
- missing gitlink source / GitVerse dependency and clone/submodule failure,
- absent credentials/session auth, expired token or VPN/AS21 reachability,
- MCP process not started or tool registry unavailable,
- Task API / MCP URLs or proxy misconfiguration,
- silently running in fake/local mode,
- AS21 read permission and pagination/source errors.
If colleagues' actual deployment logs are unavailable, mark root cause UNCONFIRMED and list exact safe, redacted diagnostics for them to run. Do not request or print tokens. No writes to Public.

### P3 — CHECKS + REPORT
- 6/6 frozen Core unchanged.
- Source files exact parity, no sensitive tracked material, private branch PR available.
- No test success claims without actual execution; perform safe source/import checks and non-mutating MCP/Task API health smoke if possible; no live mutation calls.
- Provide concise chat report: origin SHA, imported file count, destination branch, commit SHA, PR URL, safety checks, public-AS21 hypotheses supported by evidence and blockers, next owner action.
- Keep all previous A230R2.1 GREEN results unchanged. Do not mark A230R2.2 worklogs implemented or public deployment fixed.

### Short command
Perform authorized A230R2.2-MCP-IMPORT and read-only PUBLIC-AS21-DIAG exactly as specified. On any failed safety gate, STOP. No Core or feature changes, no merge, no Public source publication.
