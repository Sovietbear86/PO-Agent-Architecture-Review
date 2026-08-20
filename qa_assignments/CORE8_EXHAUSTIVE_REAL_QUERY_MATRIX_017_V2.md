# CORE8 Exhaustive Real-Query Hardening Matrix 017 V2

## Status
This file is the **single canonical test entry point** for the Core-8 revalidation freeze. It supersedes running `CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017.md` and `CORE8_CORRECTION_LOOP_ADDENDUM_017A.md` separately.

The detailed query definitions remain authoritative in those two files, but this V2 defines the complete mandatory suite, execution order, oracle rules, known positive anchors, and final GREEN gate.

Gate E remains FROZEN until this suite is GREEN.

---

## 0. Mandatory oracle/source-contract preflight
Before judging any agent result, independently prove the source contract used by the oracle.

### O-01 Person grounding
For Garanin and Kalachanov, resolve canonical assignee identifiers from real AS21/SWTR and record the raw attribute path(s). Do not use display-name-only filtering as ground truth.

### O-02 Product/space grounding
Prove how DMS, OLP and WMB membership is represented in real AS21/SWTR. Do not assume `project == DMS`, `space == DMS`, or any other field until verified from raw source evidence.

### O-03 Sprint grounding
Prove how task-to-sprint membership is represented. Enumerate tasks in at least:
- `DMS-SPRNT-1`
- `DMS-SPRNT-2`

Known positive anchors supplied by the user:
- Garanin has task(s) in `DMS-SPRNT-1`;
- Garanin has task(s) in `DMS-SPRNT-2`.

These are oracle validation anchors, NOT hardcoded expected output. The tester must verify them directly. If the oracle still reports zero Garanin tasks in both, classify `ORACLE_SOURCE_CONTRACT_BROKEN`; all dependent DMS/Garanin verdicts are INVALID until fixed.

### O-04 Status grounding
Enumerate raw statuses and the canonical mapping. Explicitly record what is considered terminal/non-terminal. If `открытые` has no approved semantic convention, the agent must clarify rather than silently invent one.

### O-05 Current/last sprint semantics
Discover current active and most recently completed sprint(s) from source. If `последний` has no approved convention, ambiguity must trigger clarification.

### O-06 Independent-oracle rule
The oracle and the agent must not share an unverified mapping assumption. Agreement between two identical broken filters is NOT PASS.

---

# 1. Core-8 exhaustive functional matrix
Execute **all tests and exact queries** defined in `CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017.md`:

## task_search
- TS-01..TS-08 single filters
- TS-09..TS-16 two-filter compositions
- TS-17..TS-24 critical 3/4-filter compositions
- TS-25..TS-28 natural-language paraphrases
- TS-29..TS-35 ambiguity/contradiction/nonexistent
- TS-36 false-empty defense

### GOLDEN query
`Покажи открытые задачи Гаранина в последнем спринте по DMS.`

For GOLDEN and every composition query record:
- raw user text;
- intent;
- all extracted slots;
- resolved assignee ID;
- resolved product/space evidence;
- resolved exact sprint ID;
- resolved status set or clarification;
- direct source task keys after each individual filter;
- direct final intersection;
- agent task keys;
- `MISSING_KEYS`;
- `EXTRA_KEYS`.

`COMPLETED + 0` is PASS only when the independent oracle proves the final intersection is empty.

## task_summary
- SUM-01..SUM-08

## task_quality
- Q-01..Q-08

## sprint_health
- SH-01..SH-10

## velocity
- V-01..V-08

## team_workload
- TW-01..TW-10

## competency_match
- CM-01..CM-09

## release_health
- RH-01..RH-10

## cross-skill compositions
Execute every X-* scenario from 017. Cross-skill queries are mandatory and cannot be replaced with isolated skill calls.

---

# 2. Harness correction/recheck loop — mandatory
Execute **all CL-01..CL-15** from `CORE8_CORRECTION_LOOP_ADDENDUM_017A.md`.

This section is part of Core-8 acceptance, not an optional Learning Loop demo.

## GOLDEN correction dialogue
Turn 1:
`Покажи открытые задачи Гаранина в последнем спринте по DMS.`

If wrong/zero, same session Turn 2:
`Ты не прав, проверь еще раз.`

Required:
1. Link the challenge to the prior execution/trace.
2. Re-open semantic assumptions and source evidence.
3. Perform NEW source reads/revalidation; cached repetition is FAIL.
4. Re-check assignee, DMS membership, sprint and status semantics independently.
5. Ask only the minimum targeted clarification still required.
6. Compare corrected result with independent source ground truth.
7. Persist a structured negative-feedback/correction trace.
8. Do NOT auto-promote a global skill rule.

Also execute the stronger challenge:
`Ты не прав. У Гаранина точно есть задачи в DMS-SPRNT-1 и DMS-SPRNT-2. Проверь через спринты.`

The user assertion is a hypothesis to verify, not permission to trust/hardcode it.

---

# 3. Clarification behavior acceptance
For ambiguous phrases, verify the agent either uses a previously approved convention and logs it, or asks a targeted clarification.

Mandatory ambiguity classes:
- `открытые` = only Open vs all non-terminal;
- `последний спринт` = current/latest-started/latest-completed;
- colloquial `хвост`, `висят`, `в работе`;
- workload `перегружен` without approved capacity threshold;
- insufficient competency evidence;
- missing task/sprint/release identifier.

Automatic FAIL:
- silently dropping a selector;
- picking an arbitrary interpretation without approved convention;
- asking the user to restate the entire original query after a simple correction;
- asking the user to know internal AS21 field names.

---

# 4. Session memory vs persistent learning
Mandatory sequence:

### L-01 Same-session correction
Correct a misunderstood semantic convention and repeat the original query in the same `session_id`.
Expected: corrected context retained.

### L-02 New session before promotion
Repeat the same ambiguous query in a new session before any candidate promotion.
Expected: session correction does NOT masquerade as persistent global learning.

### L-03 Feedback trace
Verify negative feedback trace includes prior trace/execution, skill, prior slots/result, correction text, corrected slots/result and evidence delta (or semantic equivalents).

### L-04 Candidate mining
Repeated equivalent corrections may produce a bounded candidate only through the accepted Learning Loop pipeline.

### L-05 Shadow/eval
Candidate must be evaluated against the frozen corpus/baseline. Source-contract/adapter defects must NOT be converted into a semantic learning candidate.

### L-06 Human approval
No production promotion without explicit human approval.

### L-07 Post-promotion new session
Only after approved promotion, repeat in a fresh session. First-pass behavior should improve while explicit wording still overrides learned defaults.

---

# 5. Source-contract defect classification
If a real known-positive task disappears because assignee/product/sprint/status is read from the wrong AS21 attribute, classify:
`SOURCE_CONTRACT_OR_GROUNDING_DEFECT` / HIGH.

Do NOT:
- teach it away with Learning Loop;
- change expected result to zero;
- mark agent/oracle agreement as PASS.

Required developer fix path:
`raw AS21 evidence -> adapter mapping -> canonical Task -> grounding/filtering -> production query -> regression test`.

---

# 6. False-empty / false-green defense
For every task-set result:
```text
GROUND_TRUTH_COUNT = N
AGENT_COUNT = N
MISSING_KEYS = [...]
EXTRA_KEYS = [...]
```

Unambiguous PASS requires exact set equality.

Automatic `FALSE_EMPTY_HIGH` when:
- agent returns zero;
- independent ground truth contains one or more matching tasks.

Automatic `ORACLE_BROKEN` when:
- oracle contradicts a known positive anchor;
- raw source investigation has not proved the oracle's mapping.

---

# 7. Protected regression invariants
Throughout the run verify:
- AS21 mutations = 0;
- WMB-30000 attachment visibility remains correct;
- release short/full grounding remains correct;
- false-green gates remain fail-closed;
- learning pipeline cannot auto-promote;
- no new HIGH production regressions.

---

# 8. Required reporting
Publish a single report:
`qa_reports/CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2.md`

The report must contain the complete per-test table, plus an explicit defect ledger grouped by:
- `ORACLE_SOURCE_CONTRACT_BROKEN`
- `SOURCE_CONTRACT_OR_GROUNDING_DEFECT`
- `SEMANTIC_INTERPRETATION_DEFECT`
- `CLARIFICATION_LOOP_DEFECT`
- `SESSION_CONTEXT_DEFECT`
- `LEARNING_LOOP_DEFECT`
- `SKILL_EXECUTION_DEFECT`
- `FALSE_EMPTY_HIGH`
- `FALSE_GREEN_HIGH`
- `EXTERNAL_DEPENDENCY`

Footer:
```text
ASSIGNMENT_ID = CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017_V2
CURRENT_HEAD = <sha>
ORACLE_PREFLIGHT_PASS = YES|NO
KNOWN_POSITIVE_DMS_GARANIN_ANCHORS_VERIFIED = YES|NO
TOTAL_FUNCTIONAL_TESTS = N
FUNCTIONAL_PASS = N
FUNCTIONAL_FAIL = N
CORRECTION_LOOP_PASS = x/15
CHALLENGE_TRIGGERS_SOURCE_RECHECK = YES|NO
TARGETED_CLARIFICATION_PASS = YES|NO
SESSION_CONTEXT_RETENTION_PASS = YES|NO
SESSION_MEMORY_NOT_CONFUSED_WITH_LEARNING = YES|NO
NEGATIVE_FEEDBACK_TRACE_PASS = YES|NO
LEARNING_PIPELINE_BOUNDARY_PASS = YES|NO
ORACLE_INDEPENDENCE_PASS = YES|NO
FALSE_EMPTY_HIGH_COUNT = N
FALSE_GREEN_HIGH_COUNT = N
SOURCE_CONTRACT_OR_GROUNDING_DEFECTS = N
NEW_HIGH_PRODUCTION_REGRESSIONS = N
AS21_MUTATIONS_DURING_TEST = 0
CORE8_REAL_QUERY_HARDENING_GREEN = YES|NO
READY_TO_RESUME_GATE_E = YES|NO
```

## Final GREEN rule
`CORE8_REAL_QUERY_HARDENING_GREEN = YES` only if ALL are true:
- oracle preflight proven;
- known DMS/Garanin positive anchors verified;
- all required functional tests pass or an explicitly approved live-data-drift exception exists;
- correction loop = 15/15;
- clarification behavior is correct;
- no false-empty HIGH;
- no false-green HIGH;
- session memory is distinguished from persistent learning;
- learning boundary remains safe;
- no unresolved source-contract/grounding HIGH defects;
- no new HIGH production regressions;
- AS21 mutations = 0.

Until then: **STOP. Do not resume Gate E.**