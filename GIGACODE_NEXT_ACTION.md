# A230R3.47 — SberProject pagination QA ONLY

**ChatGPT owns implementation. GigaCode may not edit, patch, commit, deploy, or auto-fix source.**

Current state: live UI 69 OLP versions total / only 20 visible, CLI hardcodes offset=0 even though SberProject GraphQL productVersionListByPage supports offset. No live pagination GREEN claim.

ChatGPT has committed offline tracked-facade safeguards (source page identity and next_offset fail-closed) and contract tests. These are NOT the working local skill bridge.

Next owner step: review the local (untracked) exact .gigacode/skills/sbt-project/src/sbt-project.js + task-api/app/... sberproject bridge. Use only read-only source inventory in scripts/inspect_sberproject_pagination.py; no network, secrets or account credentials. Return sanitized function names, parameters and source line references. Do not implement the modifications as QA.

When ChatGPT later lands a bridge/CLI pagination patch, perform a SINGLE bounded QA:
- OLP page offsets 0,20,40,60 yield disjoint IDs with 20,20,20,9 rows, aggregate 69.
- Back from page 4 to page 3, forward from page 1 to page 2; disabled at ends.
- DMS 16 versions one page.
- Search/filter retains semantics; report if search is page-local (still a limitation).
- No tenant-wide scans; query only named product; TLS verify on; Core V4 unchanged.
- One focused build/regression and live browser verification, report PASS/RED and STOP.

No fake fallback to page-one results, no invented cursor, no fake task membership.
