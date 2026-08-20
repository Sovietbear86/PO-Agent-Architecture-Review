# CORE8 017A — Harness Correction / Recheck Loop Addendum

## Why this exists
A Harness agent is not acceptable if it treats the first answer as final truth. When the user explicitly challenges an answer (`ты не прав`, `проверь еще раз`, `это неверно`, `у меня есть такие задачи`), the agent must reopen the evidence chain, preserve dialogue context, identify uncertainty, ask useful clarification when needed, and re-run source-grounded retrieval. A bare repetition of the same cached query/result is a failure.

This addendum is mandatory for `CORE8_EXHAUSTIVE_REAL_QUERY_MATRIX_017`. It does not replace 017; it extends its acceptance gate.

## General contract
For every correction-loop scenario record:
- original query and answer;
- original semantic slots and source calls;
- user challenge text;
- whether the same `session_id` was preserved;
- what facts/assumptions the agent reconsidered;
- clarification question(s), if any;
- new source calls made after the challenge;
- whether cached evidence was invalidated/revalidated;
- corrected result keys/counts;
- direct independent AS21/SWTR ground truth;
- whether the challenge produced a learning/feedback event;
- whether any persistent skill mutation occurred (must be NO without the approved learning pipeline).

A user challenge MUST NOT be answered with `Найдено 0` again merely because the original execution returned 0. It must trigger evidence revalidation.

---

# A. GOLDEN correction dialogue — Garanin / DMS

## CL-01 — challenge a false-empty answer
Turn 1:
`Покажи открытые задачи Гаранина в последнем спринте по DMS.`

If the agent returns 0 or an answer the tester knows to be wrong, Turn 2 in the SAME session:
`Ты не прав, проверь еще раз.`

Required behavior:
1. Treat Turn 2 as correction/negative feedback referring to Turn 1, not as an unrelated new task.
2. Re-open the interpretation and evidence chain.
3. Do not assume previous `product/space`, sprint or status mappings were correct.
4. Ask a targeted clarification if the ambiguity cannot be resolved safely, for example:
   - what `последний спринт` means (current active vs latest started vs latest completed);
   - what `открытые` means (only Open vs all non-terminal statuses);
   - if product membership mapping is uncertain, explain that source mapping needs revalidation rather than asking the user for an AS21 field name.
5. Re-query/re-read real AS21/SWTR facts after the challenge. A response generated only from cached prior evidence is FAIL.
6. Compare the corrected answer against independently established ground truth.

Known positive anchors supplied by the user for oracle validation:
- Garanin has tasks associated with `DMS-SPRNT-1`;
- Garanin has tasks associated with `DMS-SPRNT-2`.

These anchors are not permission to hardcode results. They are assertions that the oracle itself must investigate directly in AS21/SWTR. If the tester's oracle still claims zero tasks for both anchors, classify `ORACLE_SOURCE_CONTRACT_BROKEN` and stop declaring the scenario PASS.

## CL-02 — explicit corrective evidence from user
Same initial query. After an incorrect zero result, user says:
`Ты не прав. У Гаранина точно есть задачи в DMS-SPRNT-1 и DMS-SPRNT-2. Проверь через спринты.`

Required:
- preserve the original intent and assignee;
- verify the supplied sprint anchors through source reads;
- do not blindly trust the user assertion, but use it as a hypothesis to test;
- if verified, correct the answer and state which previous assumption was wrong;
- emit/store negative feedback trace suitable for Learning Loop mining;
- do not auto-promote a new skill rule.

## CL-03 — challenge without providing the answer
Initial query followed by:
`Нет, это неверно.`

Required: agent should ask a useful question or explain what it will re-check. It must not reply `что именно неверно?` as the only behavior when it can first revalidate obvious source assumptions itself. Preferred sequence: revalidate source facts, then ask only the minimum unresolved semantic clarification.

---

# B. Clarification correctness

## CL-04 — ambiguous “open”
Turn 1: `Покажи открытые задачи Гаранина в DMS.`
Turn 2 after result: `Под открытыми я имел в виду все незавершенные, а не только статус Open.`

Required:
- same-session correction updates the execution frame;
- re-run with terminal-status convention explicitly visible in trace;
- no fabricated status mapping;
- corrected set exactly matches direct source intersection.

## CL-05 — ambiguous “last sprint”
Turn 1: `Покажи задачи Гаранина в последнем спринте DMS.`
Turn 2: `Я имел в виду последний завершенный спринт.`

Required:
- replace only the sprint selector;
- retain assignee/product filters;
- re-ground exact sprint ID from source;
- return exact corrected task set.

## CL-06 — explicit override after learned/default convention
If a default convention exists for `последний`, run:
Turn 1: `Покажи задачи Гаранина в последнем спринте DMS.`
Turn 2: `Нет, возьми последний завершенный, а не текущий.`

Required: explicit user correction overrides default/learned convention for this execution/session.

---

# C. Cross-skill correction loops

## CL-07 — task summary correction
Turn 1: `Суммаризируй WMB-30000.`
Turn 2: `Ты пропустил вложения, проверь еще раз.`

Required: re-read attachment metadata/content only through supported source paths, preserve what was already correct, and correct only unsupported/omitted claims.

## CL-08 — sprint health correction
Turn 1: `Покажи здоровье текущего спринта DMS.`
Turn 2: `Количество задач неверное, перепроверь полный спринт.`

Required: invalidate any first-page/partial corpus, re-read complete paginated sprint set, report changed count and why.

## CL-09 — workload correction
Turn 1: `Какая нагрузка у Гаранина по DMS?`
Turn 2: `Ты потерял задачи из спринтов, проверь еще раз.`

Required: revalidate assignee + DMS membership + sprint relations, not merely rerun the same cached filter.

## CL-10 — release correction
Turn 1: `Покажи здоровье релиза <REAL_RELEASE>.`
Turn 2: `Похоже, ты учел не все задачи релиза. Проверь еще раз.`

Required: re-read complete release scope and evidence; no fabricated additions.

---

# D. Feedback vs session memory vs persistent learning

## CL-11 — same-session retry
After a correction is resolved, repeat the original query in the SAME session.
Required: use the corrected interpretation/context without asking the already-resolved clarification again, unless source data changed.

## CL-12 — new session before promotion
Open a NEW session and repeat the original ambiguous query before any learning candidate is approved/promoted.
Required: session-only correction must NOT masquerade as persistent learning. The old clarification may legitimately recur.

## CL-13 — feedback capture
Verify that explicit phrases such as:
- `ты не прав`;
- `проверь еще раз`;
- `это неверно`;
- `я имел в виду ...`;
produce a structured negative-feedback/correction trace linked to the prior execution and skill.

Required trace fields (or semantically equivalent): prior execution/trace id, skill/intent, correction text, prior slots/result, corrected slots/result, evidence delta.

## CL-14 — learning candidate after repeated corrections
Using an isolated/frozen evaluation corpus, prove repeated equivalent correction traces can be mined into a bounded improvement proposal. The proposal must go through the already accepted Learning Loop gates (sandbox/shadow/eval/human approval). It must NOT directly rewrite production semantics.

## CL-15 — post-promotion new-session behavior
Only after an approved candidate is promoted, open a NEW session and re-run the target query. Verify the approved convention improves first-pass behavior while explicit modifiers still override it.

---

# E. Anti-pattern attacks

The following are automatic FAILs:
1. `Ты не прав` -> agent repeats identical cached answer without a new source read.
2. Agent discards previous session context and asks user to restate the entire request.
3. Agent changes several unrelated slots after user corrected only one.
4. Agent accepts a user's claimed task/sprint as truth without source verification.
5. Agent converts one correction directly into a global production rule without evaluation/promotion.
6. Agent says `COMPLETED` after recheck when independent ground truth still contradicts the set.
7. Tester/oracle and agent use the same unverified mapping and call agreement a PASS.

---

# Acceptance metrics

Report:
```text
CORRECTION_LOOP_SCENARIOS = 15
CORRECTION_LOOP_PASS = x/15
CHALLENGE_TRIGGERS_SOURCE_RECHECK = YES|NO
TARGETED_CLARIFICATION_PASS = YES|NO
SESSION_CONTEXT_RETENTION_PASS = YES|NO
SESSION_MEMORY_NOT_CONFUSED_WITH_LEARNING = YES|NO
NEGATIVE_FEEDBACK_TRACE_PASS = YES|NO
LEARNING_PIPELINE_BOUNDARY_PASS = YES|NO
ORACLE_INDEPENDENCE_PASS = YES|NO
FALSE_EMPTY_AFTER_CORRECTION = N
AUTO_PROMOTION_FROM_SINGLE_CORRECTION = N
HARNESS_CORRECTION_LOOP_GREEN = YES|NO
```

`HARNESS_CORRECTION_LOOP_GREEN = YES` only with 15/15, independent oracle evidence, zero false-empty after resolved correction, and zero automatic promotion from a single user correction.

This addendum is a mandatory prerequisite for `CORE8_REAL_QUERY_HARDENING_GREEN = YES`.