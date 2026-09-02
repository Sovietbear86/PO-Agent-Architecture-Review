# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_135_DEFECT_CLUSTER_FORENSIC`

## Mission
Assignment 134 produced useful 54/54 backend coverage, but its C leg was NOT real UI: the report explicitly substituted Harness/API calls for browser evidence. Do not rerun another broad marathon now. Assignment 135 is a **forensic localization job** whose only purpose is to turn every reproducible FAIL / ERROR / suspicious `COMPLETED+0` cluster into a proven first failing boundary before owner code changes.

You are QA/test executor only. **Do not modify production/backend/frontend code, prompts, skills, adapters, AS21 data, team config or test rules.** Commit/push QA evidence only under `po-agent-platform-v2/qa_reports/`.

Historical reports 132/133/134 are leads, not truth. Reproduce current behavior on fresh sessions and current HEAD.

---

# ABSOLUTE RULES

1. Do not infer root cause from response status alone.
2. `NEEDS_CLARIFICATION` is a symptom, not automatically `SPACE_GROUNDING`.
3. `ERROR: NoneType.get` is a symptom, not automatically `CAPABILITY_RESULT_PROPAGATION`.
4. `COMPLETED + 0` is never accepted as correct until independent REAL AS21 Oracle B proves zero.
5. Do not extrapolate one failing skill to "25+ affected" without reproducing representative paths and proving the shared boundary.
6. Do not use local DB/sync/fake/mock/frozen data as truth.
7. Oracle B must be independent REAL AS21/SWTR.
8. Use fresh unique session IDs for every independent case.
9. Current production NL path must expose whether LLM-first was actually used; record interpreter class and `llm_used` where available.
10. C/browser is NOT part of the primary forensic in this assignment. Do not claim UI certification. We will run a dedicated real-browser gate after owner fixes.
11. Do not stop after finding the first defect. Complete all required clusters below.
12. Final report must contain source-level evidence sufficient for owner to change code without guessing.

Approved spaces: `WMB`, `STS`, `OLP`, `DMS`, `CRPV`.
Timeouts: normal 180s, heavy 300s, concurrency=1, transient retry up to 2 with 30s backoff.

---

# PHASE 0 — provenance and controls

1. Pull `feat/core8-real-query-hardening-v2` and record exact HEAD + `git status --porcelain`.
2. Hard restart Task API and Harness from HEAD; record PIDs/start commands/timestamps.
3. Verify REAL AS21/MCP-SWTR health with at least two direct reads from different approved spaces.
4. Run fresh control A/B pairs:
   - `Задачи Гаранина`;
   - `Задачи Гаранина в DMS`;
   - `Задачи Калачанова`;
   - exact known-good task `DMS-380` if still present; otherwise choose a freshly proven real task.
5. For each control capture exact task-key equality and do not reuse results from Assignment 134.

The report must explicitly resolve any contradiction where the same query is claimed both PASS and FAIL in previous reports.

---

# CLUSTER A — NEEDS_CLARIFICATION / entity grounding forensic

Goal: determine whether the broad clarification pattern is really space grounding, missing sprint/release entity, semantic misclassification, or capability-specific requirements.

Run these fresh cases with independent sessions:

### A1 task search controls
- `Задачи Гаранина в DMS`
- `Задачи в WMB`
- `Задачи в работе`

### A2 sprint paths
Use validated existing sprint IDs from the current source. Do NOT use bare `STS` as a fake sprint.
- sprint scope on a real sprint;
- sprint velocity on a real sprint;
- sprint WIP on a real sprint;
- one intentionally underspecified query such as `Скоуп спринта STS` to prove what clarification is legitimately required.

### A3 release paths
First discover/validate a real release/version entity via the production source contract. Then test:
- release health with the real release identifier;
- release progress with the real release identifier;
- one intentionally underspecified `Состояние релиза WMB` case.

For EVERY case capture this exact chain:

```text
USER_QUERY
INTERPRETER_CLASS
LLM_USED
RAW_SEMANTIC_FRAME
DIALOGUE_ACT
GROUNDED_FRAME
UNRESOLVED_ENTITIES / CLARIFICATION_REASON
RESOLVED_SKILL
CAPABILITY_ARGS
SOURCE_ROUTE
SOURCE_RESULT
FINAL_STATUS
```

Then identify the first artifact that is wrong relative to the user intent and source contract.

Critical question to answer: **Are approved spaces actually failing grounding, or were previous queries missing a required sprint/release entity and therefore correctly clarified?**

No `SPACE_GROUNDING` verdict is allowed without evidence that raw semantic frame contains the correct space, the space should be sufficient for that skill contract, and the grounder incorrectly rejects/loses it.

---

# CLUSTER B — AttributeError / NoneType.get forensic

Freshly reproduce EACH of these reported error paths if still reproducible:
- `task-search-assignee` with `Задачи Гаранина`;
- `task-missing-requirements` with a valid query/source scope;
- `team-competency-match` using a real configured member/team context;
- additionally retest prior historical suspects `task-quality`, `velocity`, `sprint-wip` to determine whether they belong to the same defect or were previous QA artifacts.

For each reproduced ERROR collect the complete Python traceback and trace the value across:

```text
semantic frame
 -> grounded frame
 -> selected skill
 -> capability args
 -> capability return object
 -> normalization/result propagation
 -> response rendering
```

You MUST record:
- exact file path;
- function/method;
- exact failing expression;
- object that is `None`;
- why that object can be `None` on this valid production path;
- last correct typed object before corruption/loss.

Do not write "missing null check" unless the evidence proves that `None` is a legitimate optional value. If `None` is caused by an upstream routing/contract defect, classify the upstream boundary instead.

Output one boundary per distinct root cause. If three skills share the same root cause, prove the shared call chain. If not, split them into separate defect clusters.

---

# CLUSTER C — suspicious COMPLETED + zero / exact-task semantics

Recheck these with fresh independent Oracle B:

1. `Покажи задачу <fresh real exact ID>`
2. `Сводка по <same exact ID>`
3. `Похожие задачи <same exact ID>` where applicable
4. `Анализ приемки <same exact ID>` where applicable
5. attachment/file search skills using a query/entity for which Oracle B can actually prove at least one result, if such data exist

For exact task lookup/summary, if B proves the task exists, capture whether A structured data includes that exact key even if a generic `tasks` count field is zero. Distinguish:
- response-schema interpretation problem;
- missing task propagation;
- formatter-only issue;
- genuine capability failure.

Also retest one guaranteed nonexistent task while source health is independently proven. Determine whether the first bad boundary is Task API status mapping, adapter decoding, Harness exception mapping, or response rendering.

Do not accept `AS21 unavailable` for a healthy-source authoritative NOT_FOUND if the source contract exposes that distinction.

---

# CLUSTER D — skill resolution ambiguity / duplicate semantic paths

Assignment 134 showed ordinary `task-search` could answer `Задачи Гаранина` while explicit `task-search-assignee` reportedly errored for the same user wording.

Prove how these skills are actually selected and invoked.

Test at least:
- `Задачи Гаранина`
- `Найди задачи, назначенные Гаранину`
- `Задачи Гаранина в DMS`

Capture raw semantic intent, resolved production skill/capability and final source route.

Answer explicitly:
- Is `task-search-assignee` a separately callable production semantic skill, an internal/catalog capability, or an artificial QA-forced path?
- Did Assignment 134 truly exercise natural production routing for every catalog entry, or did its runner force skill labels that the user-facing resolver would not select?
- Are any of the 54 "skills" aliases/internal variants that require different acceptance semantics?

If the QA runner itself forced an invalid path, classify `QA_HARNESS_ORACLE_DEFECT` / `QA_RUNNER_DEFECT`, not product defect.

---

# CLUSTER E — source capability vs product defect

For sprint history/carryover/scope-change, release forecast, history/time-in-status and similar skills, explicitly verify whether REAL AS21 currently exposes the necessary historical fields.

Classify each relevant behavior as exactly one of:
- `PRODUCT_DEFECT`
- `SOURCE_CAPABILITY_UNAVAILABLE_BY_DESIGN`
- `SOURCE_DATA_MISSING`
- `ORACLE_NOT_PROVEN`
- `QA_RUNNER_DEFECT`

Do not reconstruct historical truth from current task membership or local cache.

---

# PHASE 6 — cross-cluster root-cause consolidation

After all evidence is collected, group failures by **actual first failing boundary**, not by visible status.

For each final defect cluster provide:

```text
CLUSTER_ID
REPRO_QUERIES
AFFECTED_PRODUCTION_SKILLS
REPRO_COUNT
LAST_CORRECT_ARTIFACT
FIRST_INCORRECT_ARTIFACT
FIRST_FAILING_BOUNDARY
EXACT_FILE
EXACT_FUNCTION
EXACT_CODE_REGION / EXPRESSION
WHY IT FAILS
MINIMAL OWNER FIX SCOPE
PROTECTED REGRESSIONS
```

`MINIMAL OWNER FIX SCOPE` is guidance only. Do not modify code.

Protected regressions must include at least:
- Garanin generic exact-key 16-current-oracle parity;
- Garanin DMS current-oracle parity;
- Kalachanov current-oracle parity;
- exact task lookup;
- second approved space;
- Russian response;
- session isolation/correction unaffected.

---

# PHASE 7 — LLM-first verification

For at least 10 representative cases across task/sprint/team/release/PO domains, prove:
- actual interpreter class;
- `llm_used=true` where production LLM path is expected;
- raw semantic frame is model-produced;
- deterministic grounding follows the LLM frame;
- no silent heuristic interpreter has taken over ordinary production NL.

If telemetry is insufficient, classify `OBSERVABILITY_GAP` and identify exactly what is missing. Do not infer LLM usage from a correct answer.

---

# FINAL REPORT

Write:
`po-agent-platform-v2/qa_reports/DEFECT_CLUSTER_FORENSIC_135.md`

Optional raw evidence prefix:
`DEFECT_CLUSTER_FORENSIC_135_`

Mandatory summary table:

| Cluster | Symptom | Reproduced? | True affected skills | First failing boundary | Exact file/function | Product vs QA/source | Owner fix ready? |

Also include a **134 corrections section** stating which Assignment 134 claims are:
- CONFIRMED;
- NARROWED;
- DISPROVEN;
- QA-RUNNER-CAUSED;
- SOURCE-LIMITATION.

Final allowed verdicts:
- `DEFECT_BOUNDARIES_PROVEN_OWNER_FIX_READY`
- `MIXED_PRODUCT_QA_SOURCE_BOUNDARIES_PROVEN`
- `MORE_FORENSIC_REQUIRED`
- `BLOCKED_BY_ENVIRONMENT`

Do not use a broad FULL/GREEN verdict. This is a localization assignment.

## Finish
Commit/push ONLY QA report/raw forensic evidence. Return report path, full SHA, exact number of proven product defect clusters, QA-runner defects, source limitations, and STOP.

## Start now
Execute Assignment 135 autonomously and do not modify production code.