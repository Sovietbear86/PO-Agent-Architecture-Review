# GigaCode — NEXT ACTION (QA ONLY)

## A230R3.42-QA — Releases Dashboard, independent verification after owner implementation

ChatGPT OWNER CODE WRITTEN on Review branch (remote): `00373ff` (new `ReleasesDashboard.tsx`), `79ad7ab` (`Pages.tsx` swap), `c467643` (typed CSSProperties). **Do not presume these commits are present in the user's LOCAL branch**: user has unpublished live SberProject/TLS bridge commits. Source changes are remote-only at this moment and must be integrated by ChatGPT/owner-controlled safe Git synchronization before any runtime QA. GigaCode must not cherry-pick, merge, rebase, edit, commit or fix anything independently.

QA trigger: local app source has BOTH the real live bridge and the above dashboard commits, and ChatGPT explicitly supplies integrated HEAD. Until then: HOLD.

### Mandatory ownership boundaries (PO decision 2026-11-10)
- **ChatGPT is the sole author/developer**: architecture, code, features, fixes, commits, documentation, UI/UX and release integration. GigaCode is **independent QA/tester only**.
- GigaCode must NOT implement features, modify source, fix defects, change production configuration, or commit/push code. It may create a QA report only, clearly separated and untracked unless ChatGPT explicitly asks otherwise.
- Do not launch QA until ChatGPT provides a precise **integrated local** commit/HEAD and test scope. Existing owner task A230R3.42 is NOT a GigaCode implementation assignment.

### Verified domain fact supplied by PO
Tasks included in SberProject releases **are synchronized with AS21/SWTR**. Treat this as a domain invariant: release management uses SberProject as release/version authority and AS21/SWTR as task/status/hierarchy/owner/quality authority.
**Important**: the previously tested API did not expose a reliable release↔task join key (the listing returns no issueKey/percentDone); this is a **technical mapping gap**, NOT a claim that synchronization does not exist. ChatGPT will implement a source-grounded join after locating/validating the actual linkage, with no invented task membership, percentages or zero counts.

### Next QA run (ONLY after owner signals READY_FOR_QA)
1. Verify the supplied owner commit matches the working tree; frozen Core V4 6/6 byte-identical.
2. Browser inspect Releases OLP/DMS: responsive full-width layout, product/version/status filter, real source counts with pagination-completeness caveat, lifecycle statuses, dates and selected release details; compare to source-backed records.
3. Confirm no fake tasks/progress/blockers/forecast, no hidden data leakage/tenant scans; explicit 'linkage pending' only if the join has not yet been implemented.
4. Check loading, source auth/TLS unavailable, partial pagination, stale refresh, small viewport and no regressions in Sprint/Quality/Overview navigation.
5. One targeted test run + frontend build; one bounded report at `po-agent-platform-v2/qa_reports/P32_RELEASES_DASHBOARD_UI_QA.md`. If RED, report exact reproduction and failing boundary **without fixing it**. STOP.

### Owner engineering scope (for reference only; NOT a GigaCode assignment)
ChatGPT implements a Sprint-like Releases dashboard: KPI cards, portfolio status distribution, chronological version table, selected version details. MVP uses verified SberProject version metadata. Follow-on links synchronized SberProject release tasks to AS21/SWTR via verified join and adds scope/completed/WIP/blocked/forecast. Local HEAD includes live SberProject/TLS bridge commits not yet pushed to GitHub owing to broken git credentials, so owner must first get an exact up-to-date repository snapshot before safe code editing. Never overwrite local source by pulling stale remote.

**GigaCode current action: HOLD until explicit QA handoff from ChatGPT.**
