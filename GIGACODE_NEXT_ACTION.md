# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_161_H1B_AGENT_LOOP_BASELINE_FORENSIC`

## Mission
Start H1B of the Hermes re-architecture by proving the CURRENT Agent Core v3 execution shape before owner code changes. H1A Capability Registry is GREEN (Assignment 160). H1B target is a real bounded agent loop: plan/select capability -> execute tool -> observe result -> decide next tool or finish.

This assignment is QA/forensic ONLY. Do NOT modify production/backend/frontend/test source code, `.env`, prompts, registry contracts or Playwright tests. If the current runtime is single-shot, prove it precisely and STOP for owner implementation.

Accepted baseline:
- Assignment 157: H0 Browser harness GREEN.
- Assignment 160: `AGENT_CORE_V3_H1A_REGISTRY_GREEN` with REAL AS21 exact parity and Playwright 5/5.
- Current target LLM for PO Agent is the working Qwen 3.8 configuration selected by the owner/user. Do not change model during this assignment.

## H1B architectural target to compare against
The future runtime must support a bounded loop with explicit traceable steps:
1. semantic/goal understanding;
2. capability discovery/selection from the registry;
3. tool execution against authoritative source;
4. observation ingestion;
5. next-step decision: another capability call OR final answer;
6. hard max-iteration guard and fail-closed behavior;
7. no loss/mutation of accepted constraints across loop iterations;
8. no entity facts/hard-coded users/task IDs/counts in the planner/registry;
9. REAL AS21 remains authoritative.

Do NOT claim H1B exists merely because metadata currently says `stage=H1B`; prove actual control flow.

## Absolute rules
- REAL AS21/MCP-SWTR is Oracle B.
- No local DB/sync/fake/frozen/surrogate truth.
- Concurrency=1.
- Source-backed timeout 300s; proven transient failures: 2 retries with 30s backoff.
- Production/backend/frontend/test edits forbidden.
- No caveat GREEN.

## Phase 0 — provenance/runtime preflight
1. `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
2. Record HEAD and clean/dirty state.
3. Verify Assignment 160 report verdict `AGENT_CORE_V3_H1A_REGISTRY_GREEN`.
4. Start/reuse production-like runtime with:
   - `agent_core_v3_enabled=true`;
   - working Qwen 3.8 semantic LLM configuration;
   - REAL Task API/MCP-SWTR;
   - source healthy.
5. Record `/health` raw response. Do not continue if v3/LLM/REAL source preflight is not healthy.

## Phase 1 — static control-flow forensic
Inspect only; do not edit:
- `po-agent-platform-v2/src/po_agent/harness/agent_core_v3_pilot.py`
- `po-agent-platform-v2/src/po_agent/harness/agent_core_v3_registry.py`
- related runtime factory/bootstrap that invokes the v3 processor.

Answer with exact file/function/line boundaries:
1. Does one user turn allow more than one capability/tool execution today?
2. Is there an explicit loop state (`iteration`, `observation`, `next_action`, `finish`) or only direct intent -> executor branching?
3. After a tool result, is the LLM/planner called again with the observation?
4. Is there a max-iteration guard?
5. Is tool/capability selection performed through registry resolution or direct hard-coded executor branching after resolution?
6. Which metadata currently labels the stage H1B even though actual loop semantics may be absent?

Required verdict for this phase must be evidence-based: `CURRENT_SINGLE_SHOT` or `CURRENT_REAL_LOOP`.

## Phase 2 — dynamic trace proof on REAL AS21
Use fresh sessions and execute through Agent A:
1. `Задачи Гаранина`
2. `Покажи DMS-380`
3. `Задачи Калачанова в WMB`

For each persist:
- raw semantic frame;
- grounded values;
- accepted turn contract;
- resolved capability id;
- executor id/args;
- source authority;
- postconditions;
- any step/iteration/observation metadata if it exists;
- exact task keys.

Fresh-read Oracle B directly from REAL AS21 and prove exact key parity. The purpose is not to re-certify H1A; it is to determine whether each request executes as a one-shot pipeline or an actual agent loop.

## Phase 3 — multi-step capability challenge
Without changing code, submit a natural-language request that logically requires at least two task-family actions, for example:
`Проверь DMS-380 и затем покажи задачи его исполнителя`

Do NOT judge only the prose answer. Trace the actual runtime.

Record whether the agent:
A. performs point lookup -> observes assignee -> performs task search -> final answer, OR
B. collapses/guesses/routes to one capability/clarification/failure.

If the current certified task family cannot safely execute the second step because a capability/constraint is unsupported, that is acceptable as BASELINE evidence; do not add code or fabricate a success.

Also run a second variant:
`Найди задачи Гаранина в DMS и затем покажи подробности DMS-380`

The key acceptance question is whether two registry capability executions can occur in one turn with an observation-driven transition.

## Phase 4 — safety baseline
Prove current H1A protections still work while collecting baseline:
- unknown/unsupported intent fails closed;
- accepted constraints are not silently dropped;
- REAL AS21 only;
- no entity facts in registry/planner path;
- no stale session/correction contamination on fresh sessions.

Do not run the full 54-skill marathon here. H1B is not implemented yet; this is a narrow architecture forensic.

## Phase 5 — report and STOP
Write ONLY:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_AGENT_LOOP_BASELINE_161.md`

Allowed verdicts ONLY:
- `H1B_BASELINE_SINGLE_SHOT_OWNER_IMPLEMENTATION_REQUIRED`
- `H1B_BASELINE_REAL_LOOP_ALREADY_PRESENT`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`

The report MUST include a concise proposed first failing boundary for H1B implementation, but GigaCode must not implement the fix.

Commit/push ONLY the QA report and STOP.

## Start now
Execute Assignment 161 completely. First print current HEAD and this Status line so it is explicit that Assignment 160 is finished and H1B baseline forensic 161 has started.