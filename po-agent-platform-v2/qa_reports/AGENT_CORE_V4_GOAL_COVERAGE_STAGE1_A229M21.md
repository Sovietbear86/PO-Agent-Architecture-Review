# A229M2.1 — Typed Goal Detection + Postcondition Guard, Stage 1 Gate

**Verdict:** `AGENT_CORE_V4_GOAL_COVERAGE_STAGE1_RED_A229M21`
**First failing boundary:** P0 step 3 — `tests/test_v4_goal_coverage.py::test_one_terminal_cannot_prove_other_persons_collection` (owner's new suite: **2 failed / 7 passed**). Root cause is in production code: `api/v1/goal_coverage.py:128` person-matching direction. Per spec: STOP. No code was modified.

- **START_HEAD / TESTED_HEAD:** `846e571cef683ff9c0db5ebccc1bd9bf0d5b7ef2` (branch `feat/core8-real-query-hardening-v2`, in sync with origin)
- **Owner delta over A229M1 (`9a9903b`):** 5 commits — `9f85a6c` goal_coverage module (new, 179 lines), `92cc257` settings flag (default `false`), `0110697` API wiring (+6 lines), `3cbce13` offline matrix tests (new, 125 lines), `641ecf2` anaphoric related-task connector fix; plus docs.
- **Role:** QA only. No production/test/config/Core/UI modifications. No live flag flip (real stack untouched; P3 done in controlled offline harness).
- **Date:** 2026-10-14

---

## P0 — Safety / invariant / static tests (RED at step 3)

| Check | Result |
|---|---|
| Core 6/6 byte-identical to frozen checkpoint `6fb335d` | **PASS** — `git diff 6fb335d..HEAD` on the six core files is empty. Hashes at HEAD: `agent_core_v4.py` 52100ca1, `agent_core_v4_robust.py` 3bdb4d09, `agent_core_v4_reliable.py` 1f7562dc, `agent_core_v4_completion.py` cf75a6d6, `v4_plugin_registry.py` d82929d1, `llm/real.py` 1cc10e12 |
| No changes to Core/planner/registry/source/Task API | **PASS** — owner delta confined to `api/v1/goal_coverage.py` (new), `api/v1/__init__.py` +6, `config/settings.py` +5, `tests/test_v4_goal_coverage.py` (new), docs |
| `tests/test_v4_goal_coverage.py` | **RED — 2 failed / 7 passed** ← first failing boundary |
| `test_v4_browser_api_contract.py` + `test_agent_core_v4_task_created_period.py` + `test_v4_synthesis_elision.py` | **35 passed** |
| Configuration tests (`test_frontend_config.py`, `test_team_config.py` — the only config suites) | **46 passed**; new flag `Settings().v4_goal_coverage_guard_enabled == False` by default; env alias `PO_AGENT_V4_GOAL_COVERAGE_GUARD=true` parses to `True` |
| Full `test_agent_core_v4*.py` + `test_v4*.py` blast | **2 failed / 277 passed** — the 2 failures are exactly the owner's new-file failures; 0 new regressions elsewhere |
| Task API SWTR suites (`assignee_canonical`, `assignee_timestamps`, `task_query_partial/release`, `read_facade`) | **27 passed** (owner delta does not touch task-api; baseline retained) |
| Frontend `npm run build` | **exit 0** |

### F1 — production defect (first failing boundary)

`tests/test_v4_goal_coverage.py::test_one_terminal_cannot_prove_other_persons_collection`:
`assert coverage.proven == ("g1",)` → got `()`.

**Root cause (unit-proven):** `goal_coverage.py:128` matches a `person_tasks` goal as
`person_value.casefold().startswith(goal.person.casefold())` where `person_value` is the terminal's `reference`/`assignee` arg and `goal.person` is the query-text capture. The detector regex captures the **inflected** query word ("Калачанова", genitive, 9 chars); the planner's terminal carries the **normalized nominative** ("Калачанов", 8 chars — exact A229M1 live shape). A shorter string cannot start with a longer one → `False` → g1 UNPROVEN despite an executed, matching terminal. The direction is inverted for inflected forms (it is the query word that starts with the terminal reference, not vice versa).

**Consequences (all unit-proven with real A229M1 argument shapes):**
1. Owner's own test fails (shipped RED — recurring class A205-1/A205B/A217C/A229F1R: narrow new tests not run green before push).
2. **Spec P1 two-terminal control violated (false positive):** replay of M1 with both person terminals (`task.search_assignee{Калачанов, WMB}` + `task.search_assignee{Семавин, DMS}`) → `proven=()`, `unproven=(g1, g2)` → guard returns NEEDS_CLARIFICATION although "evidence and arguments truly cover all goals" → spec requires COMPLETED.
3. **Systematic false-positive class for canonical logins:** terminal references in login form (`task.search{assignee: "Kalachanov.V.V"}` — exact A229M1 C3p shape) match the query word in **neither** direction → any legitimately covered `person_tasks` goal through a resolved login is always unproven → guard would flag fully-covered responses for every person query the planner normalizes to a login.

### F2 — test-logic defect (secondary, same file)

`tests/test_v4_goal_coverage.py::test_wrong_task_key_does_not_prove_hierarchy`:
`assert coverage.unproven == ("g2",)` → got `("g1",)`.

M2 goals share the same span; goal ids are assigned after `sorted(set(found), key=(start, kind))` and `"task_hierarchy" < "task_lookup"` alphabetically → **g1 = task_hierarchy, g2 = task_lookup**. The coverage logic itself is correct (exactly one unproven goal = the wrong-key hierarchy `DMS-999`); the assertion labels the wrong id (A196-F1/A222R2 lineage: refreshed test not run to completion). Assert by kind or by the correct id.

**Owner fix (minimal, same files, then full re-gate):**
1. `goal_coverage.py:128` — inflection-tolerant person match, e.g. bidirectional stem prefix: `a = person_value.casefold(); b = goal.person.casefold(); a.startswith(b) or b.startswith(a)` (both len ≥ 4); this alone fixes F1 and the P1 two-terminal control. Canonical-login references additionally need identity binding via the trajectory's own `member.resolve` observation (A229M1 design R2 / `_CONSTRAINT_RESOLVERS` semantics) — recommend tracking as a named sub-item of the fix (login-form terminal must be accepted when a `member.resolve{reference=Калачанов…}` in the same results resolves to it).
2. `test_v4_goal_coverage.py` — correct the expected id in `test_wrong_task_key_does_not_prove_hierarchy` to `("g1",)` (or assert by kind).
3. Re-run: `pytest tests/test_v4_goal_coverage.py` green (9/9) → full A229M2.1 re-gate from P0.

---

## P1 — Offline replay (post-STOP diagnostic characterization)

Fixtures use **exact** A229M1 terminal capability ids + planner argument shapes (no oracle adjustment). DMS-267 parent source-truth = DMS-253 (A229M1 get_unit_links: 1 decomposition link) — absence may never be claimed without `task.hierarchy` evidence.

| Case | Goals (detector) | Terminal(s) in fixture | proven / unproven | Guard result | Assessment |
|---|---|---|---|---|---|
| M1 (1 terminal) | g1 person_tasks{Калачанова,WMB}, g2 person_tasks{Семавина,DMS} | `task.search_assignee{Калачанов,WMB}` | **() / (g1,g2)** | NEEDS_CLARIFICATION | Correct verdict (g2 truly unexecuted) but **g1 wrongly unproven** (F1) |
| M2 (1 terminal) | g1 task_hierarchy, g2 task_lookup (DMS-267) | `task.lookup{DMS-267}` | (g2) / (g1) | NEEDS_CLARIFICATION, question cites `task_hierarchy: DMS-267` | **CORRECT — DMS-267 false-parent claim blocked**; false prose stripped (answer=None, evidence=[]) |
| M3 (1 terminal) | g1 person_tasks{Калачанова,WMB}, g2 task_hierarchy{DMS-267} | `task.search_assignee{Калачанов,WMB}` | () / (g1,g2) | NEEDS_CLARIFICATION | Correct verdict; g1 wrongly unproven (F1) |
| M4 (1 terminal) | g1 hierarchy, g2 lookup, g3 person (DMS-267 ×2 + Калачанова/WMB) | `task.lookup{DMS-267}` | (g2) / (g1,g3) | NEEDS_CLARIFICATION, 2 parts cited | CORRECT |
| C5 (1 terminal) | g1 task_lookup, g2 task_relations (DMS-267) | `task.lookup{DMS-267}` | (g1) / (g2) | NEEDS_CLARIFICATION, cites `task_relations: DMS-267` | **CORRECT — "связанных задач не найдено" false claim blocked** |
| M2 two-terminal control | g1 hierarchy, g2 lookup | `task.lookup{DMS-267}` + `task.hierarchy{DMS-267}` | (g1,g2) / () | **COMPLETED** | No false positive ✓ |
| **M1 two-terminal control (spec: must stay COMPLETED)** | g1, g2 person | `task.search_assignee{Калачанов,WMB}` + `task.search_assignee{Семавин,DMS}` | **() / (g1,g2)** | **NEEDS_CLARIFICATION** | **FALSE POSITIVE (F1)** |
| M1 two-terminal, login-form refs | g1, g2 person | `task.search{Kalachanov.V.V,WMB}` + `task.search{Semavin.M.M,DMS}` | () / (g1,g2) | NEEDS_CLARIFICATION | **FALSE POSITIVE (F1 class: login refs)** |
| M2, hierarchy `source_unavailable: true` | g1, g2 | lookup OK + hierarchy unavailable | (g2) / (g1) | — | Freshness/completeness rule works ✓ (unavailable evidence never counts) |
| Wrong-key hierarchy (`task.hierarchy{DMS-999}`) | g1, g2 | lookup DMS-267 + hierarchy DMS-999 | (g2) / (g1) | — | Cross-goal/key isolation works ✓ |

## P2 — False-positive & scope safety (post-STOP diagnostic)

**Single-goal composed-filter controls — 0 false positives** (guard inert: fires only at ≥2 goals; detection yields 0–1):

| Case | Detector | Guard |
|---|---|---|
| C1 Semavin+DMS+open+defect+period | 0 goals | inert ✓ |
| C2 Kalachanov+WMB+attachments | 1 goal (person_tasks) | inert ✓ |
| C3s latest OLP sprint+Semavin+open+defect | 0 goals | inert ✓ |
| C4 in-progress ∩ attachments (one intersected collection) | 0 goals | inert ✓ |
| «Сравни DMS и OLP» | 0 goals (comparison → deferred, `detect_goals` returns `()`) | inert, **no fabricated coverage** ✓ |
| «Сравни незавершённые задачи в DMS и OLP» | 0 goals | inert ✓ |

**False negatives (valid multi-goal phrasings NOT recognized — documented, not failures of the conservative pilot):**
- `Задачи Калачанова в WMB и Семавина в DMS` (elided second «задачи») → 1 goal;
- `Задачи Калачанова в WMB и DMS` (same person, second space) → 1 goal;
- `Покажи DMS-267 и DMS-268` (two keys, no explicit «задач[уа]» verb near second key) → 0 goals;
- English (`Show tasks of Kalachanov in WMB and Semavin in DMS`) → 0 goals (Russian-only lexicon).

Recognized multi-goal alternates that DO work: «и её родителя» (родитель-lemma), «а также её иерархию» (comma+anaphora), three-person conjunctions (3 goals), anaphoric «связанные с ней задачи» (owner 641ecf2 fix, C5 green).

## P3 — Feature flag integration (controlled offline harness; real stack NOT touched)

- **OFF (default):** `Settings().v4_goal_coverage_guard_enabled == False` (verified); wiring is `if getattr(settings, "v4_goal_coverage_guard_enabled", False):` → guard not invoked; API path byte-equivalent to pre-owner for all statuses (COMPLETED / NEEDS_CLARIFICATION / FAILED / PARTIAL) — no other behavior change in the +6-line diff.
- **ON (injected chain simulation, exact production ordering — source-verified: period guard `:547` → coverage guard → `_remember_completed_session_context` → `_remember_clarification`):**
  - M2 lookup-only COMPLETED → **typed NEEDS_CLARIFICATION**: `answer=None`, `evidence=[]`, `data.results` popped, `options=[]`, `question` = typed "Запрос выполнен не полностью. Не удалось подтвердить: task_hierarchy: DMS-267…", `warnings += ["v4_goal_coverage_incomplete"]`, `data._agent_core_v4.goal_coverage = {requested: 2, proven: [g2], unproven: [g1]}`.
  - **`clarification_id` produced** by `_remember_clarification` (uuid4) after the guard; **pending state stored** with the **original user query** preserved (continuation seam intact); `_remember_completed_session_context` correctly skips the converted NC (no session-context pollution).
  - Fully covered M2 (lookup+hierarchy) → stays **COMPLETED** (no false positive).
  - Status pass-through unchanged: FAILED / NEEDS_CLARIFICATION / PARTIAL remain as-is.
  - Existing clarification flow and provider/source error taxonomy untouched (diff scope).

## P4 — Architecture gap audit (residual OPEN items)

1. **Detector = bounded Russian lexical pilot, not universal parsing.** Kinds implemented: `person_tasks` («задач[и|у|а|ам|ами] <Person> в <SPACE>»), `task_lookup` (verb + «задач[уа]» within 20 chars before a `KEY-N`), `task_hierarchy` (иерархи-/родитель-lemma within 35/22 chars or anaphora with exactly one key), `task_relations` (связанн…задач within 40/30 chars or anaphoric one-key, incl. «с ней/ним»). Conjunction «и» is used only as a separator, never as a splitter — compliant.
2. **OPEN — comparisons:** any «сравн…» query → `detect_goals` returns `()` → the guard is structurally inert. Safe (no fabricated coverage) but comparison goals (M5s class) are **not verified**; typed comparison extractor deferred.
3. **OPEN — single-goal coverage:** the guard fires only at ≥2 goals. A single-goal query where the planner executes the wrong capability (e.g., «Покажи иерархию DMS-267» → `task.lookup`) is NOT flagged. Out of stage-1 scope by design; needs a per-goal contract (A229M1 design) or skill-native completion.
4. **OPEN — person identity:** lexical stem match cannot accept canonical logins (`Kalachanov.V.V`) or full-name forms; login binding via the trajectory's `member.resolve` observation is required before broad enablement (F1 class item 3).
5. **OPEN — languages/morphology:** English and non-inflected variants unhandled (P2 false negatives); unknown-language multi-goal must never be reinterpreted as certified success — currently inert, which is safe.
6. **Guard can block unsafe success; it cannot execute unexecuted goals** — stage-1 boundary confirmed (no execution path exists in the module; A229M2.2 owns continuation).
7. **Risk of deterministic lexical extraction:** brittleness to word order/ellipsis (P2 list), homographs, and case sensitivity (person must be capitalized, space uppercase). Recommended before enabling broadly: (a) identity binding through governed resolver observations, (b) a typed LLM-free extractor over the planner's own trajectory (structured `load_skill`/`call` rationales already carry entity mentions) or a source-governed extractor, (c) a corpus of ≥50 production queries as the non-regression floor.

## Final return

- **Verdict:** `AGENT_CORE_V4_GOAL_COVERAGE_STAGE1_RED_A229M21` — STOP at P0 (0-failures requirement violated by the owner's new suite).
- **TESTED_HEAD:** `846e571cef683ff9c0db5ebccc1bd9bf0d5b7ef2`
- **REPORT_COMMIT:** (see git log after push)
- **Exact suite counts:** goal_coverage 2F/7P; browser_api_contract + created_period + synthesis_elision 35P; config (frontend/team) 46P; V4 full blast 2F/277P (same 2); task-api SWTR 27P; frontend build exit 0.
- **Coverage / false-positive / false-negative table:** P1 (10 replays: 5 single-terminal all correctly flagged incl. DMS-267 false-claim block; M2 two-terminal COMPLETED ✓; **M1 two-terminal FALSE POSITIVE ×2** = F1; freshness + key isolation ✓), P2 (6/6 single-goal controls 0 FP; 4 documented false negatives), P3 (OFF default + ON chain semantics all correct).
- **Core hashes (6/6 byte-identical to `6fb335d`):** 52100ca1 / 3bdb4d09 / 1f7562dc / cf75a6d6 / d82929d1 / 1cc10e12.
- **Residual OPEN gaps:** comparisons, single-goal coverage, login-identity binding, non-Russian/elliptical syntax, typed extractor before broad enablement (P4 list).
- **No checkpoint created. No flag flipped. No code modified. No next code task before owner fix review.**

---

## Re-verification — 2026-10-15 (second gate run)

Re-requested gate run. **Owner fix NOT landed**: `git diff 846e571..HEAD` over all code paths (`po-agent-platform-v2/src`, `po-agent-platform-v2/tests`, `task-api`, `mcp-swtr`, `frontend`) is empty — the only delta since the original RED test is this report file (commit `113e729`). HEAD = origin = `113e729`.

Re-run results (identical to the original run):

| Check | Result |
|---|---|
| Core 6/6 vs `6fb335d` | byte-identical — hashes 52100ca1 / 3bdb4d09 / 1f7562dc / cf75a6d6 / d82929d1 / 1cc10e12 (unchanged) |
| `tests/test_v4_goal_coverage.py` | **2 failed / 7 passed** — same two tests, same assertions |
| Focused suites (browser_api_contract + created_period + synthesis_elision + frontend/team config) | 81 passed |
| Full V4 blast `test_agent_core_v4*.py` + `test_v4*.py` | **2 failed / 277 passed** — same two failures, 0 new regressions |
| `goal_coverage.py:128` | still `person_value.casefold().startswith(goal.person.casefold())` — F1 direction bug unchanged |

**Verdict unchanged:** `AGENT_CORE_V4_GOAL_COVERAGE_STAGE1_RED_A229M21` — first failing boundary is still P0 step 3, `tests/test_v4_goal_coverage.py::test_one_terminal_cannot_prove_other_persons_collection` (F1, production matcher direction). Gate cannot pass until the owner fix (bidirectional stem prefix + member.resolve login identity binding + test-id correction) lands. No additional diagnostics re-run (code byte-identical; P1–P4 findings of the original run stand).
