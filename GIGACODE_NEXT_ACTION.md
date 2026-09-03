# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_147_AGENT_CORE_V3_H1B_FINAL`

## Mission
Final H1B certification after owner review of Assignment 146.

Important provenance:
- QA commit `7729db3103a6b95c6aaa76aabfaf81860ce8baf8` violated QA-only rules by changing production code.
- Owner reviewed that diff and REJECTED the generic Russian surname suffix normalization as unnecessary/unsafe.
- Owner commit `07c807b1fec0d829d365c6a01e0bb377e6ec83c0` removes the unsafe normalization and restores the prior deterministic TeamDirectory matcher.
- The useful generalized fix from 146 remains in `ProductionEntityResolverV2.ground()`: when authoritative grounding successfully resolves `member_login`, any stale pre-grounding `member_login` clarification must be removed.

QA/tester only. DO NOT modify production/backend/frontend code. If any product defect is found, report it and STOP.

## Absolute rules
- REAL AS21/MCP-SWTR only for factual Oracle B.
- No local DB, sync, fake, frozen or cached task facade as truth.
- v3 enabled only in isolated certification runtime.
- Fresh session UUID for every independent case.
- Concurrency=1; timeout 300s; retry transient source failures at most twice with 30s backoff.
- Exact task-key-set equality, not counts only.
- H1B GREEN requires 4/4 pilot scenarios COMPLETED through v3 with no unnecessary clarification.

## Phase 0 — provenance and code-safety gate
1. Pull branch; record exact HEAD and clean/dirty state.
2. Prove owner commit `07c807b1...` is ancestor of HEAD.
3. Inspect `entity_grounding.py` read-only and prove `_normalize_russian_case` / suffix rewrite logic is ABSENT.
4. Inspect `production_entity_grounding_v2.py` read-only and prove successful `member_login` grounding removes only stale clarification for the same field.
5. Verify GigaCode makes zero production edits during this assignment.

## Phase 1 — grounding unit/forensic gate
Using the real team config but no source fabrication, verify these person inputs against `TeamDirectory.resolve_person()` and the production grounder:
- `Гаранина`
- `Гаранин`
- `Калачанова`
- `Калачанов`
- `Kalachanov.V.V`

Requirements:
- existing deterministic token/prefix matching is sufficient for unique configured identities where applicable;
- no string suffix mutation is used;
- unique grounded identity -> canonical login and no stale `member_login` clarification;
- true ambiguity -> clarification remains fail-closed.

Include at least one synthetic ambiguous-directory unit case with two matching entries to prove the clarification is NOT broadly suppressed.

## Phase 2 — fresh Oracle B
Re-read current REAL AS21 truth independently for:
1. Garanin.R.V all approved spaces;
2. Garanin.R.V in DMS;
3. Kalachanov.V.V in WMB;
4. DMS-380 point-read.
Persist exact key sets and page/source evidence. Do not reuse prior counts.

## Phase 3 — final v3 A/B pilot 4/4
Start isolated runtime with `PO_AGENT_AGENT_CORE_V3_ENABLED=true` and existing production LLM settings.
Execute with fresh sessions:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова в WMB`
4. `Покажи DMS-380`

For every case capture `_agent_core_v3` metadata.
Natural-language acceptance requires:
- `llm_used=true`;
- LLM-backed interpreter;
- grounded canonical identity;
- accepted contract preserves every requested constraint;
- no clarification after a unique authoritative identity is grounded;
- exact key-set equality with fresh Oracle B;
- postcondition validation PASS;
- no unrelated-space evidence.

For `Задачи Калачанова в WMB` specifically require:
- COMPLETED, not NEEDS_CLARIFICATION;
- `assignee=Kalachanov.V.V` in accepted contract/executor args;
- `space=WMB` preserved;
- exact WMB task-key set == Oracle B.

## Phase 4 — negative identity safety
Prove the generalized fix does not convert ambiguity into guessing:
- an intentionally ambiguous person resolution must return clarification/fail-closed;
- an unknown person must not silently map to a configured member;
- no hardcoded Garanin/Kalachanov special-case production code exists in grounding.

## Phase 5 — protected regression
- `DMS-999999999` -> authoritative task not found, not source unavailable.
- v3 disabled -> pilot-shaped request delegates legacy.
- v3 enabled + clear non-pilot validated request -> delegates legacy.
- wrong-space synthetic result under WMB contract -> RESULT_CONTRACT_VIOLATION.

## Final report
Write:
`po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_FINAL_147.md`

Allowed verdicts:
- `AGENT_CORE_V3_H1B_FINAL_GREEN`
- `AGENT_CORE_V3_IDENTITY_RED`
- `AGENT_CORE_V3_AB_PARITY_RED`
- `AGENT_CORE_V3_CONSTRAINT_RED`
- `AGENT_CORE_V3_ROUTING_RED`
- `BLOCKED_BY_PROVEN_ENVIRONMENT`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

GREEN is forbidden unless all 4 pilot cases actually execute successfully through v3 and exact Oracle parity is proven. No "3/4 plus expected clarification" exception.

Commit/push QA report ONLY and STOP.

## Start now
Execute Assignment 147 completely.