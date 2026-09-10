# GigaCode — Current Action

## Status
`PAUSED_FOR_OWNER_AGENT_CORE_V4_SKILL_NATIVE_FOUNDATION`

## Decision
Assignment 175 is accepted as evidence that the current mandatory semantic-prepass/clarification architecture is too brittle for the product goal. Do NOT continue creating or testing surname/field/phrase-specific H1B fixes.

Authoritative architecture pivot:
- `AGENT_CORE_V4_SKILL_NATIVE_SPEC.md`
- `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`

## GigaCode role now
QA/adversarial reviewer only. Wait for the owner to commit the first Agent Core v4 implementation slice and a new explicit QA assignment.

Do NOT:
- modify production/backend/frontend/test code;
- add semantic field aliases or clarification suppression exceptions;
- add surname/name routing;
- add phrase-specific skills;
- edit model prompts/config to hide the H1B problem;
- rerun Assignment 175 as if it were still an acceptance gate;
- use local DB/sync/fake/frozen data as truth.

## Evidence preserved from H1B
Do not discard the work already proven. The v4 implementation should reuse/carry forward where appropriate:
- REAL AS21/MCP-SWTR source plane;
- live Task API routes;
- session isolation;
- typed capability contracts;
- typed CALL/FINAL loop mechanics that remain useful;
- source-backed entity resolution primitives;
- full-collection/pagination fixes;
- exact task-key postcondition validation;
- compact authoritative observations;
- Browser C / Playwright harness;
- independent REAL AS21 Oracle B methodology.

## What changes in v4
Correctness must no longer depend on a mandatory semantic JSON pre-pass producing exact fields such as `person_raw`, `intent` or `semantic_contract`.

Target behavior:

```text
raw user query
 -> compact progressive skill catalog
 -> LLM planner
 -> typed capability CALL
 -> capability-level source-backed argument resolution
 -> deterministic execution
 -> validated observation
 -> re-plan as needed
 -> response synthesis
```

Skills are procedures/capability compositions, not phrase routers.

## Mandatory future benchmark
The first v4 task-family certification must include:

`Открытые задачи Гончарова в спринте OLP-SPRNT-5`

and equivalent cases using other real source identities/sprints, without hardcoded people or sprint IDs in production routing/prompt logic.

## 54-skill obligation
The full migration still requires no-skip A/B/C certification of all 54 production skills across applicable `WMB`, `STS`, `OLP`, `DMS`, `CRPV` spaces and authoritative team identities.

## STOP
Do not take further action until a new owner assignment is committed.