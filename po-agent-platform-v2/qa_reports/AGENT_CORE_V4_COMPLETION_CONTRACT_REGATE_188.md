# Assignment 188 — V4 Completion Contract Re-Gate

## Verdict

**AGENT_CORE_V4_REPRESENTATIVE_POC_GREEN**

All mandatory gates pass. The deterministic post-observation skill completion contract
(Assignment 187) is proven generic, safe, and source-authoritative against fresh REAL AS21.

## Environment

| Item | Value |
|------|-------|
| START_HEAD | `4affbf5ed45360d24d80f42037615599cb43bca6` |
| Branch | `feat/core8-real-query-hardening-v2` |
| Task-api port | 8101 (fresh, stdio→MCP-SWTR:3000) |
| PO Agent port | 8102 (fresh, agent_core_v4_ready=true) |
| Model | `Qwen/Qwen3.8-27B` (confirmed in `.env`) |
| Oracle B timestamp | 2026-09-15T11:54:30Z (fresh live collection) |
| Oracle key counts | DMS-380 assignee=309, DMS-99 assignee=66, Zhdanov=11, Kalachanov STS open=404, DMS-SPRNT-3=51 |

## Phase 0: Build / static

| Suite | Result |
|-------|--------|
| Full test suite | **1369 passed**, 12 skipped, 16 failed, 11 errors |
| A186 baseline delta | +20 passed (new completion contract tests); 16F+11E identical to A186 baseline (real-LLM, SWTR integration, order-dependent) |
| `test_agent_core_v4_completion_contract.py` | **20/20 PASSED** |
| All V4 tests (`-k "v4"`) | **69 passed** |
| B1/B2 regression (`-k "sprint or identity or task_api"`) | 143 passed, 4 failed (all pre-existing baseline classes) |

### Static invariants in `agent_core_v4_completion.py`:
- ✅ No `DMS-380`, `Semavin`, `Kalachanov`, `SPRNT` or any entity literal in production logic
- ✅ No `if` branching on entity names, task keys, sprint IDs, or query phrases
- ✅ All completion requirements declared in `SkillSpecV4` tuples via `CompletionRequirement` dataclass
- ✅ Contract evaluation is purely structural: capability_id matching, dotted data path navigation, typed argument binding
- ✅ `_CONSTRAINT_RESOLVERS` maps capability→(role, data_key) structurally, not by entity

## Phase 1: P1 10x gate

Query: `Покажи DMS-380 и затем задачи его исполнителя`

| Run | Status | Completion | Keys | Exact | Prepass | Latency | Verdict |
|-----|--------|-----------|------|-------|---------|---------|---------|
| p1-1 | COMPLETED | runtime_contract | 309/309 | ✅ | False | 187.2s | PASS |
| p1-2 | COMPLETED | runtime_contract | 309/309 | ✅ | False | 203.0s | PASS |
| p1-3 | COMPLETED | runtime_contract | 309/309 | ✅ | False | 132.7s | PASS |
| p1-4 | COMPLETED | runtime_contract | 309/309 | ✅ | False | 98.7s | PASS |
| p1-5 | COMPLETED | runtime_contract | 309/309 | ✅ | False | 66.7s | PASS |
| p1-6 | COMPLETED | runtime_contract | 309/309 | ✅ | False | 113.7s | PASS |
| p1-7 | COMPLETED | runtime_contract | 309/309 | ✅ | False | 76.2s | PASS |
| p1-8 | COMPLETED | runtime_contract | 309/309 | ✅ | False | 58.1s | PASS |
| p1-9 | COMPLETED | runtime_contract | 309/309 | ✅ | False | 49.6s | PASS |
| p1-10 | COMPLETED | runtime_contract | 309/309 | ✅ | False | 49.2s | PASS |

**Gate: 10/10 exact parity ✅**

## Phase 2: Second lookup family

Query: `Покажи DMS-99 и затем задачи его исполнителя` (assignee: Kuznetsov.M.Se)

| Run | Status | Completion | Keys | Exact | Prepass | Latency | Verdict |
|-----|--------|-----------|------|-------|---------|---------|---------|
| p1b-1 | COMPLETED | runtime_contract | 66/66 | ✅ | False | 103.6s | PASS |
| p1b-2 | COMPLETED | runtime_contract | 66/66 | ✅ | False | 63.2s | PASS |
| p1b-3 | COMPLETED | runtime_contract | 66/66 | ✅ | False | 93.1s | PASS |
| p1b-4 | COMPLETED | runtime_contract | 66/66 | ✅ | False | 130.1s | PASS |
| p1b-5 | COMPLETED | runtime_contract | 66/66 | ✅ | False | 197.9s | PASS |

**Gate: 5/5 exact parity ✅** (proves the contract is entity-agnostic)

## Phase 3: Mixed matrix

### Person collection (Zhdanov, 5x):

| Run | Status | Completion | Keys | Exact | Verdict |
|-----|--------|-----------|------|-------|---------|
| p2-zhdanov-1 | COMPLETED | runtime_contract | 11/11 | ✅ | PASS |
| p2-zhdanov-2 | COMPLETED | runtime_contract | 11/11 | ✅ | PASS |
| p2-zhdanov-3 | COMPLETED | runtime_contract | 11/11 | ✅ | PASS |
| p2-zhdanov-4 | COMPLETED | runtime_contract | 11/11 | ✅ | PASS |
| p2-zhdanov-5 | COMPLETED | runtime_contract | 11/11 | ✅ | PASS |

**5/5 exact ✅**

### Person + space + status (Semavin DMS open, 5x):

| Run | Status | Completion | Keys | Exact | Verdict |
|-----|--------|-----------|------|-------|---------|
| p2b-sem-dms-1 | COMPLETED | runtime_contract | 6/6 | ✅ | PASS |
| p2b-sem-dms-2 | COMPLETED | runtime_contract | 6/6 | ✅ | PASS |
| p2b-sem-dms-3 | COMPLETED | runtime_contract | 6/6 | ✅ | PASS |
| p2b-sem-dms-4 | COMPLETED | runtime_contract | 6/6 | ✅ | PASS |
| p2b-sem-dms-5 | COMPLETED | runtime_contract | 6/6 | ✅ | PASS |

**5/5 exact ✅**

### Person + space + status (Kalachanov STS open, 5x):

| Run | Status | Completion | Keys | Exact | Verdict |
|-----|--------|-----------|------|-------|---------|
| p2b-kal-sts-1 | COMPLETED | runtime_contract | 404/404 | ✅ | PASS |
| p2b-kal-sts-2 | COMPLETED | runtime_contract | 404/404 | ✅ | PASS |
| p2b-kal-sts-3 | COMPLETED | runtime_contract | 404/404 | ✅ | PASS |
| p2b-kal-sts-4 | COMPLETED | runtime_contract | 404/404 | ✅ | PASS |
| p2b-kal-sts-5 | COMPLETED | runtime_contract | 404/404 | ✅ | PASS |

**5/5 exact ✅**

### Current-sprint task query (DMS, 3x):

| Run | Status | Completion | Keys | Exact | Verdict |
|-----|--------|-----------|------|-------|---------|
| p3-current-1 | COMPLETED | runtime_contract | 51/51 | ✅ | PASS |
| p3-current-2 | COMPLETED | runtime_contract | 51/51 | ✅ | PASS |
| p3-current-3 | COMPLETED | runtime_contract | 51/51 | ✅ | PASS |

**3/3 exact ✅**

## Phase 4: B1/B2 retained

- **B1 (bounded sprint collection):** DMS-SPRNT-3 (51 tasks) returned complete collection 3/3 exact.
- **B2 (status_type classification):** Kalachanov STS open = 404/404 (status_type correctly classifies terminal vs open; undecodable=0 in oracle).

**Both B1 and B2 remain effective ✅**

## Phase 5: A183 scenarios

| Scenario | Runs | Result | Verdict |
|----------|------|--------|---------|
| Human-period sprint (август→DMS-SPRNT-2) | 3/3 | COMPLETED, answer contains DMS-SPRNT-2, runtime_contract | PASS |
| Plural active-sprint list (DMS→DMS-SPRNT-3) | 2/2 | COMPLETED, answer contains DMS-SPRNT-3, runtime_contract | PASS |
| Source-authority non-roster (Ivanov in DMS-SPRNT-2) | 2/2 | COMPLETED, 0 keys, identity resolved as Ivanov.P.Se from source | PASS |

**All A183 scenarios remain green ✅**

## Phase 6: Safety / fail-closed

| Negative control | Status | Keys | Verdict |
|-----------------|--------|------|---------|
| Invented task (DMS-999999) | COMPLETED (0 keys, "not found") | 0 | PASS |
| Invented person (Неизвестный Псевдоним) | FAILED (fail-closed) | 0 | PASS |
| Invented sprint (DMS-SPRNT-999) | NEEDS_CLARIFICATION | 0 | PASS |
| Ambiguous identity (Задачи Иванова) | NEEDS_CLARIFICATION | 0 | PASS |

**4/4 fail-closed ✅** — zero fabrication, zero keys in all negative controls.

## Phase 7: Deterministic completion proof

Across all 40 COMPLETED runs (P1 10x + P1b 5x + P2 5x + P2b 10x + P3 3x + P4 7x):

| Invariant | Result |
|-----------|--------|
| All use `completion=runtime_contract` | **40/40 (100%)** |
| Zero use `planner_ready` | **0/40** |
| Last trajectory entry is the runtime marker | **40/40** |
| No post-satisfaction model terminal-repair turns | **40/40** |
| All 15 multi-step lookup→collection runs: exactly 4 turns (load→lookup→search→ready) | **15/15** |

The trajectory **no longer depends on stochastic model terminal READY**. The completion
is deterministically recognized by the runtime after the typed observation satisfies the
declared contract.

## Invariants verification (all runs)

| Invariant | Result |
|-----------|--------|
| `semantic_prepass_used=false` | **49/49 (100%)** |
| No entity hardcode in completion mechanism | ✅ (static scan clean) |
| No fabricated source facts | ✅ (all keys match Oracle B) |
| Recovery-time READY remains forbidden | ✅ (test_recovery_ready_still_forbidden_by_planner_protocol PASSED) |
| Fail-closed for missing/ambiguous/source-failure | ✅ (Phase 6) |
| No GVS5H/multi-agent orchestration in V4 | ✅ (V4 runtime only) |

## Known issues / pre-existing defects

1. **Qwen3.8-27B Cyrillic tokenization** (pre-existing, documented in A187):
   - "Задачи Семавина" (unscoped, 5/5 FAIL): model tokenizes "Семавин"→"Семанин", causing
     `member.resolve` to receive a wrong reference. This is a **model limitation**, not a
     completion contract defect.
   - With explicit space context ("Открытые задачи Семавина в DMS"), the same query succeeds
     5/5 (6/6 exact). The completion contract is not the failure boundary.
   - Not in scope for this assignment (no production changes allowed).

2. **16 failed tests + 11 errors** in full suite: byte-identical to A186 baseline
   (real-LLM integration, SWTR integration, order-dependent, repository hygiene). Zero new failures.

## Recommendation

**STOP backend POC remediation → proceed to V4-PLUGIN gate → then V4-BROWSER → progressive 54-skill migration → full V4 E2E gate.**

The deterministic completion contract (A187) is fully certified at the QA re-gate boundary.
The runtime no longer relies on stochastic model READY for any contracted skill trajectory.
All collection paths (lookup→assignee→search, person collection, sprint collection, status
classification) are proven exact against fresh REAL AS21 with zero fabrication and full
fail-closed safety.
