# PO Agent v3 — Hermes Alignment Audit

**Date:** 2026-09-10  
**Status:** architecture delta audit after Assignment 174 / before H1B closure  
**Goal:** verify that the PO Agent evolution keeps the important Hermes Agent patterns while preserving stricter enterprise/source-truth guarantees.

## Executive conclusion

The current v3 direction is still correct. We have not accidentally rebuilt the old Harness under a new name: H1B now has a bounded tool/capability loop, typed CALL/FINAL decisions, a capability registry, source-backed grounding, immutable constraints, postcondition validation, exact-source evidence, browser acceptance, and a strangler seam. Those are all compatible with the Hermes style of tool-using agent architecture.

However, we have **not yet implemented the parts that make Hermes feel like a self-improving general agent**. The largest remaining deltas are progressive skill loading, procedural skill persistence/versioning, an isolated learning reviewer, cross-session recall, deterministic family routing, and final retirement of legacy skill selection. Those are intentionally scheduled after H1B, not missing by accident.

PO Agent must also remain stricter than Hermes in one area: factual business truth. Skills/memory may store procedures, preferences and learned policy, but live task facts must always come from REAL AS21 and pass postconditions/Oracle certification.

## What Hermes does that matters for us

From current Hermes documentation/source:

1. **Tool-calling agent loop** — the model reasons, selects tools, observes results and continues until a final answer.
2. **Skills as procedural memory** — reusable task procedures can be created/updated and loaded later.
3. **Progressive/on-demand skill use** — the agent does not need every full skill instruction in every prompt; compact skill metadata can lead to loading the selected skill.
4. **Persistent bounded memory** — curated memory survives across sessions; session history can be searched on demand rather than injected wholesale.
5. **Learning loop** — experience/corrections can be distilled into reusable skills/memory rather than only patching one conversation.
6. **Tool registry/toolsets** — capabilities are explicit and extensible rather than buried in prompt wording.
7. **Provider independence** — model/provider can change without rewriting the agent architecture.
8. **Multiple surfaces over one core** — CLI/UI/messaging surfaces share the same agent core rather than having independent semantics.
9. **Isolation/profiles** — persistent state must have explicit scope; different sessions/agents must not accidentally contaminate each other.
10. **Delegation only where useful** — subagents are tools for genuinely separable work, not the default path for simple factual requests.

## Current PO Agent v3 alignment

| Hermes pattern | PO Agent status | Assessment |
|---|---|---|
| Bounded plan/execute/observe/final loop | H1B implemented | **Aligned** |
| Typed tool/capability invocation | Typed CALL/FINAL + Capability Registry | **Aligned** |
| Tool registry | Capability Registry v1 | **Aligned foundation** |
| Ground external identifiers before execution | ProductionEntityResolverV2 | **Stricter than Hermes / correct** |
| Immutable accepted constraints | AcceptedTurnContract | **Stricter and required** |
| Result validation before user output | ResultPostconditionValidator | **Stricter and required** |
| Provider independence | LLM client/model configured externally | **Mostly aligned** |
| Same core for UI/API | v3 path + Browser C certification | **Partially aligned; legacy seam remains** |
| Progressive skill loading | Not yet implemented | **H1C/H3 gap** |
| Procedural skill files/versioning | Registry exists; self-authored procedural skill lifecycle not yet present | **H3/H4 gap** |
| Persistent memory separated from session state | conversation/runtime/memory scopes designed | **Foundation exists; full runtime behavior pending** |
| Session search / long-history recall | Not yet implemented as a first-class agent capability | **Gap** |
| Autonomous learning from corrections | Current legacy correction loop insufficient; Learning Reviewer planned | **H4 gap** |
| Skill write approval/version/rollback | Planned governance | **H4 gap** |
| Multi-agent delegation | Not yet needed for task vertical | **Intentionally deferred** |
| Family-wide deterministic routing | H1B selector/legacy seam still inconsistent by wording/name | **Major H1C gap** |
| Full catalog certification | 54-skill no-skip stage still pending | **H6 mandatory** |
| Full UI data wiring | dashboard has unexplained empty values | **H7 mandatory** |

## Important architecture correction: do not copy Hermes blindly

Hermes is a general autonomous agent. PO Agent operates over enterprise business systems and therefore needs guarantees that a general desktop agent does not necessarily enforce for every answer.

The following PO Agent invariants stay mandatory even if Hermes itself is looser:

- REAL AS21/MCP-SWTR is authoritative for task facts.
- learned memory/skills cannot become the source of current task counts/statuses/owners;
- exact task-key parity outranks plausible prose;
- explicit constraints survive the whole turn unchanged unless canonically normalized;
- unsupported or ambiguous constraints fail closed;
- source unavailable is not an empty result;
- every migrated skill family must pass Agent A vs independent Oracle B vs Browser C;
- learning candidates must be validated before promotion and must be rollbackable.

## What we were at risk of missing

### 1. We still have two semantic control planes

The biggest current architectural smell is not H1B itself, but coexistence of H1B selection with legacy routing. Equivalent task requests can still take different paths based on wording/person. This is why the UI can look inconsistent even when focused H1B tests are green.

**Action:** H1C/H3 must replace surname/phrase pilot selection with capability-family selection from compact registry metadata. The model selects among task-family capabilities; deterministic grounding validates entities; no surname list determines whether v3 is used.

### 2. Progressive skill loading must be real, not a renamed registry

A registry alone is not Hermes-style progressive skills. H1C must introduce two levels:

```text
Level 0: compact catalog metadata
  id / family / description / supported constraints / source / cost

Level 1: selected skill procedure
  detailed instructions / examples / validation / executor binding / failure semantics
```

Only shortlisted skills should load their full procedure. The 54 skills must not all be injected into every semantic/planner call.

### 3. Learning must modify procedure, not business truth

Hermes' value comes from skills that improve from experience. Our current correction runtime mostly rechecks and asks the user what is wrong. That is not enough.

Target Learning Reviewer:

```text
negative feedback
 -> immutable previous-turn snapshot
 -> fresh independent source recheck
 -> compare expected vs delivered facts/constraints
 -> locate failing boundary
 -> propose generalized procedure/policy change
 -> replay against regression corpus + Oracle
 -> approval/promotion
 -> versioned skill/policy
 -> rollback metadata
```

The learned artifact may say "for assignee collections preserve explicit space through execution". It may never say "Garanin has 23 tasks".

### 4. Memory and session history are different things

Hermes deliberately separates small curated persistent memory from searchable session history. PO Agent should do the same conceptually:

- `runtime_session_id` = transient dialogue state;
- `conversation_id` = visible chat lineage;
- `memory_scope_id` = durable procedural/user context;
- historical chats/evidence = searchable store, loaded only on demand.

Do not inject full prior histories into every prompt and do not let memory_scope resurrect correction state from another conversation.

### 5. Response synthesis should ultimately be separate from planning

H1B currently allows the same planner to emit FINAL. This is acceptable for H1B, but Assignment 167/168 already showed that large observations can destabilize final generation. Long-term cleaner architecture:

```text
Planner: CALL or DONE
Executor/validator: authoritative structured result
Response synthesizer: compact user-facing answer from validated result
```

The planner should not need full task descriptions merely to decide that work is complete. This reduces token pressure and model-provider sensitivity.

### 6. Tool observations need bounded structured views

Hermes relies on tools but cannot safely stuff unlimited raw output back into context. We already started compact observations. Continue this in H1C/H3:

- planner sees compact keys/counts/essential attributes;
- detailed rows remain in structured result/evidence store;
- synthesizer can retrieve/detail only what it needs;
- no silent truncation of authoritative result sets.

### 7. Provider quirks must not leak into architecture

Qwen response-format and JSON truncation incidents proved this. Provider adapters may normalize transport quirks, but capability contracts and planner protocol must remain model-neutral. Keep typed protocol and bounded repair at the provider boundary.

### 8. We need an explicit skill lifecycle

Before calling the system self-improving, each procedural skill/policy needs:

```yaml
id:
version:
family:
source_authority:
procedure:
executor_binding:
validation_contract:
created_from_evidence:
certification_sha:
status: candidate|active|retired
rollback_to:
```

Learning Reviewer creates **candidate** versions. Main runtime only consumes **active/certified** versions.

### 9. 54-skill certification remains a release requirement

The H1/H3 pilot is not a substitute for the full catalog. For every production user-facing skill in spaces `WMB`, `STS`, `OLP`, `DMS`, `CRPV` and relevant team members:

- discover actual skill/capability contract;
- classify whether the live source can authoritatively support it;
- test Agent A;
- independently query Oracle B;
- test Browser C where user-facing;
- compare normalized facts and exact key sets;
- source-unavailable capabilities get an explicit typed classification, never fabricated GREEN;
- no case is skipped because a marathon timed out.

### 10. UI must become a first-class agent surface

Hermes uses one agent core across surfaces. For PO Agent, H7 must eliminate UI-local truth and unexplained placeholders. Every widget/action must map to a certified capability/source path and expose real state (`LOADING`, `REAL_EMPTY`, `SOURCE_UNAVAILABLE`, etc.).

## Refined remaining architecture sequence

### H1B — close factual task-loop correctness
Current blocker only: compound-query clarification reconciliation / route fidelity. No further surname-specific patches after certification.

### H1C / H3A — Progressive Skill Loading + deterministic family cutover
- remove pilot surname selector as the governing route;
- compact catalog shortlist;
- lazy-load selected procedural contracts;
- task family uniformly routes through v3;
- preserve one-shot path for simple factual queries;
- keep multi-step loop only when a second tool call is genuinely required.

### H3B — Executor consolidation
- task executor family first;
- sprint/team/release families next;
- source capability availability explicit;
- planner never implements business calculations.

### H4 — Learning Reviewer + skill lifecycle
- independent feedback reviewer;
- mismatch proof;
- generalized candidate skill/policy;
- replay/A-B validation;
- version/promotion/rollback;
- durable procedural memory;
- searchable session/evidence history on demand.

### H5 — Strangler family migration
Retire legacy family-by-family only after A/B/C certification.

### H6 — Full 54-skill certification
No-skip catalog matrix across allowed spaces/team members, including unsupported-source classification where necessary.

### H7 — Full UI/data-lineage remediation
Zero unexplained empty/zero widgets; every UI value maps to new Agent Core/source truth.

### H8 — Release hardening
Latency, provider failure modes, restart/recovery, security/read-only guarantees, packaging and release certification.

## Final verdict

**Direction: KEEP. Full rewrite to stock Hermes: NO. Continue Hermes-inspired re-architecture: YES.**

We preserved the correct enterprise-specific pieces and have already replaced the most dangerous old Harness behavior with a bounded, contract-driven loop. The remaining work is exactly the part that will make the agent *feel* like Hermes rather than merely execute correctly: progressive procedural skills, unified routing, isolated learning, durable procedural memory and family-wide migration.

The next architecture stage after H1B certification must therefore be H1C/H3 Progressive Skill Loading, followed by Learning Reviewer. Do not spend another cycle broadly patching legacy semantic routing.