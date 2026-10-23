# GigaCode — CURRENT NEXT ACTION

## A230R2.2-PUBLIC-DEPLOY-SKILLS-QA — independent deployment & health-check skills certification

**QA ONLY.** DO NOT edit application code, Core V4, scripts, tests, documentation, skills, CI, configuration or Git history. No auto-fix, merge, publish, force-push or credential printing. You may write only a sanitized QA report in the working Review repo on an isolated report branch. User-approved local installation in a **temporary separate Public clone** is allowed, but do not alter tracked files or existing production services on ports 8004/8241/3000.

### Target
- Community repo: `Sovietbear86/PO-Agent-Architecture-Public`.
- **Draft PR #3** `feat/gigacode-public-deploy-health-skills` -> `main`; first fetch **current exact HEAD**. Initial candidate `331b6023a80e170d3053e6652fe7681d0c78c91f`.
- Two canonical skills: `.gigacode/skills/public-deploy/SKILL.md` and `.gigacode/skills/public-health-check/SKILL.md`.
- Russian canonical `DEPLOYMENT.md`, `GIGACODE.md`, `scripts/public_health_check.py`, `scripts/tests/test_public_health_check.py`.
- PUBLIC publication permitted **if no secrets**; status `private=false` is NOT a failure.

### P0 — Public safety and docs
1. Run `python3 scripts/prepublish_scan.py` on the whole PR tree; independent secrets/PII scan on **all 9 changed files** and new skill text. Never print token values or actual task payloads.
2. Confirm no new `.env` tracked, no internal corporate hostnames or employee data added, no browser direct MCP read/write exposure. Track historical Review JWT rotation separately; do not copy token.
3. Check both SKILL.md YAML frontmatter `name`/`description`, distinct discoverability in GigaCode, slash or equivalent invocation path. Verify root `GIGACODE.md` routing is accurate.
4. Verify DEPLOYMENT accurately reflects PUBLIC sources: Python 3.13 for mcp-swtr, default stdio bundled directory/wrapper, env keys, ports 8003/8004/5175, `AS21_MODE=task-api`, products/team setup and Vite proxy. Check macOS/Linux/WSL2 boundary; never assume native Windows Bash support.
5. Security: no secrets pasted in logs; no source result dumped; all local services bind loopback; raw MCP has write tools and cannot be exposed directly; no tampering with Core files.

### P1 — Health CLI contract (offline and negative)
1. Run `python3 -m compileall -q scripts/public_health_check.py`; `python3 -m unittest discover -s scripts/tests -p 'test_public_health_check.py' -v`; `python3 scripts/public_health_check.py --help`. Record exact passed/failed counts.
2. Test without task code/LLM probe using controlled mock HTTP stubs: **INCOMPLETE, exit 2**, never GREEN; fake mode, no MCP, bad token, invalid/empty source, unrelated evidence must be RED/INCOMPLETE with clear first boundary. Never send credentials via URL; external non-loopback URLs must be rejected.
3. Check JSON/text do not expose tokens, task bodies, secret-containing errors, or raw LLM answer; the H6 evidence must have AS21 source provenance (`as21` or `REAL_AS21`) and V4 runtime.
4. Verify `community-ci.yml` health-tool job runs and completes; if not accessible, mark as NOT VERIFIED, do not claim GREEN.

### P2 — Fresh clean-clone deployment, not local working harness
1. Clone the *Public PR head* into an isolated temp directory. Execute the **public-deploy** skill as written, creating only ignored local venvs/.env and no tracked changes. Do not reuse local GitVerse checkout. Confirm Python 3.13, 48 MCP tools, Task API and Agent readiness and UI.
2. Run **public-health-check** skill on the clean clone, with a user-authorized EXISTING task code for H5 and bounded LLM H6. Source oracle must be independent REAL AS21; no fake/mock for live verdict. If no valid task or LLM credentials, record **INCOMPLETE**, not GREEN.
3. Validate first failing boundary for missing token, invalid AS21 URL/unavailable VPN, old MCP checkout, incorrect adapter mode or LLM 429; no automatic retries that hide source failure. Preserve existing ports and local services.
4. Run public V4 regression and relevant Task API/SWTR suite + frontend build; Core unchanged. Record counts; distinguish baseline failures.

### Verdict/report
Write **only sanitized** `po-agent-platform-v2/qa_reports/A230R2_2_PUBLIC_DEPLOY_SKILLS_QA.md` to a permitted isolated QA report branch or report in chat without a commit if the checkout is dirty. Include TESTED_HEAD, scan/CI results, discovery of both skills, per-stage H0–H6 results, actual source oracle, negative cases, regression counts, no tracked changes, and merge recommendation for PR #3. **No code fixes; STOP on real RED.** 
