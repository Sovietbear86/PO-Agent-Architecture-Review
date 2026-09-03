# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_144_AGENT_CORE_V3_H1B_PILOT`

## Mission
Certify the first executable Agent Core v3 pilot vertical. Owner code now provides LLM-first semantic interpretation, deterministic grounding, immutable AcceptedTurnContract, pilot Capability Registry, deterministic task lookup/search executors, REAL AS21 adapter reuse, result postcondition validation, and strangler routing enabled only with `agent_core_v3_enabled=True`.

Owner commits:
- `370553175128cd7b6df99da70cb921d5e47696fe`
- `322576cbc2644e8c82b9d97ea224f4d20f644b4f`
- `931632e6d1cc58be286f58fef96f3d4020f84be4`

QA only. Do not modify production/backend/frontend code.

## Rules
- REAL AS21/MCP-SWTR only for factual acceptance; Oracle B must use direct MCP independently.
- Do not run the full 54-skill marathon.
- Use an isolated runtime with `agent_core_v3_enabled=True`; do not switch browser production default yet.
- Fresh session per case, concurrency 1, timeout 300 seconds.
- Exact task-key-set equality is mandatory.

## Phase 0 — provenance
Record HEAD, clean state, owner commits and source health. Verify the normal/default runtime still has v3 disabled.

## Phase 1 — v3 trace contract
For every pilot capture `_agent_core_v3`: interpreter_class, llm_used, raw_semantic_frame, grounded_values, accepted_turn_contract, capability_id/version, executor_args, source_authority/oracle_id and postcondition_results. Require `llm_used=true` for natural-language cases.

## Phase 2 — Oracle B
Read fresh direct REAL MCP truth for:
1. Garanin.R.V all approved spaces
2. Garanin.R.V in DMS
3. Kalachanov.V.V in WMB
4. DMS-380 point-read
Persist exact key sets and all pages.

## Phase 3 — Agent Core v3 A/B
Execute with v3 enabled:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова в WMB`
4. `Покажи DMS-380`

Require all explicitly requested constraints in the accepted contract, canonical assignee grounding, WMB preserved through executor args, exact key equality against Oracle B, all postconditions passed, no unrelated-space evidence, and correct DMS-380 lookup.

## Phase 4 — contract safety unit checks
Using isolated synthetic data only, prove:
- contract `assignee=Kalachanov.V.V, space=WMB` rejects a result row with `project_space=DMS` as `RESULT_CONTRACT_VIOLATION`;
- requested `space` omitted from executor arguments raises `CONSTRAINT_LOSS`.

## Phase 5 — strangler isolation
With v3 enabled, send one clearly non-pilot sprint/release query with a validated entity and prove it delegates to legacy. With v3 disabled, prove pilot-shaped queries also delegate to legacy.

## Phase 6 — protected regressions
Recheck `DMS-999999999` authoritative NOT_FOUND and one protected legacy assignee query with v3 disabled.

## Final report
Write `po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_PILOT_144.md`.

Allowed verdicts:
- `AGENT_CORE_V3_H1B_GREEN`
- `AGENT_CORE_V3_SEMANTIC_RED`
- `AGENT_CORE_V3_AB_PARITY_RED`
- `AGENT_CORE_V3_CONSTRAINT_RED`
- `AGENT_CORE_V3_ROUTING_RED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN requires all four pilot scenarios to execute through v3, exact A/B parity, immutable constraint preservation, and validator blocking of wrong-space output. Commit/push QA report only and STOP.

## Start now
Execute Assignment 144 completely.