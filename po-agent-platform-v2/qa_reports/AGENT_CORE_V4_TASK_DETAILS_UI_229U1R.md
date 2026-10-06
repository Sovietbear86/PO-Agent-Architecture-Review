# A229U1R — Task details drawer UI re-gate (ES2020 build fix)

**Verdict:** `AGENT_CORE_V4_TASK_DETAILS_UI_GREEN_A229U1R`

**Classification:** `GREEN_FIXED_ES2020_SPLIT_JOIN_BUILD_CERTIFIED`

**START_HEAD:** `6f5883f`
**Previous RED:** `f95ab8c` (A229U1 — `RED_P0_FRONTEND_TSC_BUILD_REGRESSION`)
**Previous GREEN checkpoint:** `aa78e52` (A229F2R3)
**Date:** 2026-10-06

---

## Summary

| Phase | Result |
|-------|--------|
| P0.1 worktree / P0.2 delta isolation | ✅ GREEN |
| P0.3 frontend TypeScript/build | ✅ GREEN (A229U1 RED closed) |
| P0.4 frontend tests | ✅ N/A (no frontend unit tests; Playwright e2e only) |
| P0.5 V4 blast-radius | ✅ GREEN (242/242) |
| P1 source-backed description | ✅ GREEN (282/282 byte-exact vs raw source) |
| P2 readable intelligence tabs | ✅ GREEN (4/4 tabs; F2 note) |
| P3 loading/stale-data guard | ✅ GREEN (8/8 transitions, 0 stale reuses) |
| P4 request cardinality | ✅ GREEN (1:1 request-per-trigger, no polling) |
| P5 retained Tasks UX | ✅ GREEN (F1 pre-existing × occlusion note) |
| Audit | ✅ 0 local reads, 0 mutations, 0 unscoped scans |

The owner's one-line ES2020 fix (`key.replaceAll('_',' ')` → `key.split('_').join(' ')`, `Pages.tsx:143`) is behaviorally equivalent, restores the build, and the full drawer feature (source-backed description, intelligence tabs, loading/stale guard, request discipline, retained Tasks UX) is certified GREEN on live REAL AS21. Two non-blocking findings (F1 pre-existing × occlusion, F2 source-JSON values in structured rows) and one pre-existing LLM note (F3 phrase non-determinism) are documented.

**Recommendation (per spec):** freeze checkpoint `checkpoint/v4-task-details-ui-green-a229u1r`; owner may sync the UI-only delta to the public/community repo; resume A229R1 latency verification on the new certified HEAD.

---

## P0 — Integrity/build (GREEN)

### P0.1 Worktree
Clean; only `GIGACODE.md` modified (QA memory file, not production code). Untracked: prior QA e2e specs + QA scripts (never committed).

### P0.2 Delta isolation
`git diff 1b26cae..6f5883f --stat` (A229U1 RED → A229U1R):

```
GIGACODE_NEXT_ACTION.md            (assignment text)
PO_AGENT_HARNESS_EVOLUTION_PLAN.md (docs: A229U1 RED closure)
V4_DOD_LOCK.md                     (lock entries)
po-agent-platform-v2/frontend/src/recovery/Pages.tsx   1 line
```

The **only production code change**:

```diff
-  return labels[key] ?? key.replaceAll('_', ' ')
+  return labels[key] ?? key.split('_').join(' ')
```

Behaviorally identical for the observed key alphabet (no leading/trailing/double underscores in intelligence keys). 0 Agent Core/planner/plugin/Task API files touched. Full delta vs `aa78e52` = the A229U1 drawer feature (+184 Pages.tsx, +83 workspace.css) + the one-line fix + docs.

### P0.3 Build
- `npm run build` (`tsc && vite build`) — **exit 0** (A229U1: exit 2, TS2550 on `replaceAll` vs ES2020 lib)
- `npx tsc --noEmit` — **0 errors**
- tsconfig target/lib unchanged (still ES2020)

### P0.5 V4 blast-radius
Full V4 suite: **242/242 pass** — identical to the A229F2R3/A229U1 baseline. No backend regression.

---

## P1 — Source-backed description (GREEN)

Task: **DMS-330** (real AS21, non-empty description). Oracle captured two ways before the browser run: agent `Покажи задачу DMS-330` COMPLETED 282-char description AND raw Task API `GET :8241/api/v1/swtr-read/tasks/DMS-330` → `unit.description` 282 chars (identical). Saved to `/private/tmp/qa229u1r/oracle_dms330.json`.

Browser (Playwright, live vite → agent 8004 @ `6f5883f` → task-api 8241 → MCP-SWTR 3000):

| Check | Result |
|-------|--------|
| Opening the task issues exactly one exact source-backed lookup | ✅ 1× `Покажи задачу DMS-330` (whole session) |
| `Загружаю описание из AS21…` visible while pending | ✅ observed (sampling loop, `loading_text_seen=true`) |
| Final description equals authoritative exact task read | ✅ **282/282 byte-exact** (`description_matches_source=true`) |
| `Описание отсутствует` only when truly absent | ✅ not shown (task has a description) |
| Tab switches do not re-run the exact lookup | ✅ exact lookup count stayed 1 across 8+ switches |
| Frontend never calls AS21/MCP directly | ✅ 0 direct requests (network audit, `suspicious_urls=[]`) |

---

## P2 — Readable intelligence tabs (GREEN)

All four tabs rendered from live REAL AS21 via the drawer:

| Tab | Skill (live) | Rendering |
|-----|--------------|-----------|
| Резюме | `task.summary@4.0.0-poc` | Rich answer: paragraph + readable bullet list + open-question block; structured key/value table (Задача/goal/what to do/source title) — **no raw `**`, no `_agent_core_v4`/trajectory/source_data visible** |
| Качество | `task.quality@4.0.0-poc` | "Оценка DMS-330: 85/100 (good…)" + structured rows — correct tab-specific content |
| Что не хватает | `task.missing_requirements@4.0.0-poc` | Readable text + recommendation box; 1 table, 3 lists |
| История | `task.history@4.0.0-poc` | 2 tables (transition table + raw timeline table) with # / Переход / Дата / Автор — readable, scrollable |

- Record arrays → tables ✅ (history transitions; quality/summary structured rows)
- Scalar arrays → lists ✅ (summary "Что нужно сделать" bullets; open questions)
- Long output scrollable, no drawer overflow ✅ (`boxH == clientH` on every tab; `drawerOverflowX=false`)
- **F2 (non-blocking):** the `goal` / `what to do` structured rows display the source's **ProseMirror JSON string** verbatim (AS21 stores the description in rich-text JSON). The UI correctly renders the structured contract (value-as-text); the readability gap is a **skill-side** data-formatting issue (the rich-answer section already shows the extracted plain text). Not a drawer rendering defect.

Note: the P2 "Качество" cell in the first raw run was sampled inside a sub-second pre-effect frame (stale-look); the definitive P3 re-run proves every tab settles with its own skill content (`settled_head` shows `task.quality@4.0.0-poc` for all three Качество transitions).

---

## P3 — Loading/stale-data guard (GREEN)

Definitive dataset: `qa_229u1r_p3full.mjs` — 8 transitions with **250 ms sampling** from click time, plus failure + recovery:

| # | From → To | Old content at t=0 | Loader first seen | Old visible during loading | Settled at | New requests |
|---|-----------|--------------------|-------------------|---------------------------|------------|--------------|
| 1 | Резюме→Качество | 1 frame (pre-effect) | **252 ms** | **no** | 33.5 s | 1 |
| 2 | Качество→Что не хватает | 1 frame | **252 ms** | **no** | 23.7 s | 1 |
| 3 | Что не хватает→История | 1 frame | **252 ms** | **no** | 59.4 s | 1 |
| 4 | История→Резюме | 1 frame | **252 ms** | **no** | 49.8 s | 1 |
| 5 | Резюме→Качество | 1 frame | **252 ms** | **no** | 36.0 s | 1 |
| 6 | Качество→Резюме | 1 frame | **252 ms** | **no** | 17.6 s | 1 |
| 7 | Резюме→История | 1 frame | **252 ms** | **no** | 18.9 s | 1 |
| 8 | История→Качество | 1 frame | **252 ms** | **no** | 20.4 s | 1 |

- Active tab switches immediately ✅ (`active_immediate` correct 8/8)
- Previous tab result disappears before the loader appears ✅ (the only old-content visibility is the single pre-effect render frame at t≈0, before `useEffect` clears the result — never after loading starts)
- Spinner + `aria-busy="true"` + `Обновляю данные…` visible for the whole pending window ✅
- Success replaces loader with new (tab-specific) content ✅ (verified by `task.<skill>@version` header per settled tab)
- **Failure** (aborted request via route interception): explicit error `Не удалось обновить данные для этой вкладки.` at **154 ms**, **no stale content reused** ✅
- **Recovery**: after unblocking, Резюме and История both load normally ✅

The first raw run (p1234) observed the loader on 5/8 transitions; the 3 unobserved ones were re-proven on the deterministic 8/8 run above (same tab pairs, loader at 252 ms each time) — no app defect, first-run sampling artifact.

---

## P4 — Request cardinality (GREEN)

Full session network capture (17 POSTs, all to `/api/v1/query` only):

| Trigger | Requests |
|---------|----------|
| Page search | 1 (`Покажи задачи по документации в DMS`) |
| First task open | exactly **1 exact lookup** + **1 Summary** intelligence |
| P2 initial tabs | 3 (quality, missing, history — one each) |
| P3 transitions | 8 (one per click) |
| Failure step | 1 (aborted) |
| Recovery | 2 |

- No duplicate POST from effects/renders ✅ (no React StrictMode; 1:1 trigger↔request mapping)
- Exact task lookup **not repeated** on tab switches ✅ (single occurrence for the whole session)
- No polling ✅ (0 new requests during a 10 s idle window with the drawer open)
- No direct frontend AS21/MCP traffic ✅

---

## P5 — Retained Tasks UX (GREEN)

| Check | Result |
|-------|--------|
| NL search still works | ✅ 14 cards for the documentation query (DMS-330 present; see F3 for a one-off phrase drift) |
| Task cards open | ✅ DMS-330 card → drawer opens |
| Local task CRUD unaffected | ✅ create `LOCAL-0001` → localStorage persisted → status change (IN_PROGRESS) → edit → delete, all verified in `po-local-tasks` |
| Local form buttons real-pointer clickable | ✅ settled-state probe: submit (1322,834) and cancel (1229,834) hit-test to themselves; real clicks create/cancel |
| Drawer closes correctly | ✅ scrim click (real pointer, hit-test = `drawer-scrim`) closes; × handler works — but see **F1** (× is hit-blocked by the sticky topbar) |
| Agent launcher hidden while drawer open | ✅ `display:none` via `body.task-drawer-active`; visible again after close |
| Dark/glass design consistent/responsive | ✅ body `rgb(2,10,19)`; no horizontal overflow at 1440×900 and 1366×768 |

### F1 (non-blocking, pre-existing — A226R2 F1 lineage)
The task-details drawer's **× close button** (top-right, y≈14–55 px) is **hit-blocked by the sticky topbar**: `document.elementFromPoint` at the × center returns `HEADER.topbar`; Playwright real-pointer click is refused (`<header class="topbar"> intercepts pointer events`). Root cause: `.page{isolation:isolate}` (A226 dark-glass CSS) traps the drawer's `z-index:55` inside `.page`'s stacking context, so the topbar (`z-index:5` at root level) paints/hit-tests above the drawer's top 64 px band. The drawer still closes via the scrim (verified) and the × handler is functional (JS-verified close + launcher restore). Owner fix options: render the drawer in a body-level portal, drop `isolation:isolate` on `.page`, or lower the topbar z-index below the drawer band.

### F3 (non-blocking, pre-existing LLM class)
One live run of the same NL search query returned a 4-task phrase subset without DMS-330 (phrase-extraction non-determinism, A179 lineage); the P5 harness was made card-adaptive (P5 exercises card/drawer mechanics, and P1 already pinned DMS-330). Not an A229U1R delta.

---

## Audit (session-wide, agent log @ `6f5883f`)

- Local `/api/v1/tasks` store reads: **0**
- Mutations / writes: **0**
- Unscoped tenant scans: **0** (all task queries space-scoped by skills)
- `swtr-read` route calls: 83 (bounded: task point reads, /files, sprint routes)
- Frontend traffic: `/api/v1/query` + `/health` only (vite proxy → 8004)
- Services: agent 127.0.0.1:8004 (PID 8990 @ `6f5883f`, log `/private/tmp/qa229u1r_agent.log`), task-api 127.0.0.1:8241 (PID 88845), MCP-SWTR 127.0.0.1:3000 (PID 88405), vite 127.0.0.1:5175 (PID 89616)

## QA artifacts (untracked, not committed)

`qa_229u1r_p1234.mjs`, `qa_229u1r_p3probe.mjs`, `qa_229u1r_p3full.mjs`, `qa_229u1r_p5.mjs`/`p5b`/`p5c`/`p5d.mjs`; findings + screenshots in `/private/tmp/qa229u1r/` (`p1234_findings.json`, `p3probe.json`, `p3full.json`, `p5c_findings.json`, `p5d_findings.json`, `oracle_dms330.json`, PNGs).

## Services left running

agent 8004 (PID 8990 @ `6f5883f`), task-api 8241 (PID 88845, system python3), MCP-SWTR 3000 (PID 88405), vite 5175 (PID 89616).
