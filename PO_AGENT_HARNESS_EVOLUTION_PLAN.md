# PO Agent Harness — Authoritative Evolution Plan

**Status:** ACTIVE / consolidated source of truth  
**Current branch:** `feat/core8-real-query-hardening-v2`  
**Last reviewed:** 2026-08-27  
**Current active gate:** Assignment 095 — total real-agent regression + per-skill learning-loop certification  
**Purpose:** preserve the original PO Agent behavior while evolving it into a source-grounded, self-improving Harness with controlled persistent learning.

> This document is the execution roadmap. Historical QA reports remain evidence, but the current runtime and current regression results outrank historical GREEN. GigaCode remains QA-only unless the owner explicitly changes that rule.

## 0. Non-negotiable principles

1. Preserve the product behavior of the original PO Agent.
2. The complete production skill catalog must be discovered from the running registry; do not rely on a manually remembered skill count. Historical target remains 48 original requirements plus 6 reconciled additions.
3. AS21/SWTR business facts must be validated against real read-only source data. Fixtures are allowed only for controlled fault injection, never as acceptance evidence for source facts.
4. GigaCode is tester/adversarial reviewer. Production code changes are made on the ChatGPT/OpenAI side.
5. Deterministic retrieval, filtering and calculation stay in code. LLM interprets, clarifies and synthesizes; it must not invent AS21 facts or deterministic metrics.
6. A successful HTTP response is not proof of semantic correctness. Requested filters must survive semantic interpretation, grounding, capability arguments and final source validation.
7. Exact task-key-set equality against an independent authoritative oracle outranks answer prose and count-only checks.
8. Exact task-key lookup must use the authoritative point-read path and must not depend on a bounded `/api/v1/tasks` cache.
9. Historical GREEN is a baseline, not permanent acceptance. A later source-backed counterexample reopens the affected gate.
10. Every production skill must pass both functional regression and learning-loop regression before backend acceptance is complete.
11. Learning must generalize behavior, not memorize entities, task IDs, sprint IDs, answers or user-provided source facts.
12. Learned behavior may only come from an allow-listed policy type and must be versioned, auditable, restart-safe and rollbackable.
13. A user correction never overrides contradictory authoritative SWTR evidence.
14. Runtime learning must not rewrite Python, prompts, Skill Catalog definitions or AS21 source data.
15. Any regression in an already-green skill blocks backend certification.
16. Frontend finalization and full browser E2E happen only after backend functional + learning certification is GREEN.
17. No AS21 write authority is permitted during acceptance.

## 1. Current target evolution

```text
Original PO Agent / legacy behavior
        |
        v
AS21/SWTR source contract + Core-8 hardening
        |
        v
Exact-key / sprint / multi-filter / history hardening
        |
        v
Persistent controlled Learning Loop
        |
        v
TOTAL REGRESSION OF EVERY PRODUCTION SKILL
(functional + real source + evidence + NL variants)
        |
        v
PER-SKILL LEARNING CERTIFICATION
(correction -> source recheck -> generalized policy -> persistence -> restart -> rollback)
        |
        v
Backend catalog certification / Gate E closure
        |
        v
Frontend / PO Workspace acceptance
        |
        v
Full browser E2E
        |
        v
Release hardening and release readiness
```

## 2. Phase gates

### GATE A — AS21 Source Contract

Required source capabilities include task point read, task search, task relations, sprint membership, project/space, assignee, status, release, attachments and history/changelog where required by active skills.

The critical rule is authoritative hydration: facade/list endpoints may provide candidate keys, but task facts used for acceptance must come from the real authoritative unit/read path where available.

**Status:** historically GREEN, but individual source facts may be reopened by current regression. Exact-key direct lookup and history are explicitly rechecked in Assignment 095.

### GATE B — Core-8 and semantic/source boundary

Canonical eight domain skills remain:

1. `task_search`
2. `task_summary`
3. `task_quality`
4. `sprint_health`
5. `velocity`
6. `team_workload`
7. `competency_match`
8. `release_health`

Historical Core-8 GREEN is preserved as a baseline only. Current acceptance comes from total regression, not from historical runs.

### GATE C — Controlled persistent Learning Loop

The learning design now has two layers:

**Governance layer:** candidate/evaluation/promotion lifecycle with technical gates, human approval and rollback.

**Runtime behavioral layer:** explicit negative feedback can trigger a fresh authoritative source recheck and, only after a source-grounded correction, create an allow-listed generalized persistent learned policy for the affected skill.

Implemented production milestones:

- `f6e36ea` — persistent versioned `LearnedPolicyStore`;
- `d53124a` — correction runtime integration with persistent learning.

Expected learned behavior currently allowed:

```text
authoritative_recheck_on_negative
```

Forbidden learned artifacts include concrete truths such as `DMS-271 exists`, stored answers, sprint membership facts, assignee facts or arbitrary prompt/code mutations.

**New exit criterion:** Gate C is no longer considered fully release-certified from two representative skills only. Before release, every callable production skill must pass the applicable per-skill learning contract or explicitly prove that the learning behavior is safely non-applicable under the production policy. Assignment 095 is the certification gate.

### GATE D — Historical requirement recovery

`PO_AGENT_48_SKILL_MATRIX.md` accounts for the original 48 requirements and six reconciled additions.

**Status:** GREEN as requirement-recovery inventory.

### GATE E — Complete backend skill acceptance

Gate E is no longer accepted wave-by-wave only on implementation presence. The final backend acceptance rule is:

```text
EVERY DISCOVERED PRODUCTION SKILL
= functional GREEN
+ correct REAL source behavior where applicable
+ grounded evidence
+ natural-language variants
+ learning-loop certification
+ restart survival
+ rollback
```

Assignment 095 is the first total certification run against this rule.

**Exit criterion:** `FULLY_CERTIFIED` with zero functional RED and zero learning RED across the complete runtime skill catalog.

### GATE F — Frontend / PO Workspace

After Gate E closes, recover the original screen scope and compare it with the current frontend screen by screen. Required areas include conversational workspace, clarification UX, task search/results/detail, sprint/flow analytics, team/capacity/competency, release/product analytics, evidence/trace, feedback/learning controls, loading/empty/error/partial states and AI-PDLC lifecycle surfaces.

### GATE G — Full browser E2E

Exercise the actual production chain:

```text
Frontend -> API -> Orchestrator -> semantic interpretation/context
 -> Skill Resolver -> deterministic capability -> AS21/SWTR
 -> evidence/trace -> response -> UI -> feedback/learning path
```

Critical cases include clarification/resume, session isolation, source unavailable, LLM unavailable fail-closed behavior, empty results, exact-key task lookup, sprint/release selection, attachments/history, feedback capture, persistent learning, restart survival, rollback and zero AS21 mutation authority.

## 3. Learning-loop release contract

For each production skill where feedback learning is applicable, certify:

```text
initial execution
 -> explicit user negative feedback/correction
 -> fresh authoritative source validation
 -> generalized allow-listed behavioral policy
 -> persistent policy record with skill_id/version/audit
 -> different query/entity benefits
 -> cold process restart
 -> policy reloads and still applies
 -> rollback
 -> policy no longer applies
```

Required safety properties:

- no entity memorization;
- no answer memorization;
- no source-fact fabrication;
- no direct code/prompt/catalog mutation;
- no policy promotion from unsupported user assertion;
- no persistence of contradictory facts;
- malformed policy store fails safely;
- repeated identical correction does not create unbounded duplicate active policies;
- rollback removes the policy from active resolution.

## 4. Current production milestones

Verified important production changes in the current hardening line include:

- source-backed sprint membership and multi-filter preservation;
- MCP-SWTR stdio transport recovery and fail-closed source error handling;
- authoritative direct exact-key task lookup, including the historical DMS-271 class of failures;
- correction-aware fresh source recheck;
- controlled lifecycle for improvement candidates/evaluation/promotion/rollback;
- persistent versioned learned policy store;
- correction runtime integration that can apply a generalized learned behavior in future requests.

Historical assignments 030-049 remain diagnostic evidence for the sprint/oracle recovery path. Subsequent hardening supersedes the old roadmap state that was blocked on manual SWTR access. The active gate is now the complete Assignment 095 regression.

## 5. Assignment 095 — active total certification gate

Assignment 095 must dynamically enumerate every production skill from the running registry and produce one certification row per skill.

It includes:

- clean runtime provenance and REAL AS21 mode;
- total functional black-box regression;
- canonical Russian query plus paraphrase variants;
- critical historical exact-key, sprint, multi-filter and history regressions;
- complete Sprint Intelligence and Team Workload rechecks;
- per-skill learning trigger, source revalidation and persistent policy evidence;
- cross-entity/query generalization;
- cold restart survival;
- idempotency/versioning/rollback;
- learning safety checks;
- the entire automated test suite;
- final complete skill certification matrix.

Final allowed verdicts:

```text
FULLY_CERTIFIED
REGRESSION_DETECTED
BLOCKED_BY_ENVIRONMENT
```

`FULLY_CERTIFIED` is allowed only when every production skill is functionally GREEN and every applicable learning-loop contract is GREEN.

## 6. Ordered next steps and estimated duration

Durations below are engineering elapsed-time estimates, not guarantees. REAL SWTR latency and the number of regressions found by 095 are the largest uncertainty.

| Step | Work | Expected duration | Exit |
|---|---|---:|---|
| 095 | Total real-agent regression + per-skill learning certification | **1.5–3 h** | Full report with complete skill matrix |
| 096A | If 095 RED: diagnose the narrowest broken boundary, no broad refactor | **0.5–1.5 h per defect cluster** | Reproducible root cause + focused fix |
| 096B | Focused post-fix certification for affected skill/source boundary | **20–45 min per cluster** | Affected RED becomes GREEN without protected regressions |
| 097 | Final clean rerun of total 095-equivalent gate after all fixes | **1.5–3 h** | `FULLY_CERTIFIED` |
| 098 | Freeze backend certification artifacts, catalog/version matrix and release baseline | **30–60 min** | Backend/Gate E formally closed |
| 099 | Frontend screen-level gap/acceptance audit against original PO Agent scope | **2–4 h** | Exact UI gap matrix |
| 100 | Frontend remediation if gaps exist | **0.5–2 working days** depending on gaps | Screen matrix GREEN |
| 101 | Full browser E2E including learning/feedback/restart/failure states | **3–6 h** | Critical E2E 100% GREEN |
| 102 | Release hardening: security/read-only checks, secrets, packaging, clean install/restart smoke | **2–4 h** | Release candidate |
| 103 | Final release-readiness certification | **1–2 h** | `RELEASE_READY=YES` |

### Best-case path

If Assignment 095 is immediately `FULLY_CERTIFIED`, backend work is essentially complete. Remaining work is approximately:

```text
backend freeze          0.5–1 h
frontend audit          2–4 h
frontend fixes          0.5–2 working days, only if needed
full browser E2E        3–6 h
release hardening       2–4 h
final certification     1–2 h
```

Without meaningful frontend defects, the project can reach release-candidate quality in roughly **1 working day after 095**. With moderate frontend remediation, plan on **2–3 working days**.

### Expected path if 095 finds backend regressions

Do not restart the whole architecture campaign. Use this loop:

```text
095 RED
 -> classify each RED by narrow boundary
 -> fix one boundary
 -> focused certification
 -> protected regression
 -> repeat until zero RED
 -> one final total clean rerun
```

For one or two narrow backend defect clusters, add approximately **2–5 hours** before frontend work. If 095 exposes systemic learning-loop or source-contract failures across many skills, reserve **1–2 additional working days** before Gate E can close.

## 7. Decision rules after Assignment 095

### If `FULLY_CERTIFIED`

1. Do not keep polishing backend behavior without evidence.
2. Freeze backend skill/runtime versions and QA evidence.
3. Close Gate E.
4. Move directly to frontend screen audit and then browser E2E.

### If `REGRESSION_DETECTED`

1. GigaCode does not fix anything.
2. Read the complete skill matrix and group REDs by shared boundary.
3. Prefer one root-cause fix over per-skill patches.
4. Run a focused retest after each boundary fix.
5. After all focused gates are GREEN, rerun the complete total certification once from a clean process/state.

### If `BLOCKED_BY_ENVIRONMENT`

1. Separate source/environment failure from product failure.
2. Prove the failing external dependency independently where possible.
3. Do not replace REAL source evidence with fake/mock data.
4. Resume the same gate after the environment is restored.

## 8. Work ownership and Git QA handoff

### ChatGPT/OpenAI side

- architecture and production changes;
- source-contract and learning-policy decisions;
- QA assignment design;
- roadmap updates;
- diagnosis and fixes after QA reports;
- acceptance/release decisions.

### GigaCode side

- QA only;
- pull current branch and restart real services;
- use real read-only source data where required;
- run the complete active assignment autonomously;
- never weaken tests or acceptance rules;
- never modify production code/prompts/fixtures/learning implementation;
- commit/push only the explicitly allowed QA report;
- stop after the report and return SHA + full report.

## 9. Current gate values

```text
GATE_A_SOURCE_CONTRACT = HISTORICAL_GREEN / CURRENTLY_REVALIDATED_BY_095
GATE_B_CORE8 = HISTORICAL_GREEN / CURRENTLY_REVALIDATED_BY_095
GATE_C_LEARNING_FOUNDATION = IMPLEMENTED
GATE_C_PER_SKILL_RELEASE_CERTIFICATION = PENDING_095
GATE_D_REQUIREMENT_RECOVERY = GREEN
CATALOG_IMPLEMENTATION = 48_ORIGINAL + 6_RECONCILED / RUNTIME_DISCOVERY_AUTHORITATIVE
GATE_E_BACKEND_ACCEPTANCE = PENDING_095
FRONTEND_FINALIZATION = DEFERRED_UNTIL_GATE_E_GREEN
FULL_BROWSER_E2E = NOT_STARTED
RELEASE_READY = NO
CURRENT_NEXT_ACTION = RUN_ASSIGNMENT_095
```

## 10. Definition of Done

The product is release-ready only when:

- every production skill is functionally certified;
- every applicable skill passes the persistent learning-loop contract;
- real AS21/SWTR source contracts are grounded and fail closed;
- exact-key, sprint, multi-filter, attachment and history paths are proven;
- no entity/answer memorization occurs;
- learned policies survive restart and support rollback;
- human approval/governance boundaries remain intact where promotion requires them;
- frontend original product scope is restored/accepted;
- critical browser E2E is 100% GREEN;
- P0 defects = 0;
- unauthorized AS21 writes = 0;
- secret leakage = 0;
- final release-readiness gate = GREEN.

---

**Next action:** run Assignment 095 from a clean current checkout and use its complete skill-by-skill functional + learning matrix as the single backend acceptance truth. Do not begin frontend finalization until Assignment 095 (or its final clean rerun after fixes) returns `FULLY_CERTIFIED`.
