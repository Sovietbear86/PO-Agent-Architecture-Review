# GigaCode — NEXT ACTION (QA-ONLY)

## A230R3.44 — Releases layout review, ONE bounded smoke

ChatGPT is the SOLE developer. GigaCode is QA-only: **do not edit code, change config, fix issues, cherry-pick/merge, stage or commit**. Only run this check AFTER ChatGPT owner layout + verified-link owner patch `a07e47a` is deployed to live frontend via `scripts/update_releases_dashboard_layout.sh` and owner authorizes QA.

Test:
1. On desktop, controls Product / Search / Status / Refresh have breathing room. Search input appears to the **right** of 'Поиск версии', not below. Verify responsive wrap at narrow viewport without overlap.
2. Three panels under KPI: status distribution; milestones; **release detail** occupying the previously empty right-hand slot (responsive grid). Selecting a version from table or milestone updates details in-place (not below catalog). Closing shows instructional empty state.
3. Card contains factual fields and a keyboard-focusable, max-height scroll-ready 'Задачи релиза' region. **No live task list is claimed yet**: the release→task join is still missing from the VERIFIED server contract, despite synchronized underlying SberProject↔AS21 task data. Verify explicit source-unavailable explanation, not fake zero entries or unrelated `/releases/{id}/tasks` (local CRUD).
4. Selected version: direct SberProject link appears only when source supplies verified HTTPS project.sbertech.ru deep-link (webUrl/url). When absent, explicit explanatory fallback; no guessed URL, no unsafe hostname or javascript: scheme.
5. Pagination: first page Back naturally disabled; Next must not falsely navigate without source cursor. Record missing API cursor as SOURCE_PAGINATION_BLOCKED, a real remaining functional gap. Full OLP 69 must not be claimed loaded.
6. Visual theme matches Sprint/Overview shared panels and metric cards. No horizontal overflow at common widths.
7. One focused `tsc && vite build` + browser smoke both OLAP and DataMarts, brief evidence PASS/RED, existing Core V4 hash unchanged. STOP.

Separate ChatGPT owner stage (NOT GigaCode): verify exact release membership linkage in SberProject and AS21/SWTR with bounded read-only one-release A/B, then implement API and real scrollable task list; never infer membership from release name/space or treat empty response as 0 without provenance.
