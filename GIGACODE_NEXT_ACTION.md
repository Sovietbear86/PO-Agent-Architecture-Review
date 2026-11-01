# GigaCode — CURRENT NEXT ACTION

## A230R3.12-PUBLIC-MAIN-POSTMERGE-SMOKE-QA

**INDEPENDENT QA ONLY.** No code changes, commits, merges, pushes, deployment to network/multi-user hosts, AS21 writes, or termination of user's existing services. Keep Review frozen Core V4 (6/6). Use a fresh disposable clone of Public main and free isolated ports.

### Owners' merged release state (verify independently; do not assume)
- Public PR #3 merged into main, merge SHA `fb2e72166e80e981909696ae8c07a79d7d2eeea2`.
- Public PR #4 merged after it, merge SHA `36be0493f92c4348c55ba51e481a247b1372fb1e` (**expected Public main HEAD**).
- Prior independent PR #4 exact code-head QA `f27fea7` was PUBLIC_RELEASE_GREEN in authorized single-user isolated deployment: H0–H6 cold/warm, Chromium, bounded REAL AS21 A/B, 49 MCP, 6-job CI GREEN; current merge commit has NOT YET been postmerge certified.
- Review A230R3.10 snapshot patch passed independent GREEN but is **Review-only**; it was NOT intentionally included in this Public release.
- Multi-user session authentication and principal-bound ownership remain OPEN security gates; do not infer production authorization from merge.

### Gate 0 — source and provenance
1. Independently `git fetch origin`, verify Public main HEAD equals `36be0493...` and includes both PR #3 and #4 merge ancestry; compare main tree to QA-certified PR #4 code tree. Report any unexpected postmerge file changes and STOP if found.
2. Run `python3 scripts/prepublish_scan.py`, confirm no secrets, corporate hosts or personal identities in proposed public tree. Compare Public six frozen Core V4 files against previously verified Public main baseline blobs; no drift.
3. Verify CI on the exact **merge commit** (not only PR4 HEAD). Check six expected jobs; if not triggered/available report `POSTMERGE_CI_NOT_VERIFIED`, run local suites without inventing CI success.

### Gate 1 — clean-clone functional smoke
1. Install declared Agent, Task API, MCP (Python 3.13) and frontend Node requirements. Run available offline V4 focused/full, Task API, health CLI and frontend build. Report exact counts. Verify MCP list_tools count 49 and all read-only source facades.
2. Use Public's `public-deploy` and `public-health-check` skills from actual main clone in isolated local single-user environment, no internal GitVerse or Review dependency. Use available scoped secrets securely, never print/store in repo.
3. H0–H6 on cold and warm standalone Public, REAL AS21 bounded independent A/B, browser UI (task row, period worklog, ranked candidates), safe empty/error output and no raw planner JSON; verify proxy stays on isolated Public Agent, not Review.
4. If REAL AS21/LLM/browser unavailable, label the specific gate NOT VERIFIED rather than all-GREEN. Do not run unscoped queries or write to AS21.

### Gate 2 — Windows/macOS readiness discovery (P2)
1. Audit install Skill + health Skill + DEPLOYMENT.md against Windows 11 PowerShell 7 and macOS zsh (Apple Silicon / Intel) workflows. Record exact unsupported command, path separator, subprocess, env/export, venv, Python 3.13 stdio or port handling. No actual Windows GREEN until independently run on Windows.
2. Propose concise separate README sections / QUICKSTART_WINDOWS.md and QUICKSTART_MACOS.md covering prerequisites, install, local config, health H0–H6, browser test, rollback, troubleshooting and warnings for single-user only. **Draft recommendations only** for owner; no code/doc changes.
3. Identify especially if health H3 cold stdio 15s budget has risk on slow Windows and whether platform-specific timeout controls need redesign; do not simply increase until measured.

### Report
Exact Public main TESTED_HEAD, CI, scan, 6/6 Core, 49 tools, H0–H6, A/B, browser, deploy skill, macOS vs Windows status, first failed boundary, Windows/macOS instruction change plan. Verdict `POSTMERGE_GREEN` / `INCOMPLETE` / `RED`. QA-only, report then STOP.
