# GigaCode — CURRENT NEXT ACTION

## A230R3.11-PUBLIC-STACKED-PR-RELEASE-READINESS-QA

**INDEPENDENT QA ONLY.** Do not change code, tests, configs, docs, Git history, PR state/base, tags, AS21 or running services. No merges/pushes/commits. Preserve any local dirty files. Record LOCAL_HEAD=REMOTE_HEAD=TESTED_HEAD where tested.

### Certified evidence
- Review A230R3.10 independent **GREEN**, TESTED_HEAD `4a75cb4`: 11/11 deterministic snapshot fail-closed/cache scenarios, browser+bounded REAL AS21 parity, V4 297 passed, Task API SWTR 52 passed, frontend build 0, Core V4 6/6. Previous LLM outage remains separate.
- Public A230R3.9-R2 independent `PUBLIC_RELEASE_GREEN`, TESTED_HEAD `f27fea7`: clean isolated clone, cold/warm H0–H6, real Chromium UI, bounded REAL AS21 A/B, 49 MCP, six-job GitHub CI all GREEN, Public Core six frozen files byte-identical to Public main.
- Public PR #3 `feat/gigacode-public-deploy-health-skills` → main is OPEN/DRAFT; PR #4 `feat/a230r3-community-migration` → PR #3 branch is OPEN/DRAFT. **Neither merged**. This assignment is NOT approval to merge.

### Gate A — precise PR and security release audit
1. Fetch current Public main, PR #3 and PR #4 HEAD/base and CI. Confirm previously QA-tested SHA remains current; on changes, require new independent QA. Check PR #3 alone retains deploy and health skills, no corporate credentials, PII, hardcoded internal hostnames or unsafe defaults.
2. Check PR #4 stacked delta preserves PR #3 features, sanitized MCP bundle and 49 tools, safe public placeholders and products configuration, four experimental flags default OFF, no internal Review Core/file history copied. Public Core 6/6 must exactly match Public main (sanitized docstring preserved).
3. Identify mergeability and potential conflicts: PR #3 → main FIRST, then retarget PR #4 to main and independently validate the resulting PR delta, CI and security **before separate owner merge approval**. Do not perform any retarget, merge, change draft state or other writes.
4. Security posture: principal-bound auth/session ownership still absent for remote multi-user service, so only documented local trusted single-user deployment may be considered release ready. Record security gate required for multi-user use. No tenant-wide AS21 scans.

### Gate B — delivery and portability audit
1. Confirm full official CI for PR #3 and #4 exact heads; if tests unavailable, mark NOT VERIFIED. Verify read-only source paths, 49 tool count for PR #4, V4+Task API+frontend build and prior isolated Public H0–H6/Browser/AS21 evidence matches heads.
2. Check GigaCode public-deploy and public-health-check Skills and deployed docs. macOS isolated E2E verified; Windows/PowerShell user journey and canonical empty-host ports remain NOT VERIFIED. Do not claim cross-platform certification without actual tests.
3. Review existing separated OPEN issues: Review planner reliability vs LLM 429, created-period plural-week grammar, QualityPage raw JSON, committed predictability baseline, release sbeproject discovery. Recent Review-only A230R3.10 snapshot patch must **not** silently appear in current Public release.
4. Specify safe rollback/release tags (proposal only), full audit matrix, and recommended go/no-go for each PR. Distinguish QA-approved functionality from actual unrestricted production/multiuser readiness.

### Required report
Exact SHA and CI/PR state, security scan evidence, risk matrix, sequential merge plan, rollback, `MERGE_READY_FOR_OWNER_REVIEW` / `HOLD` / `INCOMPLETE`. No modifications, no commits. STOP.

### Command
Run A230R3.11-PUBLIC-STACKED-PR-RELEASE-READINESS-QA from Review GIGACODE_NEXT_ACTION.md. Strict independent QA only; inspect current Public PR #3 and PR #4, verify exact release evidence and propose safe merge sequence. No edits or merges, report and STOP.
