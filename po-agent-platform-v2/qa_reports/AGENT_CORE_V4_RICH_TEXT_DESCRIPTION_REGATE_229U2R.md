# A229U2R — hardened production rich-text re-gate

**Verdict:** `AGENT_CORE_V4_RICH_TEXT_DESCRIPTION_GREEN_A229U2R`

**Classification:** `GREEN_FIXED_HARDENED_POINT_READ_NORMALIZED_PROVEN`

**START_HEAD:** `491fc34`
**Previous RED:** `2894e6a` (A229U2 report; code HEAD `9f9145d`)
**Date:** 2026-10-06

---

## Summary

| Phase | Result |
|-------|--------|
| P0 integrity / delta / tests / build | ✅ GREEN (0 new failures vs baseline; 244 V4-focused; build exit 0) |
| P1 blocking production point-read (3× live DMS-333) | ✅ GREEN (3/3 stable, readable, link preserved, raw provenance kept) |
| P2 drawer rendering | ✅ GREEN (readable, no structural keys, loading retained, 1 exact lookup) |
| P3 Task Intelligence propagation | ✅ GREEN (summary/quality/missing all normalized, quality proves 65-char normalized desc) |
| P4 normalization controls (5 shapes) | ✅ GREEN (all 8 sub-checks pass) |
| P5 architecture/source audit | ✅ GREEN (deterministic, adapter-only, 0 core delta, 0 special-casing) |

The owner's hardened-mapper fix (reusing `_rich_text_to_plain` in `HardenedProductionTaskApiAS21Adapter._map_raw_unit` + preserving the raw `description` in `source_data["description"]`) is **certified live and at unit level**. The A229U2 blocking defect (production point-read leaking raw rich-text JSON) is **CLOSED**: 3/3 live `Покажи задачу DMS-333` return the clean readable link, raw source is preserved for audit, and the normalized text propagates into Task Intelligence. All five normalization controls (plain / rich-object / serialized-JSON / malformed / long) behave as specified, and the change is deterministic adapter-only with zero Core/planner/plugin/frontend delta.

**Recommendation (per spec):** freeze checkpoint `checkpoint/v4-task-details-richtext-green-a229u2r`; owner may sync the certified A229U1+A229U2 UI/adapter delta to the public/community repo; resume A229R1 latency verification on the new certified HEAD.

---

## P0 — Integrity/tests (GREEN)

### P0.2 Delta isolation
`git diff --name-only 2894e6a..491fc34`:

```
GIGACODE_NEXT_ACTION.md
PO_AGENT_HARNESS_EVOLUTION_PLAN.md
V4_DOD_LOCK.md
po-agent-platform-v2/src/po_agent/adapters/hardened_production_task_api.py
po-agent-platform-v2/tests/test_hardened_production_task_rich_text.py
```

Exactly the permitted set. **0** Agent Core / planner / plugin / frontend files touched (path-scoped `git diff --name-only` → 0). The production change is confined to the AS21 adapter boundary:

```diff
+    raw_description = unit.get("description")
     source_data = { ..., "sprint_id": sprint_id,
+        "description": raw_description,
     }
-        ... description=unit.get("description") if isinstance(unit.get("description"), str) else None ...
+        ... description=_rich_text_to_plain(raw_description) ...
```

The fix reuses the existing `_rich_text_to_plain` helper (imported, not re-implemented) and adds the raw value to `source_data` for provenance.

### P0.4 Tests/build
- Focused `tests/test_hardened_production_task_rich_text.py` + `tests/test_task_api_as21_adapter.py`: **20/20 pass**.
  - The new regression drives the **actual production class** `HardenedProductionTaskApiAS21Adapter._map_raw_unit` (the exact path A229U2 proved was bypassing the base fix) with a real DMS-333-shaped serialized unit — asserting canonical = `"wiki-страница (https://example.invalid/wiki/123)"`, `source_data["description"] == raw`, no `textAlign`/`"type":"doc"`, and plain-text passthrough. This closes the A229U2 test-masking gap.
- V4-focused blast-radius (`-k "v4 or agent_core_v4 or skill_native or plugin or task_created_period or task_search or sprint_discovery or planner_signature"`): **244 passed** (1 env-dependent live-service error, not V4) — matches the A229U1R/A229U2 244 baseline.
- Full suite on `491fc34`: **23F / 1541P / 12S / 11E**. Failure-set diff vs A229U2 baseline (`9f9145d`, 23F/1539P/11E): **0 new failures** — identical 35-entry FAILED/ERROR set (all pre-existing env/live-integration: real-LLM endpoint, live SWTR integration, health endpoint, repo hygiene). +2 passes = the 2 new hardened rich-text tests.
- Frontend `npm run build`: **exit 0**.

---

## P1 — Blocking production point-read (GREEN)

### Raw observation (independent, before any Agent query)
`GET :8241/api/v1/swtr-read/tasks/DMS-333` → `unit.description` is a **416-char serialized JSON rich-text document** (`str`): `{"type":"doc","content":[{"type":"paragraph","attrs":{...},"content":[{"type":"text","marks":[{"type":"link","attrs":{"href":"https://sberworks.ru/wiki/pages/viewpage.action?pageId=1247641989",...}}],"text":"https://sberworks.ru/wiki/..."}]}]}`. Link mark with `text == href` (the URL is both label and target). Saved to `/private/tmp/qa229u2r/dms333_raw.json`.

### Live `Покажи задачу DMS-333` — 3/3 stable (agent freshly restarted on `491fc34`)

| Run | status | canonical `task.description` | readable | raw leak | link preserved |
|-----|--------|------------------------------|----------|----------|----------------|
| 1 | COMPLETED | `https://sberworks.ru/wiki/pages/viewpage.action?pageId=1247641989` | ✅ | none | ✅ |
| 2 | COMPLETED | same | ✅ | none | ✅ |
| 3 | COMPLETED | same | ✅ | none | ✅ |

No visible serialized JSON/doc tree, no `textAlign`/`attrs`/`marks`/`content` structural keys, no fabrication — the output is exactly the source's human-visible text (the link URL).

### Provenance (unit level, real raw unit)
- `Task.description` = clean URL; `Task.source_data["description"]` = **byte-equal to the raw 416-char doc tree** (intact `{"type":"doc"...`). Raw source preserved for audit. ✅
- Canonical contains **no** structural keys. ✅

> **QA environment note (transparent):** the first 3 live runs of this gate were served by a **stale agent process** (PID 86717, still on `9f9145d`) that survived an earlier restart — they leaked raw JSON. This was a QA process-management artifact, not a code defect. After a clean kill of the stale listener and a verified fresh start on `491fc34` (PID 12263, port confirmed), all 3 runs are clean and deterministic.

---

## P2 — Drawer rendering (GREEN)

Opened DMS-333 from Tasks UI (via probe-verified collection query `Покажи задачи по ABAC в DMS` → card grid incl. DMS-333 → card click → drawer):

| Check | Result |
|-------|--------|
| Upper `Описание` block shows readable source text | ✅ `https://sberworks.ru/wiki/pages/viewpage.action?pageId=1247641989` |
| No `type/doc/content/attrs/marks/textAlign` keys visible | ✅ none present |
| Source link meaning visible | ✅ full wiki URL rendered |
| A229U1R loading indicator retained | ✅ `Загружаю описание из AS21…` observed while pending |
| Exact task lookup cardinality = one per drawer open | ✅ exactly 1 `Покажи задачу DMS-333` POST |

Frontend issued **no** direct AS21/MCP requests (all via `/api/v1/query` proxy).

---

## P3 — Task Intelligence propagation (GREEN)

For DMS-333, all three tabs settled on their own skill with **no raw rich-text JSON** and **no `_agent_core_v4`/`source_data`** internal leak:

| Tab | Skill (live) | Raw rich-text | Link/content represented | Note |
|-----|--------------|---------------|--------------------------|------|
| Резюме | `task.summary@4.0.0-poc` | none | ✅ `goal` field = normalized URL; answer: "DMS-333: [doc] ABAC с Apache Ranger описание. По доступным данным требуется: https://sberworks.ru/wiki/..." | based on normalized description |
| Качество | `task.quality@4.0.0-poc` | none | ✅ (see note) | "Оценка DMS-333 ... Итог: 75/100 (fair)"; **"Описание есть (65 символов)"** |
| Что не хватает | `task.missing_requirements@4.0.0-poc` | none | ✅ readable | "В задаче DMS-333 не хватает двух элементов: 1. Цель/контекст 2. Критерии приёмки" |

**Decisive propagation proof:** the quality tab reports the description as **65 characters** — exactly the normalized URL length (65), **not** the raw 416-char JSON. This confirms the intelligence skills receive the **normalized** `Task.description`, not the raw rich-text object. (The first browser pass momentarily captured the quality tab in its single pre-effect frame — the A229U1R-documented one-frame window where the previous tab is still shown before the effect clears; a targeted re-probe waiting for the `task.quality` skill header confirms the settled content above.)

---

## P4 — Normalization controls (GREEN)

Driven through the **hardened production mapper** (`HardenedProductionTaskApiAS21Adapter._map_raw_unit`), all pass:

| # | Shape | Requirement | Result |
|---|-------|-------------|--------|
| 1 | plain text | byte/content semantics retained | ✅ exact, raw preserved |
| 2 | rich-text object | normalize to human-readable | ✅ `Первый абзац.\nСсылка: вики (https://wiki.example/1)\nстрока A\nстрока B` (paragraphs separated, link as `label (url)`, hardBreak→newline) |
| 3 | serialized rich-text JSON string | normalize equivalently to object | ✅ byte-identical to object-form output |
| 4 | malformed JSON-looking plain text | fail soft, preserved as text | ✅ returned verbatim (not dropped) |
| 5 | long description (3599 chars) | untruncated | ✅ full 3599 chars preserved |
| 6 | unknown structural node | never stringify full raw object | ✅ `widgetXyz`/`mysteryNode` absent; visible `text` kept |
| 7 | paragraph separation | paragraphs remain separated | ✅ `P1\nP2` |
| 8 | empty / None description | normal absent path | ✅ `None` (UI renders `Описание отсутствует`) |

Raw source preserved in `source_data["description"]` for **all** shapes (str stays str, dict stays dict).

---

## P5 — Architecture/source audit (GREEN)

- **Deterministic adapter-only normalization:** `_rich_text_to_plain` is pure recursive parsing (no I/O, no LLM, no randomness). ✅
- **No LLM used to parse description:** the normalization function contains no LLM/HTTP/planner references. ✅
- **0 Core/planner/plugin/frontend delta:** path-scoped diff = 0 (P0.2). ✅
- **No product/task-specific special case:** `grep -c "DMS|WMB|STS|OLP|sberworks"` in `task_api.py` = **0** — the normalizer is generic over any ProseMirror-like doc tree. ✅
- **Raw source provenance preserved:** `source_data["description"]` carries the untouched raw payload (proven live + unit). ✅
- **No mutation / local fallback / tenant scan introduced:** agent log shows **0** local `/api/v1/tasks` reads, **0** mutations (PUT/DELETE/PATCH), **0** unscoped `task-query` tenant scans across the whole session. ✅

---

## Evidence files

- `/private/tmp/qa229u2r/dms333_raw.json` — raw task-api payload (416-char doc tree)
- `/private/tmp/qa229u2r/p1b_lookup_0..2.json`, `p1b_results.json` — 3× live lookup (clean)
- `/private/tmp/qa229u2r/p1_lookup_0..2.json` — 3× stale-process leak (QA artifact, documented)
- `/private/tmp/qa229u2r/p23_findings.json`, `p23_dms333_drawer.png`, `p23_tab_*.png` — P2/P3 browser
- `/private/tmp/qa229u2r/p3q_findings.json`, `p3q_quality.png` — quality-tab settled re-probe
- `qa_229u2r_p4_controls.py` — P4 control harness (repo root, untracked)
- `/private/tmp/qa229u2r_v4blast.out` (full suite, `491fc34`), `/private/tmp/qa229u2_v4blast.out` (A229U2 baseline used for the 0-new-failure diff), `/private/tmp/qa229u2r_v4focused.out` (244 V4-focused)
- `/private/tmp/qa229u2r_agent.log` — agent log on `491fc34`

## Services

agent 127.0.0.1:8004 (PID 12263 @ `491fc34`), task-api 127.0.0.1:8241, MCP-SWTR 127.0.0.1:3000, vite 127.0.0.1:5175.
