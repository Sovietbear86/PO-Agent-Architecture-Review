# GigaCode — CURRENT NEXT ACTION

## A230R1 — UI Real-Query Failures: independent source-oracle diagnostics (RED until fixed)

**Role: independent QA / browser and API forensics / AS21 oracle only. Do not modify production code, tests, Core, planner, runtime or configuration. If RED, capture first failing boundary and stop.** Agent Core V4's six frozen files must remain byte-identical to checkpoint `6fb335d`. Do not alter previous A229M2.2B1 GREEN verdict; new cases are additional regressions.

### Reproduce exactly — new isolated chat sessions, local loopback, REAL AS21
1. `покажи открытые задачи Калачанова за последнюю неделю` — natural rolling seven-day period is not inherently ambiguous. Capture parsed field (created/updated?), exact dates, user/space/status filters and AST. Never silently impose `created_at` for an unspecified date dimension. Either resolve defined product default transparently or request the **specific date-field** clarification, never pretend the duration itself is ambiguous. Distinguish `за последнюю неделю` from `за прошлую календарную неделю`; resolve against test execution's server-local date, including midnight/DST boundaries. Expected: no spurious "неоднозначно понять период".
2. `с 30.09.2026` following that clarification — continuation must preserve original executor, open status and intended date field; `с` means inclusive lower bound to current date, not a new unrelated query, and no fabricated creation-specific filter unless explicitly chosen. Capture state, tool calls, AS21 A/B results. Do not state a count as VERIFIED unless source-backed.
3. `покажи списания Гаранина с 01.10.2026 по сегодня` — on screenshot request returned `FAILED` after 175936 ms with generic trajectory error, no evidence. Independently establish whether worklogs/time entries capability actually exists; if unsupported return typed UNSUPPORTED/clarification, not hang or fake results. If supported, require scope/person ID/time range and REAL AS21 source-backed response; capture LLM/tool/provider timeout/429/502, first failing boundary, retry behavior, wall time.
4. `ты тут?` — screenshot ping completed after 81876 ms and rendered raw JSON in `skill_catalog` meta widget (`agent.help`, `source: AGENT_RUNTIME`). A ping must be local/fast (define a measured budget from implementation baseline), produce short friendly answer, not dump operation JSON; meta cannot be mislabelled REAL AS21 or shown as task evidence. Measure network vs LLM latency, cold/warm behavior, request trace and raw UI payload.
5. Verify widget `skill_catalog kind: meta` UI normalizes meta responses and never prints internal `step/capability_id/arguments/data` JSON as user content. Check user-facing `Evidence 0 · trace` and generic `Не удалось получить корректный результат` on failure; actionable safe typed error text must replace misleading success or opaque outcome, without leaking secrets.

### Mandatory QA artifact / verdict
- Reproduce ≥3 attempts per case if feasible; record exact TESTED_HEAD, flag matrix (OFF default and local permitted ON), screenshots, request IDs, HTTP/response statuses, elapsed timings, first failing boundary, real AS21 oracle, classified root cause and **proposed smallest fix location outside frozen Core** (API orchestration, period parser/skill contract, source adapter, UI meta presentation).
- No production changes by GigaCode. Mark each case RED or GREEN independently. Do not claim green on missing evidence.
- After OWNER applies isolated fixes, rerun full V4 tests, all Task API / SWTR regression, frontend build, browser smoke (Overview/KPI/task drawer), both existing A229M2.2B1 REAL AS21 goals and new four scenarios. Re-record fresh tested HEAD; ZERO FAILED; Core hashes unchanged; no mutations, no unscoped reads, no fake mode; feature flags OFF by default.
- Security blocker remains: session ownership/auth binding still required for remote/multi-user rollout.

### Short instruction
Run A230R1 independently from this file. QA/forensics only, no code changes. Report first failing boundary with trace and AS21 oracle; stop on RED.
