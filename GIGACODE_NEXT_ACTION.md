# GigaCode — CURRENT NEXT ACTION

## A230R2.2-LOCATE-MCP — Read-only source-location audit

**STRICTLY READ-ONLY DISCOVERY.** No edits to application, tests, configs, Core V4, MCP-SWTR, service settings, git remotes or branches. No commits/push. GigaCode stays QA/forensics only.

### Goal
Locate the **actual source checkout** of the MCP-SWTR service used by current PO Agent Harness, and establish how the OWNER can safely access it for the additive worklog-filter tool. Do not implement anything.

1. Read running MCP-SWTR process command line / working directory / service launch scripts and determine exact **local path** containing `mcp_server.py` / AS21 timesheet integration, and whether `mcp-swtr/api-docs.json` is part of that source tree.
2. From that directory run read-only `git rev-parse --show-toplevel`, `git remote -v`, `git branch --show-current`, `git status --short`, `git rev-parse HEAD`; if not a Git repo, state explicitly. Redact usernames, tokens, secrets, internal server names and credentials in the summary.
3. Check whether relevant MCP server implementation is checked into `PO-Agent-Architecture-Review` (including submodules/subtrees/vendor or ignored/untracked paths), or is an entirely separate checkout/dependency. Report the smallest relevant paths/functions and the git remote **repository identity** only if safe to share.
4. Verify the audited raw endpoint `POST /rest/api/timesheet/v1/report` and existing MCP worklog tool implementation locations by source inspection only; DO NOT make new live source calls.
5. Return a concise report IN CHAT ONLY: MCP source path, repo name or 'not versioned', branch/HEAD, which files are owner-editable, whether tracked in an accessible remote, and recommended safe path for OWNER changes. Do not modify `GIGACODE_NEXT_ACTION.md` or generate speculative code.

### Stop
Once the location/access route is known, STOP. Only the OWNER (not GigaCode) implements A230R2.2 from `docs/assignments/A230R2_2_WORKLOG_IMPLEMENTATION_SPEC.md`. Frozen 6 Core files remain unchanged.
