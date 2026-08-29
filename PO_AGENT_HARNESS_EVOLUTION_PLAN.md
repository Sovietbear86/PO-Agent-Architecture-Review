# PO Agent Harness — Authoritative Evolution Plan

**Status:** ACTIVE / consolidated source of truth  
**Current branch:** `feat/core8-real-query-hardening-v2`  
**Last reviewed:** 2026-08-29  
**Current active gate:** Assignment 072 — production semantic-correction boundary localization; owner fix follows only after QA evidence  
**Next major certification gate:** Assignment 095 — total real-agent regression + per-skill learning-loop certification  
**Purpose:** preserve the original PO Agent behavior while evolving it into a source-grounded, self-improving Harness with controlled persistent learning.

> This document is the execution roadmap. Historical QA reports remain evidence, but the current runtime and current regression results outrank historical GREEN. GigaCode is QA-only. Production code changes are owned by ChatGPT/OpenAI side after a defect boundary is proven.

## 0. Non-negotiable principles

1. Preserve the product behavior of the original PO Agent.
2. The complete production skill catalog must be discovered from the running registry; do not rely on a manually remembered skill count. Historical target remains 48 original requirements plus 6 reconciled additions.
3. AS21/SWTR business facts must be validated against real read-only source data. Fixtures are allowed only for controlled fault injection, never as acceptance evidence for source facts.
4. GigaCode is tester/adversarial reviewer only. It must not modify production code, prompts, fixtures or learning implementation. Production fixes are made on the ChatGPT/OpenAI side after QA evidence identifies the first failing boundary.
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
16. Any semantic-correction fix must preserve the complete learning loop. A fix that makes correction output correct but breaks authoritative recheck, policy promotion, persistence, generalization, restart survival or rollback is RED.
17. Frontend finalization and full browser E2E happen only after backend functional + learning certification is GREEN.
18. No AS21 write authority is permitted during acceptance.

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
CURRENT: semantic correction-state hardening (Assignment 072)
        |
        v
TOTAL REGRESSION OF EVERY PRODUCTION SKILL (Assignment 095)
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

**Status:** historically GREEN. Real AS21 remains mandatory evidence for current correction/regression work and will be revalidated comprehensively by Assignment 095.

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

Historical Core-8 GREEN is preserved as a baseline only. Assignment 071 proved semantic recovery defects A1/A2 and exposed a production correction-state corruption: correction can corrupt `member_login` and fail to replace stale `status_raw`. This reopens the affected semantic/correction boundary without invalidating unrelated historical GREEN.

**Current status:** LOCALLY REOPENED by Assignment 072 until the first failing correction boundary is proven, minimally fixed by the owner, and post-fix regression is GREEN.

### GATE C — Controlled persistent Learning Loop

The learning design has two layers:

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

**Protected regression rule for Assignment 072:** correction hardening must not disable or bypass the learning loop. After the owner fix, certification must explicitly prove:

```text
negative correction
 -> fresh authoritative recheck
 -> valid generalized policy candidate/promotion path
 -> persistent learned policy
 -> reuse on a different query/entity where applicable
 -> cold restart survival
 -> rollback
```

If correction state is fixed but this chain regresses, Assignment 072 remains RED and Gate C is reopened.

**Release exit criterion:** every callable production skill must pass the applicable per-skill learning contract or explicitly prove that learning is safely non-applicable under production policy. Assignment 095 remains the comprehensive certification gate after 072 closes.

### GATE D — Historical requirement recovery

`PO_AGENT_48_SKILL_MATRIX.md` accounts for the original 48 requirements and six reconciled additions.

**Status:** GREEN as requirement-recovery inventory.

### GATE E — Complete backend skill acceptance

Final backend acceptance remains:

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

Assignment 095 is the next total certification run after Assignment 072 correction hardening is closed.

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
- rollback removes the policy from active resolution;
- internal semantic rechecks must not accidentally corrupt conversation state;
- preventing correction-state contamination must not suppress the authoritative learning evidence path.

## 4. Current production milestones and active regression

Verified important production changes in the current hardening line include:

- source-backed sprint membership and multi-filter preservation;
- MCP-SWTR stdio transport recovery and fail-closed source error handling;
- authoritative direct exact-key task lookup, including the historical DMS-271 class of failures;
- correction-aware fresh source recheck;
- controlled lifecycle for improvement candidates/evaluation/promotion/rollback;
- persistent versioned learned policy store;
- correction runtime integration that can apply a generalized learned behavior in future requests;
- Assignment 071 semantic slot recovery fixes A1/A2 retained unless a regression is proven.

### Active regression — Assignment 072

Known production symptom from Assignment 071:

```text
initial:    Покажи задачи Гаранина в DMS со статусом todo
correction: Покажи задачи Гаранина в DMS со статусом in progress
```

Observed corruption included:

- `member_login` becoming the full correction query instead of the authoritative member login;
- `status_raw` remaining `todo` instead of being replaced by `in progress`.

Current QA task is boundary localization only. GigaCode must reproduce the defect and trace semantic state through interpretation, cached previous frame, dialogue classification, correction processing, grounding and pre-execution slots. It must identify `FIRST_FAILING_BOUNDARY` separately for identity and status.

GigaCode must not repair production code. After evidence is available, the owner makes the narrowest justified production fix. The post-fix test must include both correction-state regression and the protected learning-loop contract.

Historical assignments 030-049 remain diagnostic evidence for the sprint/oracle recovery path. Historical GREEN remains useful but does not override current production counterexamples.

## 5. Assignment 095 — next major total certification gate

Assignment 095 starts only after Assignment 072 closes GREEN.

It must dynamically enumerate every production skill from the running registry and produce one certification row per skill. It includes:

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

Durations are engineering elapsed-time estimates, not guarantees. REAL SWTR latency and regressions found by the total gate remain the largest uncertainty.

| Step | Work | Expected duration | Exit |
|---|---|---:|---|
| 072A | QA-only correction reproduction ×3 + A-I boundary trace | **30–60 min** | Proven `FIRST_FAILING_BOUNDARY`; no production changes |
| 072B | Owner diagnosis + minimal production correction fix | **20–45 min** | Narrow diff tied to proven boundary |
| 072C | QA post-fix correction trace ×3 + focused regression matrix + second member + REAL AS21 proof | **30–60 min** | Correction-state invariants GREEN |
| 072D | Protected Learning Loop certification after correction fix | **30–60 min** | Recheck/promotion/persistence/generalization/restart/rollback GREEN |
| 095 | Total real-agent regression + per-skill learning certification | **1.5–3 h** | Full report with complete skill matrix |
| 096A | If 095 RED: diagnose narrowest broken boundary, no broad refactor | **0.5–1.5 h per defect cluster** | Reproducible root cause + focused owner fix |
| 096B | Focused post-fix certification for affected skill/source boundary | **20–45 min per cluster** | Affected RED becomes GREEN without protected regressions |
| 097 | Final clean rerun of total 095-equivalent gate after all fixes | **1.5–3 h** | `FULLY_CERTIFIED` |
| 098 | Freeze backend certification artifacts, catalog/version matrix and release baseline | **30–60 min** | Backend/Gate E formally closed |
| 099 | Frontend screen-level gap/acceptance audit against original PO Agent scope | **2–4 h** | Exact UI gap matrix |
| 100 | Frontend remediation if gaps exist | **0.5–2 working days** depending on gaps | Screen matrix GREEN |
| 101 | Full browser E2E including learning/feedback/restart/failure states | **3–6 h** | Critical E2E 100% GREEN |
| 102 | Release hardening: security/read-only checks, secrets, packaging, clean install/restart smoke | **2–4 h** | Release candidate |
| 103 | Final release-readiness certification | **1–2 h** | `RELEASE_READY=YES` |

### Best-case path from current state

If 072 is a narrow correction-state defect and the owner fix preserves the learning loop, then 095 is immediately `FULLY_CERTIFIED`:

```text
072 closure             ~1.5–3 h
095 total certification  1.5–3 h
097/098 final rerun+freeze 2–4 h
frontend audit           2–4 h
frontend fixes           0.5–2 working days, only if needed
full browser E2E         3–6 h
release hardening        2–4 h
final certification      1–2 h
```

Without meaningful frontend defects, release-candidate quality remains plausible in roughly **1–2 working days after backend certification**. With moderate frontend remediation, plan on **2–3 working days**. If systemic learning/source failures are found, reserve additional time rather than weakening acceptance.

### Expected defect loop

Do not restart the architecture campaign. Use:

```text
QA proves first failing boundary
 -> owner fixes one boundary
 -> focused QA certification
 -> protected functional + learning regression
 -> repeat until zero RED
 -> one final total clean rerun
```

## 7. Decision rules

### During Assignment 072

1. GigaCode does not fix production code.
2. New defects are traced to the first failing boundary before any owner change.
3. Do not patch formatter/output to hide semantic corruption.
4. Do not hardcode member identities, task IDs, sprint IDs, query strings or unsupported status semantics.
5. Do not replace REAL AS21 evidence with fake/mock/frozen data.
6. Owner fix must be minimal and directly justified by trace evidence.
7. Post-fix certification must explicitly prove the Learning Loop remains intact.
8. Do not start Assignment 095 until 072 is GREEN.

### After Assignment 095

If `FULLY_CERTIFIED`: freeze backend evidence, close Gate E and move to frontend audit.

If `REGRESSION_DETECTED`: group REDs by shared boundary, owner fixes one boundary at a time, focused QA follows each fix, then rerun the complete total gate once.

If `BLOCKED_BY_ENVIRONMENT`: prove the external dependency failure independently where possible; never substitute fake source evidence; resume the same gate when the environment is restored.

## 8. Work ownership and Git QA handoff

### ChatGPT/OpenAI side

- architecture and production changes;
- source-contract and learning-policy decisions;
- QA assignment design;
- roadmap updates;
- diagnosis and fixes after QA reports;
- acceptance/release decisions.

### GigaCode side

- QA/tester only;
- pull current branch and restart real services;
- use real read-only source data where required;
- run the active assignment autonomously;
- collect traces and adversarial evidence;
- never weaken tests or acceptance rules;
- never modify production code/prompts/fixtures/learning implementation;
- commit/push only explicitly allowed QA artifacts;
- stop after the report and return SHA + report.

## 9. Current gate values

```text
GATE_A_SOURCE_CONTRACT = HISTORICAL_GREEN / REAL_SOURCE_REQUIRED_FOR_CURRENT_QA
GATE_B_CORE8 = HISTORICAL_GREEN / CORRECTION_BOUNDARY_LOCALLY_REOPENED_BY_072
GATE_C_LEARNING_FOUNDATION = IMPLEMENTED
GATE_C_CORRECTION_PROTECTED_REGRESSION = PENDING_072D
GATE_C_PER_SKILL_RELEASE_CERTIFICATION = PENDING_095
GATE_D_REQUIREMENT_RECOVERY = GREEN
CATALOG_IMPLEMENTATION = 48_ORIGINAL + 6_RECONCILED / RUNTIME_DISCOVERY_AUTHORITATIVE
GATE_E_BACKEND_ACCEPTANCE = BLOCKED_UNTIL_072_GREEN_THEN_095
FRONTEND_FINALIZATION = DEFERRED_UNTIL_GATE_E_GREEN
FULL_BROWSER_E2E = NOT_STARTED
RELEASE_READY = NO
CURRENT_NEXT_ACTION = ASSIGNMENT_072_QA_BOUNDARY_LOCALIZATION
NEXT_MAJOR_GATE = ASSIGNMENT_095
```

## 10. Definition of Done

The product is release-ready only when:

- every production skill is functionally certified;
- every applicable skill passes the persistent learning-loop contract;
- real AS21/SWTR source contracts are grounded and fail closed;
- exact-key, sprint, multi-filter, attachment and history paths are proven;
- semantic correction preserves prior valid constraints and replaces corrected constraints without state corruption;
- correction hardening does not break authoritative recheck or persistent learning;
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

**Current next action:** complete Assignment 072 QA boundary localization. After the report proves the first failing boundary, the owner makes the minimal production fix. Then run focused correction + protected Learning Loop certification. Only after Assignment 072 is GREEN proceed to Assignment 095 as the complete backend acceptance truth.