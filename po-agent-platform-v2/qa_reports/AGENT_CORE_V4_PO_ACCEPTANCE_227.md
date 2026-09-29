# A227 — PO acceptance corrections — QA report

**Verdict:** `AGENT_CORE_V4_PO_ACCEPTANCE_RED_A227`
**Classification:** `RED_PREEXISTING_PLANNER_RELIABILITY_PERSON_COMPOSITION` (A179 lineage) — NL task search (P3) blocked by V4 planner failures on person + multi-constraint queries; **not** an A227 frontend regression.

- START_HEAD: `db5e35f1b378b6ffde0c10085af8b68e4bf1e6b5`
- Branch: `feat/core8-real-query-hardening-v2`
- Date: 2026-09-29
- Role: QA/adversarial tester only (no code modified)
- STOP rule: first RED at P3 → P4 (partially observed), P5–P7 NOT executed.

## Owner changes under test

- snapshot timeout 65s → 120s (`pageSnapshot.tsx` `REFRESH_TIMEOUT_MS = 120_000` — verified in source);
- Tasks = one natural-language input + `Найти` + `+ Локальная задача`; no mode buttons; no product-space selector; no auto-query; raw text sent to V4; task collections → cards, non-task → grounded answer;
- Quality: separate `taskRefreshNonce` / `agingRefreshNonce`; page refresh = quality/missing/acceptance only; Aging Refresh = Aging only.

## P0 — build/diff: GREEN

- Diff `4867472..db5e35f` = frontend only: `Pages.tsx`, `QualityDashboard.tsx`, `pageSnapshot.tsx`, `workspace.css` + docs (`GIGACODE_NEXT_ACTION.md`, `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`, `V4_DOD_LOCK.md`). **Zero** changes in `po-agent-platform-v2/src` (Agent Core/planner/runtime) or `task-api` → no architecture drift.
- `tsc --noEmit` clean; `vite build` clean.
- Focused suites: `test_agent_core_v4_task_search_source_status.py`, `test_agent_core_v4_team_aging.py`, `test_agent_core_v4_task_search_release_regression.py`, `test_agent_core_v4_task_catalog.py` → **18/18 pass**.

## P1 — Overview refresh reliability: GREEN

Browser C (fresh context, 1440×900):

| Check | Result |
|---|---|
| Initial 4 snapshots settle | 87s, metrics 119/40/7/25.2%, rich brief |
| Refresh completes before 120s | **68s**, no false-timeout (spec: normal source latency 60–80s must not false-fail) |
| Old snapshot visible during refresh | yes (stale brief rendered while `Обновляем…`) |
| Button returns `Обновляем…` → `Обновить` | yes |
| Timestamp ru-RU advances | `29.09.2026, 22:14` → `29.09.2026, 22:15` |
| 4 POSTs on refresh (4 snapshots) | 4 |
| Injected genuine hang (route never fulfilled) | at **120s** error state `Не удалось обновить · данные на 29.09.2026, 22:15`, **stale data preserved** (brief still rendered), button re-enabled |
| Retry after failure | succeeds in 68s, error clears |
| Away/back cached revisit | **0 POSTs both directions** (overview ↔ team, pre-warmed) |

The earlier away/back sample that showed 6 POSTs was the team page's legitimate first mount; the pre-warmed control proves cached revisit = 0.

## P2 — Tasks UI surface: GREEN

- Exactly one input (`aria-label="Текстовый поиск"`, placeholder `Например: Открытые задачи Калачанова с вложениями в пространстве WMB`); toolbar buttons exactly `[Найти, + Локальная задача]`.
- Mode buttons `Исполнитель/Статус/Спринт/Релиз`: **absent**. Product-space selector: **absent** (0 selects with space options).
- First open: **0 auto POSTs**; idle text `Введите запрос естественным языком и нажмите «Найти».`.
- Submit sends raw query verbatim (captured POST body `{"query":"Открытые задачи Калачанова с вложениями в пространстве WMB"}`).

## P3 — NL composition: RED (first blocking failure)

Independent oracles (REAL AS21 via task-api, read-only):
- WMB ∩ Kalachanov.V.V: **5 tasks, all `done`** (WMB-30000/29890/29995/29830/29242); 3 have attachments (5+1+10 files) — so the correct answer for "open + attachments" is a **grounded empty**, with teeth against constraint-dropping.
- DMS-SPRNT-3: 75 tasks; canonical `IN_PROGRESS` set = **11** (10 named "In progress" + 1 "На исправлении" via statusType=progress fallback; Тестирование→QA, In review→IN_REVIEW, QA→QA are distinct canonical states).
- DMS: 450 rows, 83 open; aging >7d = 77, >15d = 68.
- "Открытые задачи в DMS" control: agent returned **83 = exact oracle parity**.

### P3-A `Открытые задачи Калачанова с вложениями в пространстве WMB` — RED

- Browser: terminal `ERROR :: Ошибка — Не удалось получить корректный результат.` (Skill: —, Evidence: 0).
- First API probe (same process, minutes earlier): **COMPLETED, correct** — `task.search_attachments`, 17 evidence, trajectory `tasks.search → space.resolve(WMB) → member.resolve(Калачанов→Kalachanov.V.V, REAL_AS21) → task.search_attachments`; answer: *«Открытых задач Калачанова (Kalachanov.V.V) с вложениями в пространстве WMB не найдено. В WMB обнаружено 3 задачи с вложениями, но все они имеют статус Закрыт»* with the 3 keys/attachment counts — exactly the grounded empty the oracle requires.
- Then **5/5 subsequent runs FAILED** (reprobe ×3 + control ×1 + final probe ×1), deterministic within the window, identical signature:
  `planner failed robust bounded repair: ['ValidationError' ×4]` → `Agent Core v4 не смог безопасно завершить траекторию.`
- Failing trajectory (evidence `/tmp/qa227_control.json`): turns 1–4 valid (`load tasks.search` → `space.resolve{reference:WMB}` → `load task.search_attachments` → `member.resolve{reference:Калачанов,space:WMB}`), then the composite person+status+attachments call is schema-invalid on **all 4 bounded-repair attempts** — repair retries the same failing generation.

### P3-B `Задачи Семавина по рискам` — RED

- Browser: same ERROR state.
- First probe: **COMPLETED, correct** — `member.resolve(Семавин→Semavin.M.M)` + `task.search_text{phrase:"риск", assignee:Semavin.M.M}` bounded over all 5 approved spaces, `source_complete=true`, answer: *«Поиск по фразе «риск» в закреплённых за ним задачах вернул 0 результатов»* — no invented risk rows.
- Then **3/3 FAILED**, identical `ValidationError ×4` signature.

### P3-C `Задачи в работе в сентябрьском спринте по DMS` — non-deterministic, false-zero risk

- Browser run: **11/11 exact** canonical IN_PROGRESS keys (`tasks.search`, evidence 12 = 11 tasks + sprint resolution), sprint correctly resolved to DMS-SPRNT-3.
- Reprobe 3×: **1/3 correct** (11 tasks) and **2/3 confident false zero** via the `sprints.discover` path: *«В сентябрьском спринте DMS-SPRNT-3 задач со статусом «В работе» нет — найдено 0»*. The correct variant phrases the status as «In Progress», the false-zero variants as «В работе» — status-literal sensitivity on the discover→search path (11 real source-backed tasks exist).
- A confident **false zero** on a source-populated query is a correctness risk, not just a reliability flake.

### P3-D `Спринты в DMS` — GREEN

- Non-task output rendered as a grounded rich answer (`sprints.list`, 3 evidence): 3 sprints with code/name/status/period table + «Активный спринт — DMS-SPRNT-3». No fake empty task cards.

### Root-cause classification

- The defect is in the **V4 planner** (person-identity → multi-constraint composite call), i.e. the documented **A179/180/181 defect class** ("Qwen3.8 planner invalid decision at step 2 after person/lookup resolution; fix: constrained/structured output or deterministic fallback"). Owner fix still pending per memory.
- **Not introduced by A227:** the diff is frontend-only (P0), the failing component is untouched, and the same queries returned correct COMPLETED responses in the same process minutes earlier (state change, not code change).
- Controls prove the agent is otherwise healthy right now: overview/daily-brief COMPLETED (17s), sprints.list COMPLETED, single-constraint open-status COMPLETED with **83 = exact oracle**.
- Completion rate on the person-composition class in this window: **2/9** (A 1/6, B 1/4, C correct 2/4 incl. false zeros) — same order as A179's 3/16.

## P4 — task rendering/persistence: partial (harness crash, app signals observed)

QA-harness crash (Playwright selector ambiguity: `.task-drawer .icon-button` matched the closed local drawer) — not an app defect. Observed before the crash:
- Task cards rendered with key/status/title/assignee-meta; card click opened Task Details drawer with real source data (status/Исполнитель/Спринт DMS-SPRNT-3) and live Task Intelligence (256-char answer loaded).
- Away/back, input-edit-no-submit, and Refresh-re-run checks were **not** completed → must be re-verified in the A227 re-gate.

## P5–P7 — NOT executed

Stopped per first-RED rule. Quality refresh isolation (P5), Aging DMS>7/>15 exact parity (P6), and retained regression (P7) remain open for the re-gate.

## Audit (A227 window, task-api access log)

- 488 HTTP lines: **0** local-store reads (`GET /api/v1/tasks`), **0** mutations, **0** unscoped tenant-wide task-query (99 task-query lines, all space/assignee-scoped).
- 8×502 = QA's own undersized oracle probe (`limit=2` on a >200-row space → `pagination exceeded max_pages` fail-closed — correct behavior, documented).
- No LLM endpoint 429/500 in the browser window (the failures are planner-decision ValidationErrors, not transport errors).

## Owner fix (proposed, not implemented by QA)

1. **A179-class fix (blocking):** constrained/structured output for the planner decision after `member.resolve`, or a deterministic fallback that assembles the known composite call (assignee + status + attachments + space) from resolved observations; bounded repair must not retry the identical failing generation 4× (4 identical `ValidationError`s = repair is a no-op).
2. **C false-zero (blocking, correctness):** audit the `sprints.discover → task.search` path for status-literal handling («В работе» vs «In progress»; canonical IN_PROGRESS set = 11 tasks in DMS-SPRNT-3); a source-populated query must never complete with a confident 0.
3. Add non-mocked regressions: person+attachments composition, person+phrase composition, discover-path status filter — each asserting source-exact keys, never fabricated empties.
4. Then full A227 re-gate: P3 A/B/C ×3 (browser), P4 complete, P5, P6 (DMS>7 = 77, DMS>15 = 68 oracles captured), P7.

## Evidence

- `/tmp/qa227_reprobe.json` — A/B/C ×3 with error detail; `/tmp/qa227_control.json` — simple/complex controls + full failing A trajectory.
- `/private/tmp/qa227_p1/run.log` — P1/P1b; `/private/tmp/qa227_p2p3p4/run.log` + screenshots `p3a.png/p3b.png/p3c.png/p3d.png` — P2–P4.
- `/private/tmp/qa227_oracle.json`, `/private/tmp/qa227_p3c_oracle.json` — REAL AS21 oracles.
- QA harnesses (untracked, per convention): `po-agent-platform-v2/frontend/qa_227_p1.mjs`, `qa_227_p1b.mjs`, `qa_227_p2p3p4.mjs`, `qa_227_p4.mjs`, `qa_227_p5p6.mjs`, `qa_227_p7.mjs`; `qa_227_oracle.py`.

## Services (left running)

- agent 8004 (PID 56837, @db5e35f code — A227 has no backend changes), task-api 8241 (system py3), MCP-SWTR 3000, vite [::1]:5175 (PID 70935, fresh on db5e35f).

## Non-blocking observations

- P3-A/B browser ERRORs are the agent's typed fail-closed presentation of `FAILED` (no fabrication, 0 evidence) — safe, but the NL surface surfaces them as a generic error; after the owner fix the grounded answers (already proven reachable) will render.
- `waitSettled`-style consumers should treat `data-state` panel states as terminal (QA harness note).
