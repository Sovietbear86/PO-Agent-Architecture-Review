# GigaCode — QA ONLY / A230R3.45

ChatGPT is the only developer. Never edit source, deploy, adjust config, commit, or perform open-ended test loops.

## Trigger
After user runs ChatGPT's `scripts/update_releases_dashboard_toolbar.sh` and confirms patch applied, perform one bounded UI verification.

1. Compare search field `.filter-input-row.free-search-row input` styling with **Tasks** text search (same background, borders, spacing, placeholder). No separate highlighted background.
2. Verify release Refresh uses `.entity-toolbar` button styling and is right-aligned like Sprint with the timestamp nearby. Test narrow viewport wrap.
3. Verify OLP 69 total/20 loaded and DMS 16/16 source facts unchanged. Check filter works on currently loaded rows. Do not mark pagination PASS: Next is nonfunctional due to missing source cursor.
4. Verify browser remains 200, no console errors. Only one focused tsc+vite build; report any genuine failure, do NOT fix.
5. Check Core V4 unchanged, user services unaffected. Single concise QA report and STOP.

## Critical open problem / not solved by toolbar patch
Real pagination requires ChatGPT source-side fix for `.gigacode/skills/sbt-project` (or live CLI) and `task-api/app/services/sberproject/sberproject_read.py` + typed API response. `has_more=true` without `next_offset` must NOT be treated as working. Also no tenant-wide scans, no fabricated page numbers or version lists. Users demand access to all 69 OLP versions.

To support ChatGPT without changing code, QA may provide bounded **read-only excerpts** from local live files about version CLI pagination (arguments, GraphQL paging, `_ALLOWED_FIELDS`, `next_offset`, `total`). NEVER print access tokens, credentials, environment secrets or actual private task payloads. Provide only source paths/signatures/line numbers.

**STOP after report.**
