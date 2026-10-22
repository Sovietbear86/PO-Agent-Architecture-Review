# A230R1 — UI Real-Query Failures: Independent Source-Oracle Diagnostics

**Verdict: AGENT_CORE_V4_A230R1_UI_REAL_QUERY_RED** (4 of 5 cases RED; Case 2 mechanics GREEN with semantic note)

## Identity

| Field | Value |
|-------|-------|
| TESTED_HEAD | `8bb68b21c266fb42ef2c7af97b4b00405564f574` (docs-only over A229M2.2B1 GREEN de0249a) |
| REPORT_COMMIT | _(this commit)_ |
| Date | 2026-10-22 (server-local MSK; UTC 2026-10-22 ~11:40–16:40) |
| Branch | `feat/core8-real-query-hardening-v2` |
| Services | agent 8004 (PID 75119 @8bb68b2, flags ALL OFF default), task-api 8241 (PID 78133), MCP 3000 (PID 78067), vite [::1]:5175 (PID 81246, proxy → localhost:8004) |
| A229M2.2B1 verdict | UNCHANGED (GREEN, report de0249a). No A229M2.2B1 goal re-run required for these new cases; flags were OFF. |

## P0 — Frozen Core (re-verified this session)

Core 6/6 **byte-identical** to `6fb335d` (git blob hashes, worktree vs ref):

| File | Hash |
|------|------|
| agent_core_v4.py | 52100ca1 |
| agent_core_v4_robust.py | 3bdb4d09 |
| agent_core_v4_reliable.py | 1f7562dc |
| agent_core_v4_completion.py | cf75a6d6 |
| v4_plugin_registry.py | d82929d1 |
| llm/real.py | 1cc10e12 |

Flag matrix: agent started with all three goal flags OFF (`ps eww` verified); no executor/guard/continuation markers in any response of this session. Worktree clean except `GIGACODE.md` (pre-existing).

## Session audit (agent_off.log, 17 query requests)

| Metric | Value |
|--------|-------|
| LLM 200 OK | 57 |
| LLM 429 | 32 (sustained degraded endpoint window, intermittent throughout) |
| LLM 500 | 1 |
| Source GETs (task-api) | 54 — all bounded (assignees/resolve + task-query assignee-scoped max_pages=100 + sprints/health) |
| Local store reads | 0 |
| Mutations to task-api | 0 |
| Source 5xx | 0 |

Environmental: api.ai.sbt 429/500/ReadTimeout throughout the session — wall times inflated vs A229 baseline; all provider failures terminated typed FAILED (fail-closed correct).

---

## CASE 1 — «покажи открытые задачи Калачанова за последнюю неделю» — **RED**

**Reproduced 4/4** (3/3 in `case1.py` 157–200s + 1 retry 24.4s), deterministic, LLM-independent in the root cause:

- Status: `NEEDS_CLARIFICATION` (warning `v4_planner_needs_clarification`), question: «Не удалось однозначно понять период в запросе. Уточните период создания задач…»
- Trajectory: loaded `[tasks.search, task.search_created]`; **0 executed capabilities**; stored error (captured verbatim in retry):
  `ValueError: created_period must contain 'последние N дней'/'last N days', 'за N дней'/'за день'/'сегодня', an explicit start date such as 'с DD.MM.YYYY по сегодня', or two explicit dates (DD.MM.YYYY or YYYY-MM-DD)`

**Root cause (code-exact):** the period parser `_parse_human_created_period` (`harness/v4_plugins/_task_live_handlers.py:330-395`) supports only day-granular relative expressions (`последние N дней` / `last N days`, `за N дней`, `за день`, `сегодня`), explicit two-date ranges, and `с DD.MM.YYYY [по сегодня]`. The week unit («неделю»/«неделю», «последнюю неделю») **has NO branch** → the planner's (correct) `task.search_created(created_period='за последнюю неделю')` raises ValueError → bounded repair exhausts (the raw phrase is unparseable by construction) → `_promote_planner_failure_to_clarification` (api/v1/__init__.py:279-293) converts to NC.

**Spec violations:**
1. The spurious «неоднозначно понять период» — the duration IS unambiguous (rolling 7 days); the defect is a parser grammar gap.
2. The clarification asserts the date dimension is **creation** («период создания задач») — silently imposing `created_at` for an unspecified dimension. The query only says «за последнюю неделю»; the dimension was never established.
3. Note: the API period-intent regex (`__init__.py:147-152`) also lacks a week branch, so the coverage guard (`v4_constraint_coverage_clarification`) would not even fire for week wording — the NC comes purely from the planner-failure promotion.

**Oracle (for the fixed behavior):** full-tenant Kalachanov corpus 2990 rows (task-query assignee-scoped, 27.8s, 0 missing created_at); rolling 7-day window 15.10 00:00 MSK → now: **5 open** = [STS-593400, STS-593477, STS-595781, STS-595782, STS-595942]; open-all = 617.

**Control (supported wording) «за последние 7 дней»:** executed path `member.resolve → task.search_created` — one run COMPLETED server-side (342s wall, client 300s timeout; LLM degraded + full-tenant scan), one run FAILED on 429s. The parser/period grammar is the only gap; the capability chain works.

**Proposed smallest fix (outside frozen Core):** plugin only — (a) extend `_parse_human_created_period` with week/month units (`последн(?:ий|юю|ие|их) (?:недел(?:ю|ю|е|ю)|month)`, `last N weeks`): week = 7 calendar days, month = calendar month, same 00:00 MSK convention; (b) add the week pattern to `_TASK_PERIOD_INTENT_RE` so the coverage guard covers it; (c) product decision recorded in the skill contract: whether the default date dimension is creation — if yes, the clarification must say so transparently, not pretend the duration is ambiguous.

---

## CASE 2 — continuation «с 30.09.2026» — **RED (partial): mechanics GREEN, dimension silently fixed to creation**

Flow (fresh session, same chat):

- **T1** (original query) → NEEDS_CLARIFICATION, `cid=b209d877…` (Case 1 defect above), 18.9s.
- **T2** = same session + `clarification_id` + «с 30.09.2026» → **COMPLETED, 40.4s**:
  `task.search_created(created_period='с 30.09.2026', reference='Калачанов', status='not_completed')` → **count=111**, keys sample [STS-595942, STS-595782, STS-595781, STS-593477, STS-593400, WMB-30482, STS-584266, …].

**VERIFIED source-backed (oracle from same 2990-row corpus, window 30.09 00:00 MSK → now):** open tasks created since 30.09 = **111 — EXACT parity**. Agent's answer states the dimension: «созданных с 30.09.2026 по сегодня» (creation). `с` handled as inclusive lower bound to now by the parser (`explicit_start_to_now` branch) — correct.

**GREEN aspects:** continuation preserved original executor (Калачанов) and open status (not_completed); «с DATE» is NOT treated as an unrelated new query; count is source-verified; no fabricated status.

**RED aspect (semantic):** the creation dimension was never explicitly chosen by the user — it was fixed by the T1 clarification text («Уточните период **создания** задач»), which is itself Case 1's defect. Spec: «no fabricated creation-specific filter unless explicitly chosen». The continuation mechanism is faithful to the (mis)stated dimension; the dimension default must come from a product decision (see Case 1 fix). Marked RED until the dimension is either transparently defaulted or the clarification asks for the **specific date field**.

**Oracle:** `/private/tmp/qa230r1/oracle_c2.json` (111, window 2026-09-29T21:00Z→2026-10-22T16:21Z, corpus 2990, 0 missing created_at).

---

## CASE 3 — «покажи списания Гаранина с 01.10.2026 по сегодня» — **RED**

**Reproduced 3 attempts:**
- Run 1: FAILED 19.6s — `planner failed robust bounded repair: ['HTTPStatusError' x4]` (429 window, environmental).
- Run 2: FAILED 194.2s — `['HTTPStatusError', 'ValidationError', 'HTTPStatusError', 'ReadTimeout']` (user's screenshot: FAILED after 175936 ms — same class).
- Retry (LLM recovered): **NEEDS_CLARIFICATION 51.9s** — `planner failed robust bounded repair: ['ValidationError', 'invalid_recovery_action' x3]`, promoted by `_promote_planner_failure_to_clarification` (planner-failure branch, generic question asking for «исполнитель, пространство, статус, тип задачи, период создания и/или спринт»).

**Root cause (capability gap + wrong-surface clarification):**
1. **No person+date-range worklog capability exists.** Worklog source is per-task only: `GET /api/v1/swtr-read/tasks/{task_code}/work-logs` (task-api swtr_read.py:944) via `adapter.get_task_worklogs(task_key)`. Plugin capabilities: `task.worklogs`/`task.time_spent` (task_key only); `member.time_spent`/`member.worklogs`/`member.utilization_actual` **require space+sprint** and raise typed `V4NeedsClarification` («Укажите продукт/пространство и спринт…») when absent. A person+explicit-date-range query (no sprint, no task) has no mapped path → the planner cannot construct a valid call (ValidationError: member skills reject sprint-less/date-range args; task skills lack a person arg) → bounded repair exhausts.
2. **Wrong-surface terminal:** the query is a worklog intent, but the failure surfaces either a generic trajectory error (screenshot) or a **task-search filter clarification** (retry) — listing task filters that don't apply to worklogs. Spec requires typed UNSUPPORTED/worklog-specific clarification.
3. A literal execution would be N+1 worklog fan-out over the person's full corpus (Kalachanov analog: 2990 tasks; corpus read alone 27.8s) with client-side date filtering — no bounded person-scope worklog route exists.

**What actually exists (established independently):** per-task worklogs (REAL_AS21, complete-flagged), sprint-window member/sprint/team aggregates. Person+date-range: unsupported.

**Proposed smallest fix (outside frozen Core):** (a) skill-contract/procedure wording so the planner maps person+worklog+date-range to a typed UNSUPPORTED/clarification naming the missing dimension (sprint OR task), never a task-search filter list; (b) optionally a person-scoped bounded worklog route in task-api (assignee → bounded task set → per-task work-logs with semaphore, as in A215F2 pattern) if the product wants the feature; (c) provider 429s must surface typed FAILED, not a 175s hang (already fail-closed — wall time is the residual issue, LLM endpoint reliability).

---

## CASE 4 — «ты тут?» ping — **RED** (latency)

**Measured (3 runs, 2 COMPLETED, 1 FAILED-on-429):**
- Run 1: COMPLETED 77.7s; `agent.help(mode=ping)` → `data={mode: ping, available: true, source: AGENT_RUNTIME}`, answer «Да, я на связи.» (15 chars), `ui={result_kind: meta, preferred_widget: skill_catalog}`.
- Run 2: FAILED 12.4s (429s, environmental, typed).
- Run 3: COMPLETED 86.0s; answer «Да, я на связи. Чем могу помочь?» (32 chars).
- User's screenshot: 81876 ms — matches measured distribution (LLM-dependent).

**Latency decomposition (measured):**
- Handler intrinsic (in-process, no LLM/source, n=20): **p50=0.000ms, p90=0.001ms, max=0.002ms** — the capability is pure local.
- End-to-end 77.8/86.0s = **100% LLM planner + response-synthesis** (several sequential chat/completions calls at 15–50s each under load, +429 retries). Network to agent is ms-scale (health probe). Cold/warm: no difference — the LLM path is always taken.

**RED:** a presence ping must be local/fast; measured budget from implementation baseline = handler 0.001ms, yet e2e = 77–86s. The ping has no fast path: no deterministic presence short-circuit before the planner, and the final synthesis POST is always paid.

**Proposed smallest fix (outside frozen Core, presentation/API seam):** deterministic presence short-circuit at the API seam (pattern: A229F3R postcondition guards) — when the query matches a bounded presence lexicon and the planner's first decision is `load agent.help`, answer directly from the ping capability result (0 LLM, <100ms); or at minimum elide the synthesis POST for `agent.help(mode=ping)` (TerminalSynthesisElider seam already exists, flag-gated) with the handler's fixed answer text. No Core change.

---

## CASE 5 — `skill_catalog kind:meta` UI normalization — **RED** (raw JSON leak, browser-proven)

**Browser forensics (Chromium, 1440×900, screenshots `case5/ping.png`, `case5/skills.png`; raw capture `case5/query_log.json`, `case5/render.json`):**

1. **The V4 panel renders the raw capability envelope as user content.** For the ping the panel body is literally:
   `{"step":1,"capability_id":"agent.help","arguments":{"mode":"ping"},"answer":"Да, я на связи.","data":{"mode":"ping","available":true,"source":"AGENT_RUNTIME"}}`
   with header `V4 · Данные получены · widget: skill_catalog · kind: meta`. DOM markers all true: `capability_id`, `"arguments":`, `"step":`, `"data":` visible on the page.
2. **Mechanism (frontend code-exact):** `V4ResultPanel.tsx` → `structuredRows(result.data)` → `findField` (recursive, returns the first `results` array it encounters) picks `result.data.results` — the list of capability envelopes. Each envelope row has no `key/id/title/name` → `rowLabel` falls through to `JSON.stringify(record)` → the full internal step JSON becomes a visible row. The panel never consults `ui.result_kind`; there is **no `kind=meta` renderer at all** (grep: zero `meta` handling in frontend/src).
3. **Meta mislabel:** the ping response (no catalog) still carries `preferred_widget=skill_catalog` (agent_help.py:120-121 is per-capability, not per-mode) — the widget label lies for mode=ping. `source: AGENT_RUNTIME` is displayed as-is inside the dumped JSON; the page's `REAL AS21` text is from other dashboard panels (adapter label / attention rows), not from the meta response — no explicit mislabeling of the meta source found, but the raw dump itself leaks internal structure, violating «never prints internal step/capability_id/arguments/data JSON as user content».
4. `skills` mode (72 skills) renders a friendly LLM summary in the chat bubble — but the same panel still shows the ping envelope from the prior turn's result (panel bound to the page's last result object), and `Evidence 0 · trace` + `Не удалось получить корректный результат` appear correctly on FAILED states (verified in resultState.ts:142/152; ERROR state text is the generic message — safe, but it follows the raw-JSON success state, so the panel's two states are inconsistent).
5. No console errors; 0 5xx; network clean (proxy → 8004).

**Proposed smallest fix (frontend only):** in `V4ResultPanel.tsx`, branch on `result.ui.result_kind === 'meta'`: render only `answer` (or a compact «агент на связи / N навыков» line); never run `structuredRows` on meta envelopes. Optionally agent_help.py: make the widget mode-aware (`presence` for ping). No Core change.

---

## Per-case verdicts

| Case | Verdict | First failing boundary |
|------|---------|------------------------|
| 1 (rolling week) | **RED** | Period parser `_parse_human_created_period` has no week unit → ValueError → promoted NC that pretends the duration is ambiguous AND asserts the creation dimension |
| 2 (continuation «с 30.09.2026») | **RED (partial)** | Continuation mechanics GREEN + count 111/111 EXACT vs oracle; RED only on the silently-fixed creation dimension inherited from Case 1's clarification |
| 3 (Гаранин worklogs) | **RED** | No person+date-range worklog capability; failure surfaces as generic task-search filter clarification (or 175s hang under 429s), not typed UNSUPPORTED for worklogs |
| 4 («ты тут?» ping) | **RED** | e2e 77–86s for a 0.001ms local capability — no presence fast path; synthesis always paid |
| 5 (meta widget) | **RED** | V4ResultPanel JSON.stringifies the full capability envelope for kind=meta (no meta renderer) |

**FIRST FAILING BOUNDARY of the assignment (chronological, highest-priority):** Case 1 — deterministic parser-grammar gap at `harness/v4_plugins/_task_live_handlers.py:330-395` (no week/month units) surfaced through `api/v1/__init__.py:279-293` (promotion text mislabels the defect as period ambiguity and pre-selects the creation dimension).

## Non-blocking observations

1. **LLM endpoint degraded** (32×429, 1×500, ReadTimeouts all session) — all provider failures terminated typed FAILED (fail-closed correct); wall times not comparable to A229 baseline.
2. **Duplicate `member.resolve`** per request (2× assignees/resolve in 6/6 inspected trajectories) — known efficiency class (A229R1 O3), not a defect.
3. `task-query?assignee=X` with `max_pages` < needed pages → typed 502 «AS21 assignee pagination exceeded max_pages» (guard works; agents correctly use max_pages=100; 2990-row full-tenant scan = 27.8s).
4. Person-scope task search (no space) legitimately triggers full-tenant assignee scans — bounded but slow; spec-level decision needed for person-only queries.
5. Overview page auto-fires snapshot POSTs on mount (attention queue etc.) — unrelated chat queries appear in the network log; matched by request body.

## Security

- Session ownership/auth binding **STILL OPEN** (client-chosen session_id; no principal binding) — local QA only, never release-ready for remote/multi-user.
- No mutations, no local-store reads, no unscoped tenant scans beyond the bounded assignee corpus reads; flags OFF by default; fake mode never used.

## QA artifacts (local)

- `/private/tmp/qa230r1/` — p0_core_hashes.py, case1.py, case2.py, case3.py, case4.py, case5_browser.mjs, ping_handler_baseline.py, oracle_c1.py (+oracle_c1.json, oracle_c2.json, c1_corpus.json), retry_batch.json, case2.json, case3.json, case4.json, agent logs per mode, case5/{ping.png,skills.png,query_log.json,render.json}.

**STOP per spec — no production changes made. Owner applies isolated fixes (plugin period parser + API clarification text + meta widget renderer + ping fast path + worklog capability decision), then full re-gate: V4 blast, Task API/SWTR, frontend build, browser smoke, A229M2.2B1 REAL AS21 goals, and these four scenarios; fresh TESTED_HEAD; ZERO FAILED; Core 6/6 unchanged.**
