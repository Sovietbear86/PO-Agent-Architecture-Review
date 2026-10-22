# A230R2 — Owner fix specification after A230R1 RED

Status: OPEN / not implemented. This is an OWNER implementation plan. GigaCode remains QA-only and must not fix production code.

## Verified QA findings (reported A230R1)
- TESTED_HEAD 8bb68b2; 4/5 RED; QA report commit 4b94635 (verify in local clone). Frozen six Core files 6/6 byte-identical to 6fb335d; flags OFF.
- C1: `покажи открытые задачи Калачанова за последнюю неделю` produces parser ValueError when task live handler tries created-period parse without week unit support; also invents created_at dimension.
- C2: `с 30.09.2026` continuation mechanic and oracle correct (five open rolling 7d; 11 open since Sep 30), but created-period dimension improperly inherited from C1.
- C3: `покажи списания Гаранина с 01.10.2026 по сегодня` unsupported by existing person+date worklog skill (per-task only; member skills require space/sprint). No fake task search fallback.
- C4: `ты тут?` uses heavy LLM planner/synthesis with ~77–86s observed, despite in-process ping handler ~0.001 ms.
- C5: v4ResultPanel JSON.stringify renders raw `step/capability_id/arguments` JSON, mislabels ping as skill_catalog meta.

## Guardrails
- ZERO byte changes to six frozen Core files from checkpoint 6fb335d: agent_core_v4.py, agent_core_v4_robust.py, agent_core_v4_reliable.py, agent_core_v4_completion.py, v4_plugin_registry.py, llm/real.py.
- Small scoped changes only in external period parsing/skills, source adapters or API pre-routing, frontend presentation and tests. No hidden direct MCP bypass. Flag OFF baseline parity; no unauthorized local facts or invented counts; no auth/session rollout.
- Make one small fix at a time, add failing reproducer first, run focused tests then mandatory full suite at each implementation head, do not reuse old GREEN.

## Fix 1: relative periods and no invented temporal dimension
- Extend bounded relative-period parser outside frozen Core to recognize `за последнюю неделю` (rolling 7 calendar days) and `за прошлую неделю` (previous calendar week), plus day/month forms where contract supports; timezone-local deterministic now injection for tests.
- Expose normalized from/to with clear inclusive bounds and compare from source date fields explicitly.
- If question lacks date dimension (created / updated / due / activity), ask specific clarification about dimension ONLY or apply an explicit documented product default announced in response. Never assert implicit `created_at` because parser matched date words.
- Reproduce exact C1; ValueError must become typed, actionable error rather than generic failure; preserve executor/status and scopes.
- Fix subsequent C2 state to avoid carrying a guessed dimension; date lower bound Sep 30 inclusive.

## Fix 2: worklogs by person + range
- Check real AS21/SWTR capability and data scope for cross-task worklogs by person and date. Create governed/read-only typed capability and proper source-backed aggregation only if API genuinely supports it.
- Otherwise return immediate precise `UNSUPPORTED_CAPABILITY` including missing requirements, not a task-search clarification, synthetic fallback, or 175-second FAILED.
- No broad space scan to imitate worklogs; permission and pagination bounds required.

## Fix 3: cheap local ping routing
- Add a narrow allowlist for isolated ping/help intents at API ingress (not frozen Core) to reach existing governed runtime meta capability without LLM planner/synthesis, honoring authenticated session and existing runtime policy.
- Reject overlapping/multi-intent requests from fast path. Keep source provenance `AGENT_RUNTIME`, not REAL_AS21; do not expose raw operations.
- Establish measured local p50/p90 budget in realistic UI E2E (goal <2s warm local, not assertion of SLA); test no change to normal search behavior.

## Fix 4: frontend meta renderer and errors
- Render agent.help / ping as concise natural-language text; do not JSON.stringify internal envelope into user content. Hide technical trace in collapsed diagnostics only and render meta not as source evidence.
- Typed user-safe error messages distinguish `UNSUPPORTED_CAPABILITY`, `NEEDS_CLARIFICATION`, `SOURCE_UNAVAILABLE`, `PROVIDER_TIMEOUT`, and `PARTIAL`; no internal secrets.
- Frontend tests assert no `step/capability_id/arguments` strings, no pseudo evidence, correct kind/meta distinction.

## Acceptance / QA gate (A230R3)
- 3+ distinct attempts per C1–C5 and regression case C2 with AS21 A/B oracle; exact TESTED_HEAD and diagnostics.
- Core hashes 6/6; flags OFF; complete V4 and Task API/SWTR suites and frontend build GREEN.
- Verify A229M2.2B1 3-goal REAL AS21 and prior complex search/hierarchy/period/Overview/task drawer. Ping latency measured p50/p90; no raw JSON UI leakage.
- Ensure no local file mutations / unscoped reads; security session ownership remains OPEN for remote use.
- Only after independent A230R3 GREEN consider public sync; do not ship RED.
