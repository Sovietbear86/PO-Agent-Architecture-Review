# A230R2.1-QA — Independent regression of week period changes

**Verdict: AGENT_CORE_V4_A230R2_1_WEEK_PERIOD_GREEN (partial gate R2.1 only; C3–C5 explicitly NOT considered fixed)**

## Identity

| Field | Value |
|-------|-------|
| TESTED_HEAD | `6708883cd700afdf3f9cc70f1a80b6b02796adf7` |
| REPORT_COMMIT | _(this commit)_ |
| Date | 2026-10-22 (server-local MSK ~21:55–23:58) |
| Branch | `feat/core8-real-query-hardening-v2` |
| Owner commits under test | `8090bb6` (week parser, `_task_live_handlers.py`), `34ef574` (period-intent guard, `api/v1/__init__.py`), `d9dd200` (regression test `test_a230r2_week_periods.py`) |
| Services | agent 8004 (PID 97110 @6708883, V4 enabled, goal flags ALL OFF — fresh restart on TESTED_HEAD; stale A230R1-era process PID 75119 @8bb68b2 killed first), task-api 8241 (PID 78133, MCP SSE connected 48 tools), MCP 3000 (PID 78067), vite [::1]:5175 (PID 81246, proxy → localhost:8004) |
| Scope | STRICTLY TEST ONLY — no production/test/config changes; only this report written |

## P0 — Frozen Core, worktree, flags — GREEN

Core 6/6 **byte-identical** to checkpoint `6fb335d` (git blob hashes, worktree vs ref, re-verified at final HEAD):

| File | Hash |
|------|------|
| agent_core_v4.py | 52100ca1 |
| agent_core_v4_robust.py | 3bdb4d09 |
| agent_core_v4_reliable.py | 1f7562dc |
| agent_core_v4_completion.py | cf75a6d6 |
| v4_plugin_registry.py | d82929d1 |
| llm/real.py | 1cc10e12 |

- Worktree: only `GIGACODE.md` modified (pre-existing local edit) + untracked `.gigacode/skills/` (environmental); **zero tracked production changes** since `6fb335d` beyond the 3 owner commits (`8090bb6`, `34ef574`, `d9dd200`) — proven by `git diff 6fb335d..6708883 --stat` (2 prod files + 1 test file within the R2.1 commits; the remaining range diff = already-certified A229M2.2B1/A230R1 history).
- Goal feature flags: all OFF (defaults, `ps eww` + no guard/executor/continuation markers in any response).
- Owner delta is exactly: `_task_live_handlers.py` +27 (rolling_week + previous_week fullmatch blocks, outside frozen Core), `__init__.py` _TASK_PERIOD_INTENT_RE +2 week patterns, `test_a230r2_week_periods.py` new.

## P1 — Focused suites — GREEN (82/82)

`test_a230r2_week_periods.py` (8 new cases: 4 rolling-week parametrized phrases, 3 previous-week, malformed rejection) + `test_agent_core_v4_task_created_period.py` + `test_v4_browser_api_contract.py` + `test_v4_goal_coverage.py` + `test_v4_missing_goal_execution.py` + `test_clarification_engine.py` + `test_clarification_loop.py`:

**82 passed in 0.89s, 0 failed, 0 errors.** No tracebacks.

## P2 — Deterministic rolling/previous week — GREEN (probe `qa230r21/p2_boundaries.py`)

Fixed-clock, timezone-locked probes (Europe/Moscow), all on the production parser `_parse_human_created_period`:

- **Rolling week = 7 calendar dates (today + 6 preceding)** — verified for `за последнюю неделю`, `последнюю неделю`, `last week`, `past week` @Thu 22.10.2026: 16.10 00:00 MSK → now, kind `last_7_calendar_days`, exactly 7 distinct dates.
- **`за прошлую неделю` = previous Monday–Sunday, ISO convention** — anchors: Thu 22.10 → 12.10(M)–18.10(S); Mon 26.10 (ISO week 44) → 19.10(M)–25.10(S); Sun 18.10 (ISO week 42) → 05.10(M)–11.10(S). **All three match `date.isocalendar()` exactly.** (Two of my initial probe expectations used the Sunday-starts-the-week convention and were corrected — the parser is ISO-consistent, including "on Sunday, the current week already started on Monday".)
- **Month boundary**: Sat 03.01.2026 rolling → 28.12–03.01 (7 dates); previous-week → Mon 22.12–Sun 28.12 (ISO week 1 of 2026, correct). **Year boundary**: Thu 01.01.2026 rolling → 26.12.2025–01.01.2026 (7 dates).
- **`последние 7 дней` ≡ rolling week** (identical start/end/kind) — documented semantic overlap, no conflict.
- **Explicit `с 30.09.2026` inclusivity retained**: `explicit_start_to_now`, 30.09 00:00 MSK → now; `с 30.09.2026 по сегодня` identical. Two-date range retained (30.09→01.10 inclusive, end 23:59:59.999999).
- **Malformed/unsupported rejected (typed ValueError, no invented semantics)**: `за несуществующую неделю`, `за 2 недели`, `за 1 неделю`, `за две недели`, `за последний месяц`, `last month`, `в этом году`, `неделю`, `на прошлой неделе`, lone date without start marker — all raise.
- **No accidental regex false positives**: the pre-existing `последние N дней` search does not match week wordings (`неделю`/`недели` do not match the day-stem alternation); day-form regressions unchanged (`за день` → `last_1_calendar_days`, `за 5 дней` → 18.10 start, `последние 10 дней` → 13.10 start).

## P3 — Coverage guard + date-field invention — GREEN (with independent semantic report)

- `_TASK_PERIOD_INTENT_RE` now matches: `…за последнюю неделю`, `…за прошлую неделю`, `задачи за последнюю неделю`, plus all pre-existing forms (`с 30.09.2026`, `за 5 дней`, `за период`); does NOT match a plain `покажи задачи Калачанова` (no false trigger). The R1 note that the coverage guard would not fire for week wording is closed.
- **No date field invented by the delta**: the R2.1 diff adds no "создан/created/updated" wording anywhere in logic or user-facing text.

**Independent dimension report (per spec — parsing as `created_period` ≠ resolved user intent):**
- Parser: field-agnostic — it resolves only a time window; field choice belongs to the skill contract (comment in `8090bb6`).
- Skill contract (pre-existing, `task_catalog.py`): *"For a bare task-search period, use creation time as the default time dimension. If the user explicitly names another dimension (updated time, deadline, time-in-status), do not reinterpret it as created_period."* — i.e. creation is a **documented, transparent default**, not a silent invention.
- Live proof of transparency: T2c's answer states the dimension explicitly («созданные с 30.09.2026»), matching the R1 requirement that the creation dimension be stated, not pretended-ambiguous.
- Residual ambiguity: if a user says «за последнюю неделю» meaning activity/updated, the agent returns creation-period results per the documented default. Product decision item, not a code defect. The R1 defect — a clarification that claimed the *duration* was ambiguous and pre-selected "период **создания**" while the parser couldn't even parse the phrase — is gone (no such NC is reachable for week wording anymore).

## P4 — REAL AS21 A/B source oracle — GREEN (week + explicit continuation), one pre-existing boundary reported

Oracle (fresh, bounded, no hardcoding historic counts): task-api `assignee-tasks?assignee=Kalachanov.V.V&limit=100&max_pages=500` → **2990 rows, 0 missing created_at, 30 pages, ~24s**; open classification replicated from `Task.is_open` with the **raw `swtr_attributes.workflow_status.value.statusType`** as primary (this route does not expose statusType on the simplified `source_data.workflow_status` string — first oracle draft read the wrong layer and was corrected; with the correct layer it matches A230R1's independent counts exactly: open_all=617, week=5, since-30.09=111).

### Case W — «покажи открытые задачи Калачанова за последнюю неделю» — GREEN (2/2 COMPLETED, exact)

| Run | Wall | Terminal call | Result |
|-----|------|---------------|--------|
| T1 | 96.4s | `member.resolve(Калачанов)` → `task.search_created(created_period="последнюю неделю", reference="Калачанов", status="not_completed")` | **count=5** — [STS-595942, STS-595782, STS-595781, STS-593477, STS-593400] |
| T1b | 59.0s | same, `created_period="за последнюю неделю"` | **count=5 — same 5 keys** |

- Window: `created_from=2026-10-16T00:00:00+03:00` (today−6 00:00 MSK), `created_to` = run execution time, `period_kind=last_7_calendar_days` — exact rolling semantics on the wire.
- **Parity vs fresh oracle: EXACT** (5/5 keys both runs; `STS-595942` created 2026-10-21T13:35:18 MSK point-read proven, in window). R1's deterministic parser ValueError → spurious «неоднозначно понять период» clarification is **closed**; the answer states the dimension (creation) per the documented contract.
- Both runs: 0 LLM 429s, 0 source 5xx, all reads bounded.

### Case C — continuation `с 30.09.2026` — GREEN in executable form; bare form = pre-existing planner boundary (typed, safe)

- **T2c (explicit continuation, same session r2)** «покажи открытые задачи Калачанова с 30.09.2026» → **COMPLETED 67.4s**, `task.search_created(created_period="с 30.09.2026", reference="Калачанов", status="not_completed")` → **count=111 — EXACT vs fresh oracle (111/111)**, `explicit_start_to_now`, from 30.09 00:00 MSK, sample keys include WMB-30482 (cross-space, source-true). The R1 T2 mechanics (executor + open status preserved, «с» inclusive-to-now, source-verified count, answer states creation dimension) are all retained.
- **Bare continuation «с 30.09.2026» alone (2/2 deterministic)**: planner resumes with **only** `task.search_created(created_period="с 30.09.2026")` — it **drops the prior turn's reference+status** (trajectory rationale: «User gave a bare task-search period … with no other constraints») → handler's pre-existing guard `_live_query` raises the **typed** `AS21SourceUnavailable` ("requires a bounded person or product space") → `FAILED warning=source_unavailable` in 6.7–7.8s, **0 LLM 429s, 0 tenant scan actually executed** (proven by direct probe: bare unscoped task-query takes 253.5s and is itself incomplete — CRPV/STS exceed the 10k pagination cap — so the typed rejection is the correct safe behavior, not a source outage).
- Classification: **pre-existing, not an R2.1 regression** — the R1 C2 flow could never reach a working T2 (R1's T1 was the parser NC; there was no cid-based continuation available). The bare-continuation drop belongs to the documented session-context/planner-reliability open class (A229M2 lineage: planner does not reliably carry prior-turn person+status into a continuation turn). Safe fail-closed; no fabrication; no false zero.
- 429 vs parser distinction: **0 429s in the entire session log**; every failure in this session is code-deterministic (parser rejections in P2, typed guard rejection in T2-bare), no provider failures.

## P5 — Full regression, build, UI smoke, retained goals — GREEN (with retained C5 note)

| Suite | Result |
|-------|--------|
| V4-focused (`-k "v4 or V4 or agent_core"`) | **333 passed, 0 failed** (1.87s) |
| Full po-agent suite | **23 failed / 1609 passed / 12 skipped / 11 errors** — stable across 2 runs; **0 new failures vs baseline**: read-only worktree at `6fb335d` gives 24 failed/1558 passed/11 errors and the failure-set diff is exactly one **baseline-only** flake (`test_harness_api_v1.py::test_as21_diagnostics_reports_runtime_wiring_without_secrets`, passes at HEAD); remaining 23F+11E are the pre-existing legacy classes (core8/harness legacy fixtures, real-LLM integration env, live task-api env expectations) — none in the V4/period/week domain. New file adds 9 collected tests (1605→1655), all passing. |
| Task API SWTR suite (`-k swtr`) | **57 passed, 1 failed** (`test_s21_agent_integration.py::test_swtr_adapter_initialization` — known pre-existing env failure, stable since A226R2/A229 lineage) |
| Frontend build (`tsc && vite build`) | **exit 0** |
| A229M2.2B1 3-goal retained (`test_v4_missing_goal_execution.py` + `test_v4_goal_coverage.py`) | **27 passed, 0 failed** — not broken |
| UI smoke (Playwright, browser → vite 5175 → agent 8004) | **API + chat GREEN; panel raw-envelope = retained C5** (see below) |

**UI smoke detail:** week query in the agent chat — response pair `COMPLETED`, terminal `task.search_created` count=5, `task_keys` exact, window 16.10 00:00→now, `period_kind=last_7_calendar_days`; chat bubble renders the grounded markdown answer with a proper task-key table (STS-595942/595782/595781/593477/593400). The V4 **result panel** additionally prints the raw capability envelope JSON (`"capability_id":…`) as user content — this is the **pre-existing A230R1 C5 raw-envelope leak class** (frontend is **byte-unchanged** since the C5 baseline `8bb68b2`, proven by `git diff --stat`), explicitly out of R2.1 scope. No NEW leak introduced by R2.1.

### Session audit (agent log, all runs)

| Metric | Value |
|--------|-------|
| LLM 200 OK | 47 |
| LLM 429 / 5xx | **0 / 0** |
| task-api calls | 103 — **all GET, all 200** |
| Unscoped tenant scans (task-query without space/assignee) | **0** |
| Local store reads (`/api/v1/tasks`) | **0** |
| Mutations | **0** |

## Open semantic issues (carried, per spec)

1. **C1 (rolling week): CLOSED at R2.1 scope** — parser + guard + exact live parity.
2. **C2 (continuation «с 30.09.2026»): CLOSED at R2.1 scope** — executable continuation 111/111 exact, dimension stated; the R1 RED aspect (silent creation dimension) is resolved as a **documented, transparent contract default** (creation) — residual activity/updated ambiguity = product decision item, not a defect.
3. **Bare-continuation planner drop** (new observation, pre-existing class): a bare «с 30.09.2026» follow-up loses prior-turn person+status → typed fail-closed. Safe; belongs to the session-context planner-reliability track (A229M2 lineage), not R2.1.
4. **C3 (person+date-range worklogs): NOT fixed — out of scope** (no owner change touches worklogs; untouched).
5. **C4 («ты тут?» ping latency): NOT fixed — out of scope** (no presence fast path added; untouched).
6. **C5 (raw capability envelope in V4 result panel): NOT fixed — out of scope**, re-observed live in the UI smoke (frontend byte-unchanged since C5 baseline).
7. Session auth/ownership remains OPEN (client-chosen session_id) — deployment blocker, unchanged.
8. Minor (non-blocking): `normalize_task_status` lacks masculine «открыт» (map has «открыта»); at the assignee route the authoritative `statusType` ("pause") governs open classification so no count impact — but name-only routes would classify «Открыт» as UNKNOWN.

## QA artifacts (local)

- `/private/tmp/qa230r21/` — p2_boundaries.py, oracle_week.py (+oracle_week.json), t1_week.json, t1b_week.json, t2b_since.json, t2c_since.json, agent.log
- `po-agent-platform-v2/frontend/e2e/qa230r21-week.smoke.spec.ts` (untracked QA harness; asserts the C5 "no raw JSON" invariant, which fails by design until C5 is fixed — API/chat assertions all pass)
- Baseline worktree at 6fb335d removed after use.

**STOP per spec — partial gate R2.1 only. No production changes made; C3–C5 remain RED/OPEN for their own assignments.**
