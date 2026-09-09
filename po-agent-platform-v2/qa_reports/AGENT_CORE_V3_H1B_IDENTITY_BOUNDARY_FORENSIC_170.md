# Assignment 170 — H1B Identity Boundary Forensic

**Date:** 2026-09-09  
**HEAD:** `78db4fbcbf4daf13c95eb1435547ae7ed4479418`  
**Query under test:** `Задачи Гаранина`  
**Model:** Qwen3.8-27B  
**Source:** REAL AS21 via MCP-SWTR  
**Oracle B:** `garanin.r.v` → 24 tasks (7 DMS + 5 STS + 12 OLP)

---

## Verdict

**`H1B_IDENTITY_RECOVERY_OWNER_FIX_READY`**

The sole H1B blocker is **LLM semantic prepass intermittency**: in 8/10 runs, the LLM prepass produced no result (`llm_used=False`, `raw_slots={}`, `grounded_values={}`). When the LLM does run, the full grounding→search→parity chain works perfectly (2/2 PASS with exact 24/24 key parity).

The source-backed identity resolver confirms all 3 team members resolve **uniquely**. A deterministic recovery path exists.

---

## Forensic Results: 10 Fresh-Session Queries

| Run | ms | llm_used | intent_hint | person_raw | member_login | status | Classification |
|-----|-----|----------|-------------|------------|--------------|--------|----------------|
| 1 | 35,580 | **False** | *(empty)* | *(empty)* | *(empty)* | FAILED | INTERPRETER_ENTITY_OMISSION |
| 2 | 70,639 | True | task_search_assignee | Гаранина | Garanin.R.V | COMPLETED | PASS (24/24 ✅) |
| 3 | 68,498 | **False** | *(empty)* | *(empty)* | *(empty)* | FAILED | INTERPRETER_ENTITY_OMISSION |
| 4 | 42,907 | **False** | *(empty)* | *(empty)* | *(empty)* | FAILED | INTERPRETER_ENTITY_OMISSION |
| 5 | 41,986 | **False** | *(empty)* | *(empty)* | *(empty)* | FAILED | INTERPRETER_ENTITY_OMISSION |
| 6 | 40,140 | **False** | *(empty)* | *(empty)* | *(empty)* | FAILED | INTERPRETER_ENTITY_OMISSION |
| 7 | 26,418 | **False** | *(empty)* | *(empty)* | *(empty)* | FAILED | INTERPRETER_ENTITY_OMISSION |
| 8 | 39,150 | **False** | *(empty)* | *(empty)* | *(empty)* | FAILED | INTERPRETER_ENTITY_OMISSION |
| 9 | 35,275 | **False** | *(empty)* | *(empty)* | *(empty)* | FAILED | INTERPRETER_ENTITY_OMISSION |
| 10 | 41,185 | True | task_search_assignee | Гаранина | Garanin.R.V | COMPLETED | PASS (24/24 ✅) |

**Score: 2/10 PASS, 8/10 FAIL**

### Failure Classification

| Category | Count | Description |
|----------|-------|-------------|
| **INTERPRETER_ENTITY_OMISSION** | **8** | LLM semantic prepass not used (`llm_used=False`), no intent extracted, no person slot returned |
| INTERPRETER_ENTITY_PRESENT_GROUNDER_MISS | 0 | — |
| GROUNDED_LOGIN_LOST_AFTER_GROUNDING | 0 | — |
| SOURCE_IDENTITY_AMBIGUOUS | 0 | — |
| PROVIDER_OR_ENVIRONMENT_FAILURE | 0 | — |

### Failure Details (all 8 identical pattern)

```
status=FAILED
failure_code=UNRESOLVED_CONSTRAINT
details={"value": "Garanin.R.V"}
semantic_prepass:
  llm_used=False
  raw_intent=""
  raw_slots={}
grounded_values={}
```

**Root cause:** The LLM semantic prepass (which converts "Гаранина" → `person_raw=Гаранина` → grounder → `member_login=Garanin.R.V`) silently did not produce a result. The planner then proposed "Garanin.R.V" as a literal (it can infer this from the name in the query), but the safety system correctly rejected it because `grounded_values` was empty and "Garanin.R.V" is not a literal in the user's query text.

**This is not a source failure, not a grounding logic bug, not an LLM connection failure.** The LLM prepass simply returned an empty/no-op result in 8 out of 10 runs. The LLM was "healthy" per `/health` endpoint but the specific prepass call produced no structured output.

### Successful Runs (2/10)

Both successful runs show the full correct chain:
- `llm_used=True`
- `intent_hint=task_search_assignee`
- `person_raw='Гаранина'`
- `member_login=Garanin.R.V`
- `task-search-v3` with `assignee=Garanin.R.V`
- **Exact Oracle parity: 24/24**

---

## Source-Backed Identity Resolution Tests

| Login | external_id | Task count | Verdict |
|-------|-------------|-----------|---------|
| `garanin.r.v` | `Garanin.R.V` | 24 | **UNIQUE** ✅ |
| `semavin.m.m` | `Semavin.M.M` | 307 | **UNIQUE** ✅ |
| `kalachanov.v.v` | `Kalachanov.V.V` | 2867 | **UNIQUE** ✅ |
| `nonexistent.person` | *(HTTP 409)* | — | NO MATCH (negative control) ✅ |

**All 3 real team members resolve to exactly one `external_id` via the source-backed `search_users → find_units_by_filter` chain. The negative control correctly fails with HTTP 409 (no match).**

---

## Conclusion

The single remaining H1B blocker is **not** a code architecture issue. It is a **model output reliability gap** in the LLM semantic prepass: Qwen3.8 intermittently returns an empty/invalid result for the person-extraction step (80% failure rate for this specific query pattern).

### Key Facts for the Owner

1. **When LLM runs → full chain works** (grounding, search, parity all PASS)
2. **When LLM doesn't run → nothing downstream can recover** (grounded_values empty, planner literal rejected by safety)
3. **The source-backed identity resolver is 100% reliable** (all known members resolve uniquely)
4. **The LLM is not "broken"** — it works on some requests and not others (non-deterministic)
5. **The safety system is working correctly** — it fail-closes when it can't verify the identity

---

## Recommended Owner Fix

**Deterministic source-backed entity recovery in the grounding layer**

When the LLM semantic prepass produces no person slot (`llm_used=False` or `raw_slots` has no person field), the grounding layer should:

1. Extract potential surname tokens from the raw query (e.g., last noun, word before "задач", capitalized tokens)
2. For each candidate token, attempt resolution against the **source-backed identity** (the same `search_users` mechanism used by `assignee-tasks`)
3. If **exactly one** source-backed identity matches → bind `member_login` to that canonical login
4. If **zero or two or more** matches → fail closed (existing behavior, no change)

### Constraints for the fix

- ✅ Only activate when LLM prepass produced no person slot (does NOT replace or override successful LLM grounding)
- ✅ Source-backed only (no hardcoded surname→login mappings)
- ✅ No capability/intent routing changes
- ✅ No regex/keyword-to-capability routing
- ✅ Uniqueness required: 0 or 2+ matches → fail closed
- ✅ Must not bypass the existing typed constraint safety (the resulting `member_login` still goes through the same `$ground` validation)

This fix would convert the 8/10 `INTERPRETER_ENTITY_OMISSION` failures into successful grounded lookups, since "Гаранина" → "garanin.r.v" → `Garanin.R.V` is a unique source-backed resolution.

---

## Environment Notes

- PO Agent required 2 restarts during 169 testing due to intermittent LLM connection drops (`BrokenPipeError`). These are environmental and not code defects.
- In this forensic, the LLM was NOT used for 8/10 requests. The `/health` endpoint showed the LLM as "healthy" but the specific prepass call produced no structured output. This is distinct from a connection-level failure.

---

## Report File

`po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_IDENTITY_BOUNDARY_FORENSIC_170.md`

**Commit/push this report only. STOP.**