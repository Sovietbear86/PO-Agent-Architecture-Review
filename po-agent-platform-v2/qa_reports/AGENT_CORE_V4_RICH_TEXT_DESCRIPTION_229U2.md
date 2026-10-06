# A229U2 — AS21 rich-text description normalization re-gate

**Verdict:** `AGENT_CORE_V4_RICH_TEXT_DESCRIPTION_RED_A229U2`

**Classification:** `RED_P1_PRODUCTION_POINT_READ_MAPPER_NOT_NORMALIZED`

**START_HEAD:** `9f9145d`
**Previous GREEN checkpoint:** `73645ce` (A229U1R report; code HEAD `6f5883f`)
**Date:** 2026-10-06
**STOP at:** P1 — first failing boundary (canonical exact task lookup still returns raw rich-text JSON)

---

## Summary

| Phase | Result |
|-------|--------|
| P0 integrity / delta / tests / build | ✅ GREEN (V4 blast: see below) |
| **P1 REAL AS21 description normalization** | ❌ **RED — production point-read mapper bypasses the fix** |
| P2 task drawer | ⏸️ SKIPPED (first-RED STOP) |
| P3 Task Intelligence propagation | ⏸️ SKIPPED (first-RED STOP) |
| P4 normalization controls | ⏸️ SKIPPED (first-RED STOP) |
| P5 architecture/source audit | ⏸️ SKIPPED (first-RED STOP; partial in P0) |

The owner's normalization **function is correct** — on the real DMS-333 raw payload it produces the clean, readable link text. But the fix was applied only to `TaskApiAS21Adapter._map` (`task_api.py:564`), while the **production exact-task-read path** used by `task.lookup` goes through `HardenedProductionTaskApiAS21Adapter._map_raw_unit` (`hardened_production_task_api.py:154 → 161 → 214`), which still maps `description=unit.get("description")` **without normalization**. Live, "Покажи задачу DMS-333" COMPLETED and returned the raw 416-char `{"type":"doc",...}` JSON as the canonical description. Secondary: the hardened mapper also does **not preserve the raw description in `Task.source_data`**, so the provenance requirement fails on the production path as well. The owner's new tests mask the gap by driving `TaskApiAS21Adapter.search_tasks` directly (same test-masking class as A222R).

---

## P0 — Integrity/build/tests (GREEN)

### P0.2 Delta isolation
`git diff --stat 73645ce..9f9145d`:

```
GIGACODE_NEXT_ACTION.md                            (assignment)
PO_AGENT_HARNESS_EVOLUTION_PLAN.md                 (docs)
V4_DOD_LOCK.md                                     (docs)
po-agent-platform-v2/src/po_agent/adapters/task_api.py   (+98)
po-agent-platform-v2/tests/test_task_api_as21_adapter.py (+72)
```

Exactly the permitted set. **0** Agent Core / planner / plugin / frontend files touched (verified by path-scoped `git diff --name-only` → 0).

### P0.4 Tests/build
- Focused `tests/test_task_api_as21_adapter.py`: **18/18 pass** (16 retained + 2 new rich-text tests)
- Frontend `npm run build`: **exit 0**
- V4-focused blast (v4/agent_core_v4/skill_native/plugin/search/discovery/parity selection): **244 passed** (1 env-dependent live-service error in `test_integration_real_services`, not V4)
- Full-suite regression vs parent: new HEAD `9f9145d` = **23F / 1539P / 12S / 11E**; baseline `73645ce` (read-only worktree, removed after) = **24F / 1536P / 12S / 11E**. Failure-set diff: **0 new failures caused by the delta** (one baseline flake `test_as21_diagnostics_reports_runtime_wiring_without_secrets` passes on the new HEAD). All 34 shared failures are pre-existing environment/live-integration issues (real-LLM endpoint, live SWTR integration, health endpoint, repo hygiene) — identical in both runs.

### Owner's tests (reviewed)
Both new tests are correct *for the class they test*:
1. `test_as21_rich_text_description_is_normalized_to_readable_text` — dict-form rich text through `TaskApiAS21Adapter.search_tasks` → `"Подготовить описание ABAC с Apache Ranger.\nДокументация: wiki-страница (https://example.invalid/wiki/123)"` — link preserved as `text (url)`.
2. `test_as21_serialized_rich_text_description_is_normalized_without_destroying_plain_text` — serialized string → `"Первая строка\nВторая строка"`; plain text unchanged.

**Masking:** both construct `TaskApiAS21Adapter` with a `MockTransport` handler — the production `HardenedProductionTaskApiAS21Adapter.get_task` point-read (the path `task.lookup` actually uses) is never exercised. No non-mocked regression drives the hardened mapper with a rich-text payload.

---

## P1 — REAL AS21 description normalization (RED)

### Raw observation (independent, pre-browser)
`GET :8241/api/v1/swtr-read/tasks/DMS-333` → `unit.description` is a **serialized JSON rich-text document** (416 chars, `str`):

```
{"type":"doc","content":[{"type":"paragraph","attrs":{"id":"3d269309-...","indent":0,"textAlign":"justify"},
"content":[{"type":"text","marks":[{"type":"link","attrs":{"href":"https://sberworks.ru/wiki/pages/viewpage.action?pageId=1247641989","target":"_blank","rel":"noopener noreferrer nofollow","class":null}}],
"text":"https://sberworks.ru/wiki/pages/viewpage.action?pageId=1247641989"}]}]}
```

Saved to `/private/tmp/qa229u2_dms333_raw.json`. Rich-text structure confirmed: doc → paragraph (attrs) → text with link mark, text == URL.

### Function level — the fix itself works ✅
`_rich_text_to_plain(raw_description)` on the real payload:

```
'https://sberworks.ru/wiki/pages/viewpage.action?pageId=1247641989'
```

Readable, link not lost, no JSON residue.

### Production mapper level — RED ❌
`HardenedProductionTaskApiAS21Adapter._map_raw_unit(real_DMS-333_unit)` → `Task.description` = **the raw 416-char JSON document** (byte-identical to the source payload).

### Live canonical lookup — RED ❌
`POST /api/v1/query` "Покажи задачу DMS-333" on agent @ `9f9145d` (fresh restart):
- status `COMPLETED`, task key `DMS-333`
- `task.description` = **raw rich-text JSON** (leak reproduced live, `/private/tmp/qa229u2_p1_lookup.json`)

### Root cause (causally proven)
Class chain: `HardenedProductionTaskApiAS21Adapter(ProductionTaskApiAS21Adapter(TaskApiAS21Adapter))`.

- Fixed: `TaskApiAS21Adapter._map` (task_api.py:564) — used by collection/task-query row mapping and by the row-based `ProductionTaskApiAS21Adapter.get_task` (production_task_api.py:92, which also preserves `"source_data": unit` — that path is fine).
- **Shadowed in production:** `HardenedProductionTaskApiAS21Adapter.get_task` (hardened_production_task_api.py:154) calls its **own** `_map_raw_unit` (line 178) which builds the Task at line 214 with `description=unit.get("description")` — unnormalized. This is the path the live `task.lookup` uses (A219R-certified single point read with `_raw_unit_cache`).

### Secondary defect (same boundary)
`Task.source_data` from the hardened mapper = `{swtr_code, swtr_space, workflow_status, swtr_attributes, sprint_id}`; `swtr_attributes` has **no `description` attribute** (verified against the real raw unit: 35 attribute codes, none `description`). The raw rich-text description is **dropped entirely** from the production `Task` object → the "raw source preserved for provenance/audit" requirement is unmet on the production path (row-based `ProductionTaskApiAS21Adapter.get_task` does preserve it via `source_data=unit`, but the hardened override shadows it).

### Owner fix (proposed, not implemented)
1. In `HardenedProductionTaskApiAS21Adapter._map_raw_unit` (hardened_production_task_api.py:214), map `description=_rich_text_to_plain(unit.get("description"))` (import/reuse the existing helper; keep the plain-string fast path).
2. Preserve the raw value in `source_data` (e.g., add the raw `description` into `source_data` alongside the existing keys) so audit/provenance holds on the hardened path, mirroring the row-based path's `source_data=unit`.
3. Add a **non-mocked production-path regression**: drive `HardenedProductionTaskApiAS21Adapter` (the class the runtime actually uses) point-read mapping with the real DMS-333-shaped unit (serialized JSON string with link mark) asserting canonical = readable text AND raw preserved in `source_data`. Do not rely on `TaskApiAS21Adapter`-level tests for the point-read contract.
4. Re-gate from P1 (live DMS-333 lookup + drawer + intelligence tabs + P4 controls + P5 audit).

---

## Evidence files

- `/private/tmp/qa229u2_dms333_raw.json` — raw task-api payload
- `/private/tmp/qa229u2_p1_lookup.json` — live agent lookup response (leak)
- `/private/tmp/qa229u2_agent.log` — agent log on `9f9145d`
- `/private/tmp/qa229u2_v4blast.out` — full-suite result (new HEAD)
- `/private/tmp/qa229u2_v4blast_736.out` — full-suite result (baseline 73645ce worktree)
- `/private/tmp/qa229u2_v4focused.out` — V4-focused blast (new HEAD)

## Re-verification (post-report, same code HEAD `9f9145d`; no owner fix committed)

Independent second run on the live stack:
- `Покажи задачу DMS-333` → `COMPLETED`, `task.description` = raw rich-text JSON again (`/private/tmp/qa229u2_p1_rerun.json`) — leak deterministic, not a one-off.
- Unit-level: `_rich_text_to_plain(raw)` = clean URL; `HardenedProductionTaskApiAS21Adapter._map_raw_unit(real_unit).description == raw` (byte-equal, unnormalized); hardened `source_data` has no description attribute.

Verdict unchanged: `AGENT_CORE_V4_RICH_TEXT_DESCRIPTION_RED_A229U2`, first failing boundary P1. Owner fix (section above) still required before re-gate.

## Services

agent 127.0.0.1:8004 (PID 86716 @ `9f9145d`), task-api 127.0.0.1:8241 (PID 88845, reused), MCP-SWTR 127.0.0.1:3000 (PID 88405, reused), vite 127.0.0.1:5175 (PID 89616, reused; frontend unchanged).
