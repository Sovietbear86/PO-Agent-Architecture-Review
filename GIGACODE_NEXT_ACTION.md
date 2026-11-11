# A230R3.46 — QA only: Releases toolbar one-row verification

ChatGPT owns ALL source development and fixes. GigaCode must not edit source, scripts, configuration, commit, deploy, or troubleshoot by changing code.

After user runs `scripts/update_releases_dashboard_toolbar.sh`, perform exactly ONE bounded browser review:
- Desktop 1200px+: **one row** with Product, Status, narrow dark version Search, source timestamp, and Refresh at the far right; timestamp directly LEFT of Refresh; no Refresh line break.
- At narrow viewport ensure no overlap or clipped controls; horizontal scrolling is tolerable only when actual available width is below the controls' minimum.
- Compare Refresh button with Sprint and Overview buttons, and version-search background with Tasks tab; no white input.
- OLP 69 total / 20 currently loaded, DMS 16 total; no red React exceptions.
- Strict front-end build PASS as prerequisite (owner script runs it). Core V4 unchanged. One concise PASS/RED report; STOP.

**Pagination: development task, NOT QA**. Live SberProject source GraphQL `productVersionListByPage` supports OFFSET, but skill CLI hardcodes offset=0 while exposing --max-results. The browser cannot get page 2 until owner changes the CLI and server bridge to carry verified offsets and next_offset. DO NOT invent cursors, turn on fake Next, or declare this issue GREEN. Next owner step is source code of `.gigacode/skills/sbt-project/src/sbt-project.js` command definition plus local `task-api/app/services/sberproject/` integration. QA must not modify.
