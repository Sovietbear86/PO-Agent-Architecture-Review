# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_188_V4_COMPLETION_CONTRACT_REGATE`

## Mission
Assignment 187 implemented the **deterministic post-observation skill completion contract**
(`agent_core_v4_completion.py`) and the owner has completed live verification against fresh
REAL AS21. This is the **QA-only re-gate**: independently re-test the full verification matrix
and confirm the runtime completion mechanism is generic, safe, and source-authoritative.

## QA role
- GigaCode is **QA/tester only**.
- Do NOT modify production code, prompts, adapters, tests, or config.
- Do NOT modify `GIGACODE.md`, `V4_DOD_LOCK.md`, or this file.
- Do NOT start Assignment 189 or any next milestone.
- Commit/push only the allowed QA report file.

## Mandatory pre-read
```bash
git pull --ff-only origin feat/core8-real-query-hardening-v2
```
Record `git rev-parse HEAD` as `START_HEAD`.

Then read:
- `po-agent-platform-v2/qa_reports/` (latest A186 report for lineage)
- `V4_DOD_LOCK.md` §6 (completion contract properties)
- `AGENT_CORE_V4_SKILL_NATIVE_SPEC.md`
- A187 owner verification results in `qa_187_live_*.json` and `qa_187_oracle_b.json`
- `po-agent-platform-v2/src/po_agent/harness/agent_core_v4_completion.py`
- `po-agent-platform-v2/src/po_agent/harness/agent_core_v4.py` (completion contract integration)

## Scope
Independently re-verify the A187 completion contract against fresh REAL AS21.
No production code changes allowed.

## Invariants to verify
- `Qwen/Qwen3.8-27B` is the active model (check `.env`).
- No semantic prepass (`semantic_prepass_used=false` in all responses).
- No surname/person/task/sprint/query-phrase hardcode in the completion mechanism.
- No fabricated source facts.
- REAL AS21 remains authoritative.
- Recovery-time `READY` remains forbidden.
- Fail-closed for missing/ambiguous/source-failure.
- No GVS5H/multi-agent orchestration in V4.

## Phase 0 — Build / static invariants
1. Run full test suite: `cd po-agent-platform-v2 && source .venv/bin/activate && python -m pytest tests/ -q`
   - Record total passed/failed/error.
   - No NEW failures beyond the A186 baseline (document known pre-existing failures).
2. Focused suites must be GREEN:
   - `python -m pytest tests/test_agent_core_v4_completion_contract.py -v` (20/20)
   - `python -m pytest tests/ -k "v4" -v` (all V4 tests)
   - B1/B2 regression: `python -m pytest tests/ -k "sprint or identity or task_api" -v`
3. Static invariants in `agent_core_v4_completion.py`:
   - No `if` branching on entity names, task keys, sprint IDs, or query phrases.
   - No `DMS-380`, `Semavin`, `Kalachanov`, `SPRNT` literal in production logic.
   - All completion requirements declared in `SkillSpecV4` tuples (not ad-hoc runtime checks).

## Phase 1 — P1 gate: 10x DMS-380 multistep exact parity
Start fresh task-api + fresh PO Agent (new ports, record them).
Refresh Oracle B live (no hardcoded counts).

Run: `10x` `Покажи DMS-380 и затем задачи его исполнителя`

Mandatory per run:
- status=COMPLETED
- `completion=runtime_contract` (NOT `planner_ready`)
- exact key-set parity with Oracle B
- `semantic_prepass_used=false`
- last trajectory entry is the runtime marker (no extra model terminal-repair turns after satisfaction)
- record: trajectory, latency, keys, completion type

Gate: **10/10 exact parity** required.

## Phase 2 — Second lookup→assignee→tasks family
Run: `5x` a second lookup→assignee→tasks case discovered live (DMS-99 if still source-valid,
or another valid task key).

Gate: **5/5 exact parity**, `completion=runtime_contract`.

## Phase 3 — Mixed matrix / unseen combinations
Run at minimum:
- `5x` person collection (roster member, e.g. Зhdanov)
- `5x` person + space + status
- `3x` current-sprint task query on a source-valid sprint
- `3x` sprint period resolution (human period → canonical sprint)
- `2x` plural active-sprint list
- `2x` non-roster identity (source-authority resolution)

Gate: exact parity for each.

## Phase 4 — B1/B2 retained exactness
Verify the A185 B1/B2 fixes remain effective:
- Sprint with >100 tasks (if available) returns complete collection
- Status classification (terminal vs open) is source-accurate
- Run at least one case from each

## Phase 5 — A183 scenarios
Three scenarios remain green:
1. Human-period sprint resolution
2. Plural active-sprint list
3. Source-authority non-roster identity

## Phase 6 — Safety / fail-closed
Negative controls:
- Invented task (e.g. DMS-999999) → typed not-found, 0 keys
- Invented person → fail-closed, 0 keys
- Invented sprint → typed not-found/clarification, 0 keys
- Ambiguous identity → NEEDS_CLARIFICATION, 0 keys
- (Optional) source unavailable → bounded typed failure

## Phase 7 — Proof of deterministic completion
For ALL multi-step lookup→collection runs, record:
- Whether completion was `runtime_contract` or `planner_ready`
- That NO post-satisfaction planner repair loop occurred
- That the last trajectory step is the runtime marker (no extra LLM calls after the satisfying observation)

This proves the trajectory no longer depends on stochastic model terminal `READY`.

## Allowed report file
`po-agent-platform-v2/qa_reports/AGENT_CORE_V4_COMPLETION_CONTRACT_REGATE_188.md`

## Report structure
```
# Assignment 188 — V4 Completion Contract Re-Gate
## Verdict
## Environment (HEAD, ports, model, Oracle B timestamp)
## Phase 0: Build / static
## Phase 1: P1 10x gate
## Phase 2: Second lookup family
## Phase 3: Mixed matrix
## Phase 4: B1/B2 retained
## Phase 5: A183 scenarios
## Phase 6: Safety / fail-closed
## Phase 7: Deterministic completion proof
## Known issues / pre-existing defects
## Recommendation
```

## Verdict rules
- `AGENT_CORE_V4_REPRESENTATIVE_POC_GREEN` only if ALL mandatory gates pass:
  - P1 10/10, P2 5/5, P3 exact, P4/P5/P6/P7 all pass
- Otherwise: precisely attributed bounded RED / source block / model-reliability finding
- If GREEN, recommendation MUST be:
  **STOP backend POC remediation → proceed to V4-PLUGIN gate → then V4-BROWSER → progressive 54-skill migration → full V4 E2E gate.**

## STOP
After report creation and commit/push, do NOT continue to the next assignment.
