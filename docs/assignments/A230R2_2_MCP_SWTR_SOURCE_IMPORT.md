# A230R2.2 — Consolidate MCP-SWTR source into PO Agent working repository

## Decision
Import a **reviewed tracked source snapshot** from the clean local GitVerse checkout at `mcp-swtr/` into the **private working** GitHub repository. Replace the current 160000 gitlink with ordinary tracked files. This removes GitVerse as a build-time dependency for this working checkout. Do **NOT** publish the internal MCP code into `PO-Agent-Architecture-Public` automatically.

## Verified facts (A230R2.2-LOCATE-MCP)
- Checkout: `PO_Agent_Harness/mcp-swtr` — separate GitVerse repository, branch `master`, clean.
- Main repository points at it as a gitlink (mode 160000), not a registered submodule.
- Relevant files: `mcp_server.py`, `models/timesheet.py`, `api-docs.json`. `.env` is untracked and contains local credentials: **never copy or stage**.
- MCP service runs from the checkout and must be restarted/tested after import.
- Need to record source SHA and provenance before import.

## Safety gate (mandatory, before any mutation)
1. Confirm license/IP authorization to mirror the source from corporate GitVerse into this GitHub private repository. If unclear, STOP.
2. No dirty worktree in either main or nested repo, except explicitly understood local ignored files. Confirm no local-only patches.
3. Ensure main repo branch `feat/core8-real-query-hardening-v2`. Record parent HEAD, child SHA; verify gitlink matches child SHA or document and resolve discrepancy first.
4. Inventory `git -C mcp-swtr ls-files`; scrutinize tracked files for secrets, internal credentials, private keys, tokens and sensitive company material — filenames alone are insufficient. Abort on unresolved findings.
5. Require the new source to be **private**. The public mirror must retain a sanitized/redacted interface instead of entire MCP source.

## Safe recommended procedure (owner local terminal; not GigaCode)
From the parent repo root, AFTER safety gate and with explicit approval:
```bash
set -euo pipefail
test "$(git branch --show-current)" = "feat/core8-real-query-hardening-v2"
test -z "$(git status --porcelain)"
test -z "$(git -C mcp-swtr status --porcelain)"
git ls-files --stage -- mcp-swtr
git -C mcp-swtr rev-parse HEAD
git -C mcp-swtr ls-files
```
Create an archive of **tracked files only** (never use `cp -R`, which could copy `.env`, `.git`, or secrets). Use a temporary directory OUTSIDE the repo and keep a separate backup of the original child checkout. Verify archive manifest/content before replacement.

Then, in a dedicated migration branch from the working branch:
- Remove the gitlink from the **index only**: `git rm --cached mcp-swtr`.
- Replace the nested checkout with the reviewed tracked-only archive; do not delete its original `.git`/untracked local configuration before backing up.
- Stage source files deliberately using `git add`, verify `git diff --cached --name-status` and `git diff --cached --check`. Confirm no `.env`, `.git`, `*.pem`, `*.key`, tokens, credentials or generated bulk artifacts in the staged tree.
- Ensure staged `mcp-swtr` paths are ordinary blobs (100644/100755) and there is **no 160000 gitlink**.
- Preserve provenance `source remote (redacted), branch, commit SHA, import date` in a nonsecret file. Never embed credentials or internal remote URLs with tokens.
- Commit once and open a PR back into the private working branch. Do not push to Public.
- Reconfigure/restart local MCP service only after reviewing changed paths; verify `mcp_server.py` and `api-docs.json` are present.

## Post-import gates
- Compare imported tracked-file hashes to the source GitVerse HEAD (bit-for-bit).
- 6/6 frozen Agent Core V4 files unchanged vs checkpoint `6fb335d`.
- No secrets: staged file scan + historical credential patterns.
- MCP-SWTR local start and all 48 existing read tools health-tested; Task API 8241, agent 8004, UI still work.
- No user-facing behavioral change at import stage. New filtered worklog route added only in subsequent A230R2.2 implementation PRs.
- Run full V4 / Task API SWTR regression and frontend build; independent GigaCode QA **after** owner migration.
- Preserve separate downstream GitVerse update strategy, or explicitly record that PO Agent now owns the vendored copy.

## Stop rules
If authorization, tracked credentials, dirty checkout, SHA mismatch, or startup compatibility fails: STOP without importing/publishing.
