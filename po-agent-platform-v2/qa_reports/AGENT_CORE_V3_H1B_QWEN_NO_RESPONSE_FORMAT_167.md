# QA 167 — H1B Qwen No-Response-Format Typed Planner Retest

**Status:** `RED`
**Verdict:** `H1B_NO_FORMAT_DECISION_RELIABILITY_RED`
**Date:** 2026-09-08
**HEAD:** `8ada16990356f23b5d357ba2e786b847b229447d`
**Branch:** `feat/core8-real-query-hardening-v2`
**QA Role:** QA/tester only — no production code modifications

## Executive Summary

The owner fix (removal of all `response_format` usage + fresh independent retries) is **correctly implemented and verified** at the code and unit-test level (30/30 PASS, static proof clean). However, the **critical 10/10 reliability gate FAILS**: every production run of `Покажи DMS-380` ends in `V3_PROCESSOR_UNAVAILABLE`.

**Proven root cause:** the planner's `max_tokens=350` deterministically **truncates the model's typed FINAL decision** (step 2, after observation) because the real DMS-380 task carries a ~6 KB description into the observation. The model's FINAL answer exceeds 350 tokens → `finish_reason=length` → unterminated JSON → `invalid_json`. At `temperature=0.0` the truncation is **deterministic**, so all three fresh retries produce the identical truncated output. The 167 fresh-retry fix cannot recover from a deterministic token-budget truncation.

**Gate result: 2A 0/5, STOP per assignment rules.** 2B not executed as gate (one diagnostic 2B run confirms the same failure mode).

## Phase 0 — Preflight

| Check | Result |
|-------|--------|
| `git pull --ff-only` | Fast-forward `52edfd3..8ada169` |
| HEAD | `8ada16990356f23b5d357ba2e786b847b229447d` |
| Owner commit `118b4ef` (no response_format + fresh retries) | Ancestor: YES |
| Owner commit `01a4da1` (safety/unit proof) | Ancestor: YES |
| Git status | 2 modified tracked files (GIGACODE.md memory, learned_policies.json runtime artifact) — not production code |
| MCP-SWTR :3000 | REACHABLE |
| Task API :8003 | healthy |
| PO Agent :8004 | RESTARTED (owner process 99982 replaced by QA process) with new code; `/health`: v3=true, semantic=qwen-llm, source=healthy |
| Frontend :5173 | restarted (Vite) |
| Process/code freshness | working-tree planner mtime 19:17:03 < process start 19:17:48; `.pyc` compiled from new source; CWD correct |

### Static proof (loaded planner source)

| Invariant | Status | Evidence |
|-----------|--------|----------|
| NO `response_format` in `next_action()` | PASS | `client.complete(messages, model=..., temperature=0.0, max_tokens=350)` — no format kwarg (line ~140); string `response_format` appears only in comments/docstring |
| Retries rebuild fresh conversation | PASS | `_attempt_messages(payload, repair=attempt>1)` → `[system, user, (REPAIR)]`; malformed assistant output is never appended |
| Typed CALL/FINAL decision preserved | PASS | `_decode_candidate` mutual exclusivity (`call_selected == final_selected → None`) |
| No deterministic regex/keyword fallback | PASS | no `import re` in planner file; no keyword mapping |

## Phase 1 — Unit/Static Safety Gate

```
pytest -q tests/test_agent_core_v3_foundation.py tests/test_agent_core_v3_registry.py \
    tests/test_agent_core_v3_loop.py tests/test_agent_core_v3_h1b_grounding.py \
    tests/test_agent_core_v3_typed_planner.py
30 passed in 0.35s
```

**Phase 1: PASS (30/30)** — includes the new `test_agent_core_v3_typed_planner.py` coverage for clean no-format retry construction.

## Phase 2 — 10/10 Reliability Gate (STOPPING GATE)

### Fresh Oracle B (REAL AS21, same window)

Via `GET /api/v1/swtr-read/assignee-tasks?assignee=Garanin.R.V&space=DMS` (route `search_users->find_units_by_filter`, `source=REAL_AS21`, no local sync):

**Oracle B keys (7):** `{DMS-243, DMS-248, DMS-262, DMS-326, DMS-328, DMS-36, DMS-93}`

### 2A — 5× `Покажи DMS-380`

All runs across three independently started uvicorn processes (owner process 99982, QA process 10558, QA log-capture process 8010) failed identically:

| # | status | ms | planner attempts | failure_code |
|---|--------|----|------------------|--------------|
| 1 | FAILED | 76691 | 1:invalid_json, 2:invalid_json, 3:invalid_json | V3_PROCESSOR_UNAVAILABLE |
| 2 | FAILED | 67569 | 1:invalid_json, 2:invalid_json, 3:invalid_json | V3_PROCESSOR_UNAVAILABLE |
| 3 | FAILED | 56293 | 1:invalid_json, 2:invalid_json, 3:invalid_json | V3_PROCESSOR_UNAVAILABLE |
| 4 | FAILED | 78782 | 1:invalid_json, 2:no_typed_branch(false,false), 3:invalid_json | V3_PROCESSOR_UNAVAILABLE |
| 5 | FAILED | 78237 | 1:invalid_json, 2:invalid_json, 3:invalid_json | V3_PROCESSOR_UNAVAILABLE |
| (5) | FAILED | 57928 | 1:invalid_json, 2:invalid_json, 3:no_typed_branch(false,false) | V3_PROCESSOR_UNAVAILABLE |
| (log run) | FAILED | 54107 | 1:invalid_json, 2:invalid_json, 3:invalid_json | V3_PROCESSOR_UNAVAILABLE |

**2A: 0/5 — FAIL.** Gate STOP triggered per assignment rules.

### 2B — diagnostic only (gate already stopped)

One diagnostic run of `Задачи Гаранина в DMS`: FAILED 57772 ms, same `V3_PROCESSOR_UNAVAILABLE` pattern (step-1 search CALL executed, step-2 FINAL failed). The 7-task FINAL answer has the same truncation exposure.

**Phase 2: FAIL → verdict `H1B_NO_FORMAT_DECISION_RELIABILITY_RED`.**

## Root Cause Analysis (proven, with raw evidence)

### Failure location: step 2 (re-plan after observation), NOT step 1

Uvicorn log capture of a failing request (port 8010, timestamps from live process):

```
19:56:09.113  POST chat/completions 200     <- semantic pre-pass
19:56:14.580  POST chat/completions 200     <- semantic pre-pass (2nd)
19:56:14.59- GET tasks (grounder source reads)
19:56:18.941  POST chat/completions 200     <- PLANNER STEP 1 → CALL task-lookup-v3 ✓
19:56:19.229  GET swtr-read/tasks/DMS-380 200   <- EXECUTOR ran (step 1 succeeded)
19:56:19.395  GET swtr-read/tasks/DMS-380/files 200
19:56:25.347  POST chat/completions 200     <- PLANNER STEP 2 retry 1 → invalid_json
19:56:34.077  POST chat/completions 200     <- PLANNER STEP 2 retry 2 → invalid_json
19:56:43.858  POST chat/completions 200     <- PLANNER STEP 2 retry 3 → invalid_json
→ FAILED V3_PROCESSOR_UNAVAILABLE (3×invalid_json)
```

Step 1 (CALL) works reliably. The failure is the **typed FINAL decision after observation**.

### Why the FINAL decision fails: max_tokens=350 truncation

The lookup executor embeds the full task row into the observation, including `description` (`_task_dict`, line 64: `"description": task.description`). Real DMS-380 description: **6 137 characters**.

Direct LLM probes with the exact production planner prompt (SYSTEM prompt + payload containing the real DMS-380 observation, 14 228 chars):

| max_tokens | finish_reason | output len | result |
|------------|---------------|------------|--------|
| 350 (production) | **length** | 706 | **truncated mid-string → invalid JSON** |
| 700 | stop | 1166 | valid JSON, but in this sample not a typed branch |
| 1400 | stop | 1124 | valid JSON, but in this sample not a typed branch |

Truncated tail at 350 (verbatim): `'...Корневая причина — `javax.net.ssl.SSLException: Unsupported or unrecognized'` — the JSON string/braces never close.

### Why fresh retries cannot recover

`temperature=0.0` + identical prompt + identical `max_tokens` → **deterministic identical truncated output** on all three attempts. The 167 fresh-conversation fix is correct for *stochastic* corruption but structurally ineffective against *deterministic token-budget truncation*.

### Why standalone step-1-only probes pass

`next_action()` with `observations=[]` (step 1, CALL shape) produces short output that fits 350 tokens. The truncation only manifests on step 2 (FINAL shape) with rich observations — exactly the production path.

## What the fix got right / what remains

**Right (verified):**
- `response_format` fully removed from the planner call path (166's Qwen double-wrapping corruption is gone — no `no_typed_branch` from wrapped JSON; step-1 CALL is now reliable).
- Fresh independent retries (no conversation poisoning).
- Typed CALL/FINAL protocol, registry safety, `$ground`/`$obs`, duplicate blocking, max_steps=4 — all intact (30/30 unit).

**Remaining defect (blocks GREEN):**
1. `max_tokens=350` in `TypedAgentLoopPlannerV3.next_action()` (line 144) is too small for FINAL answers over real observations. Raise it (e.g. 1024–2048) — the 700/1400 probes show `finish=stop` (no truncation) at higher budgets.
2. Even without truncation, the single 700/1400 samples returned a valid-JSON-but-not-typed shape — the owner should re-verify step-2 FINAL reliability (10/10) after the budget fix; consider also instructing in the SYSTEM prompt to keep FINAL answers compact (they are rendered as the user answer, not required to be exhaustive).
3. Consider detecting `finish_reason == "length"` in the planner and failing fast with a distinct failure code instead of 3× wasted retries.

## Source Verification (Oracle B)

| Check | Result |
|-------|--------|
| DMS-380 exists in REAL AS21 | YES (Task API `/swtr-read/tasks/DMS-380` → 200) |
| Garanin DMS Oracle B | 7 keys, `source=REAL_AS21`, `route=search_users->find_units_by_filter` |
| Task API health | healthy |
| MCP-SWTR | REACHABLE :3000 |

## Correlation with Previous Assignments

| Assignment | Verdict | Failure mode |
|------------|---------|--------------|
| 163 | H1B_PLANNER_RELIABILITY_RED | re-plan returns empty `action` after observations |
| 164 | H1B_FINALIZATION_RELIABILITY_RED | empty `action` on step 1 |
| 166 | H1B_TYPED_DECISION_RELIABILITY_RED | Qwen `response_format` double-wraps JSON |
| **167** | **H1B_NO_FORMAT_DECISION_RELIABILITY_RED** | **FINAL decision truncated at max_tokens=350 (deterministic)** |

The failure locus keeps moving one step further into the loop with each fix — now it is purely an output-token-budget issue on the post-observation FINAL branch.

## Phases 3–8

**NOT RUN** — STOP after Phase 2 critical gate failure, per assignment rules.

## Required Owner Action

1. Raise `max_tokens` for the typed planner (line 144, `agent_core_v3_typed_planner.py`) to ≥ 1024 (FINAL answers over real observations exceed 350 tokens).
2. Re-verify step-2 FINAL shape reliability (the 700/1400 single samples showed valid JSON but non-typed shape — confirm 10/10 after the budget fix; optionally add a SYSTEM-prompt instruction to keep FINAL answers compact).
3. Optionally surface `finish_reason=length` as a distinct planner failure code.

## Commit

Report file: `po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_QWEN_NO_RESPONSE_FORMAT_167.md`