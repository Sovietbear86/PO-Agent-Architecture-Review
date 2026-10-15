# A229M2.2AR2 — Cross-turn Goal Coverage Re-gate

GigaCode role: independent QA only. Do not change application, tests, configurations or Agent Core. Stop on first RED.

Previous A229M2.2AR RED: on a continuation, trusted previous lookup is restored to the planner but excluded from current `data.results`. Therefore the goal guard wrongly declares the lookup unproven after hierarchy completes.

Owner fix: API now passes server-stored `continuation.observations` into the goal coverage verifier as private credit-only evidence. Previous facts are checked for REAL_AS21 provenance, compact allowed fields and size/quantity bounds, and combined with current terminal results ONLY in an internal coverage view. Public `data.results` remains current-turn only. Added three two-turn regression tests. Feature flags stay OFF by default.

P0: Pull current HEAD. Verify Core 6/6 hashes identical to frozen checkpoint, no planner/registry modifications. Run goal coverage/browser API/synthesis tests, full V4 blast, Task API suites and frontend build. Zero failures required.

P1 first boundary: 3 valid REAL AS21 M2 trials with flags ON in isolated QA stack. T1 DMS-267 lookup is proven and saved, T2 executes ONLY hierarchy, parent oracle DMS-253. Guard must credit both goals and return COMPLETED. No duplicate lookup reads, no unsupported claim or source-card leak. Ensure public results only show this-turn source operations. Critically verify final user-facing answer addresses BOTH requested goals, not only hierarchy; if coverage passes but prose omits lookup, RED and STOP.

P2: Repeat M1 (two people), M4 (three goals), C5 (links) with independent source facts. Unproven goal remains NEEDS_CLARIFICATION. Invalid/expired/stale/untrusted previous evidence cannot count. Verify source/429 taxonomy, one-shot clarification, session TTL, bounds and flag-OFF parity. Authentication/session ownership remains an unresolved deployment blocker.

P3: Report verdict AGENT_CORE_V4_GOAL_STATE_PRESERVATION_GREEN_A229M22AR2 or AGENT_CORE_V4_GOAL_STATE_PRESERVATION_RED_A229M22AR2, exact first failing boundary, TESTED_HEAD, Core hashes, counts and observations. Commit QA report only: `po-agent-platform-v2/qa_reports/AGENT_CORE_V4_GOAL_STATE_PRESERVATION_REGATE_A229M22AR2.md`. Do not enable flags or create checkpoint.
