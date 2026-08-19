# PO Agent Harness Evolution Plan — Status Amendment 013

**Date:** 2026-08-19  
**Applies to:** `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`  
**Branch:** `feat/learning-loop-013-v1`

This amendment updates the execution-status portion of the authoritative plan without replacing its architectural rules, gates, Core-8 matrix, AS21 policy, ownership rules, or final Definition of Done.

## Verified gates

- [x] **Gate A — AS21 Source Contract GREEN.** Exact task lookup, assignee/project/status/sprint/release facts, attachments, pagination and read-only boundary have been exercised against real AS21 through the accepted Core-8 campaign.
- [x] **Gate B — Eight Core Skills GREEN on real AS21.** `task_search`, `task_summary`, `task_quality`, `sprint_health`, `velocity`, `team_workload`, `competency_match`, `release_health` = 8/8 production E2E.
- [x] **Gate C foundation / Learning Loop 012.** Controlled baseline-vs-candidate gate, false-green rejection, insufficient-evidence rejection, immutable evidence artifact and human approval boundary are independently QA-verified. Core-8 remains 8/8; no automatic SkillRegistry or AS21 mutation.

## Current step

### C1 — measurable self-improvement on `task_search` — CURRENT (Learning Loop 013)

Required chain:

```text
real/reproducible task_search failure or controlled weak baseline
  -> classified failure evidence
  -> deterministic failure cluster
  -> automatically synthesized bounded candidate proposal
  -> isolated candidate sandbox/evaluator
  -> identical frozen corpus for baseline and candidate
  -> shadow comparison
  -> measurable target improvement
  -> protected false-green/regression gates
  -> RECOMMEND only
  -> human approval boundary preserved
```

013 must not edit production behavior automatically. Source-contract/adapter failures are never converted into prompt/router learning patches; they remain source-contract review items.

**C1 exit criterion:** candidate improves the intended `task_search` metric on the identical frozen corpus, Core-8 remains 8/8, false-green/protected regressions stay GREEN, production mutations = 0, and automatic promotion = 0.

## Next steps after 013

### C2 — analytical skill learning + rollback
Use `sprint_health` as the second representative core skill. Demonstrate a bounded improvement, shadow comparison, human-approved candidate lifecycle in an isolated registry, then exercise rollback and prove previous active version restoration. Completing C1 + C2 closes **Gate C — Learning Loop GREEN** from the authoritative plan.

### Gate D — recover and freeze exact original 48-skill catalog
Do not expand skills before Gate C closes. Produce `PO_AGENT_48_SKILL_MATRIX.md` from earliest specifications/commits and account for exactly 48 original requirements.

### Gate E — expand 8 -> 48 in controlled waves
Then Gate F frontend screen finalization, then Gate G full browser E2E/release readiness.

## Plan conformance conclusion

Current work is in the planned order:

`Gate A -> Gate B 8/8 -> Gate C controlled loop 012 -> C1 task_search 013 -> C2 analytical skill/rollback -> Gate D 48 skills -> Gate E expansion -> frontend -> browser E2E`.

The old `Current execution status` block in the base plan still names A3 as current and is historically stale. This amendment is the current status override until that block is consolidated in a later documentation cleanup. No architectural sequencing rule from the base plan is changed.
