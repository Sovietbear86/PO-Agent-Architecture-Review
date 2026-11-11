# GigaCode — NEXT ACTION / QA ONLY

## A230R3.43 — Releases widget/theme/navigation independent QA

**Do not develop, edit source, fix issues or commit**. ChatGPT alone owns source. Wait until owner executes the source-only widget update from `scripts/update_releases_dashboard_widgets.sh`; do not run it on GigaCode's behalf.

### Code under test
ChatGPT owner Review commits `c495181`, `61f2cb3`: change `frontend/src/recovery/ReleasesDashboard.tsx` ONLY. Existing live source currently runs SberProject OLP 69 total / DMS 16 total through validated CLI bridge. This patch does not change API, authentication, trusted CA, Core V4, or other pages.

### Scope: one concise, bounded QA pass
1. Browser screenshot color/theme parity against Sprint/Overview/Quality. Shared `metric-card`, `panel`, `insight-grid`, `metric-grid`; compare backgrounds, borders, text, accent, spacing and responsiveness, avoiding hardcoded release-only cyan.
2. OLP and DMS `Ближайшие выпуски и контрольные даты` read real releaseDate when supplied; if not, use endDate **only** as explicitly labeled planned-completion milestone; never misrepresent as actual releaseDate. Filter out terminal statuses, past dates, invalid dates, and check ordering. Confirm DMS empty result is honest if no future source dates, not a UI defect.
3. Pagination: inspect actual HTTP JSON `has_more`, `next_offset`, `total` on both products. `Далее` is enabled ONLY when has_more AND valid next_offset; if has_more with null offset, stays disabled with visible explanation (no fabricated page 2). Report this as **SOURCE_PAGINATION_BLOCKED**, not a frontend failure. Verify Back and stale status where applicable.
4. One targeted tsc+vite build; verify source and Core V4 unaffected by test, no secret logging. One QA report with PASS/FAIL and source examples, STOP.

**Important:** Need true end-to-end pagination for all 69 OLP versions later; this requires adding verified offset support in the CLI/backend, which is a **ChatGPT owner task**, not a QA fix.
