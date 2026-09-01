# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_109_AGENT_SEMANTIC_CONTEXT_LANGUAGE_FORENSIC`

## Role boundary
You are QA/forensic executor only. **Do not modify production code, frontend code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, testing rules, or this file.**

Assignment 108 proved one independent source/capability defect: status filtering could lose authoritative `workflow_status`. The owner has applied a minimal production fix in `po-agent-platform-v2/src/po_agent/adapters/hardened_production_task_api.py` to preserve workflow status from the REAL sprint-task row while still proving sprint membership via individual point reads.

Owner fix under test:
- `31459197d9a7a43dc5242a608d872152d2e27f25`

The owner's manual browser tests also exposed additional agent-quality failures that Assignment 108 did not fully localize:
- a Russian query `Задачи Гаранина` caused the Agent to mention/invent `SPRNT-2`, although the user did not provide a sprint;
- the same clarification was emitted in English;
- after selecting a member in an OLP sprint, the Agent sometimes broadened to all 66 sprint tasks, indicating a lost member filter;
- follow-up requests such as `только открытые` or `теперь только In progress` could return zero incorrectly or lose prior member/sprint constraints;
- a bare `DMS-SPRNT-2` could be routed into a path complaining about missing `task_key`;
- negative/correction turns could get stuck in repeated `Что именно нужно исправить?` loops rather than executing the clarified request.

These are counterexamples to the intended semantic contract. Do not assume they are prompt-only defects. The current interpreter already forbids inventing source IDs, and grounding is supposed to validate sprint/member IDs against REAL source facts. This assignment must prove the earliest failing boundary for each symptom before any owner semantic/state-machine fix.

## Global acceptance rules
1. REAL AS21/SWTR only for authoritative business facts; fake/mock/frozen authoritative calls = 0; AS21 writes = 0.
2. AS21 may be transiently unavailable. Timeout/502/503 requires up to 2 retries with 20–30 s backoff, then runtime/source revalidation and one focused retest before environment classification.
3. concurrency = 1. Normal timeout >=120 s; heavy source calls may use 180 s.
4. For task collections compare **exact task-key sets**, not only counts or response status.
5. HTTP 200 / `COMPLETED` never overrides wrong business facts.
6. For Russian user input, every user-facing Agent answer, clarification, error and correction question must be Russian. Immutable source identifiers, logins, task IDs and canonical source status names may remain as source values. An English Agent sentence in these scenarios is a product defect.
7. The Agent must never introduce a sprint/task/release/login that is absent from the current query, valid prior session context, or source-grounded clarification result.
8. Do not create/promote Learning Loop policies during this forensic. Capture policy state before/after and require no change.

## Phase 0 — provenance and fresh runtime
1. Pull current branch; record exact HEAD and clean tracked worktree.
2. Verify owner fix `31459197d9a7a43dc5242a608d872152d2e27f25` is in ancestry.
3. Fully stop/restart MCP-SWTR/AS21 bridge, Task API, Harness and frontend from current HEAD. Record PID/start time/ports.
4. Prove Harness is in REAL task-api mode and frontend proxies to the same Harness.
5. Independently prove current REAL source truth for:
   - `DMS-SPRNT-2` primary;
   - `DMS-SPRNT-1` cross-check;
   - `OLP-SPRNT-5` independent cross-check;
   - `Garanin.R.V` if currently present;
   - the correct source-backed identity/login for Александр Шалдунов if present;
   - Андрей Моисеев / `Moiseev.A.N` if present;
   - current workflow statuses represented in the chosen sprints.
6. Never reuse historical counts as expected truth. Re-read source now.

## Phase 1 — post-change status-filter certification
Before investigating semantic context, certify the owner fix from Assignment 108.

Use a REAL sprint/status pair that has non-empty Oracle results, preferably `DMS-SPRNT-2` + `In progress` if still source-valid.

Run through:
A. Browser/UI Agent.
B. Direct Harness with a fresh session.
C. Independent Oracle B from REAL sprint-task data.

Mandatory queries:
- `Покажи задачи со статусом In progress в DMS-SPRNT-2`
- one natural Russian paraphrase of the same request.

Compare exact task-key sets. Also inspect mapped task status/status_raw for at least several matching and non-matching tasks. Former silent `0` result must be absent when Oracle is non-empty.

Verdict this subgate as `STATUS_FIX_AB_PASS` or identify the exact first failing boundary.

## Phase 2 — unauthorized sprint invention + language contract
Use a completely fresh browser/session with no previous sprint context.

Primary exact query:
`Задачи Гаранина`

If `Garanin.R.V` is source-present, use that fact only for Oracle/member grounding. If absent, also run an equivalent surname-only request for another source-present member, but preserve the Garanin case as a semantic-invention test.

Trace, turn by turn:
1. original user query;
2. semantic interpreter output: intent, canonical_query, all slots and clarifications;
3. any previous/cached frame injected into interpretation;
4. grounding input/output;
5. clarification object actually returned to UI;
6. visible browser text.

Hard invariants:
- no `sprint_raw`, `sprint_id`, `SPRNT-2`, `DMS-SPRNT-2`, or any other sprint may appear unless explicitly present in valid session context or supplied by the user/source-grounded clarification;
- asking only for a person may clarify **the person**, not invent a sprint;
- all user-facing prose for this Russian query must be Russian.

Classify separately:
- `UNAUTHORIZED_SPRINT_INVENTION`
- `RUSSIAN_LANGUAGE_CONTRACT_VIOLATION`

For each, identify FIRST_FAILING_BOUNDARY.

## Phase 3 — Garanin member-only search
If `Garanin.R.V` exists in the live source:
1. Oracle B: independently calculate the exact task-key set assigned to that member in the source scope supported by the relevant skill contract.
2. UI: `Задачи Гаранина`.
3. If a person clarification is genuinely necessary, select the source-backed `Garanin.R.V` option.
4. Verify clarification application puts `member_login=Garanin.R.V` (or exact canonical source casing) into the next semantic frame.
5. Verify no unrelated sprint/status/product slot appears.
6. Compare Agent exact task-key set with Oracle B.

A member-only request returning zero while Oracle is non-zero is FAIL. A member filter disappearing before execution is `MEMBER_FILTER_LOST`.

## Phase 4 — Shaldunov sprint/member multi-filter
Use REAL `OLP-SPRNT-5` and the source-backed Александр Шалдунов identity if currently present. First build the Oracle sets from REAL AS21; do not assume any count.

Fresh-session query:
`Покажи задачи Александра Шалдунова в спринте OLP-SPRNT-5`

If the Agent requests a person clarification, choose only the source-backed identity/login. Then trace:
- initial frame;
- clarification state;
- selected option application;
- grounded frame;
- pre-execution slots;
- capability arguments;
- exact result task keys.

Required invariant: after person clarification, both `member_login` and `sprint_id=OLP-SPRNT-5` survive. The Agent must not broaden to all 66 (or current total) sprint tasks merely because the person was clarified.

Compare exact member ∩ sprint set with Oracle B.

Classify any loss as:
- `MEMBER_FILTER_LOST`
- `SPRINT_FILTER_LOST`
- or another precise boundary.

## Phase 5 — conversational follow-up slot retention/replacement
Continue the **same successful Shaldunov session**.

Turn 2:
`Да, только открытые`

Turn 3:
`Теперь только In progress`

Use the repository's current contract for the semantics of `открытые`; if it requires a legitimate clarification because no learned/canonical rule exists, record that clarification, then complete the turn using a source-backed choice. Do not silently assume a definition.

After each turn prove:
- member slot survives;
- sprint slot survives;
- new status constraint is added/replaces the previous status as appropriate;
- unrelated slots are not introduced;
- exact result set equals Oracle B for member ∩ sprint ∩ status.

The third turn must replace the previous status constraint rather than stack mutually exclusive old/new statuses.

## Phase 6 — direct natural multi-filter queries
Run each in a new clean session so success cannot depend on earlier dialogue:
- `Покажи открытые задачи Александра Шалдунова в спринте OLP-SPRNT-5`
- `Покажи задачи Александра Шалдунова со статусом In progress в OLP-SPRNT-5`
- `Покажи задачи Андрея Моисеева в DMS-SPRNT-2`
- `Покажи открытые задачи Андрея Моисеева из активного спринта по DMS`

For `активного спринта по DMS`, independently resolve the actual current/active sprint from REAL AS21. The Agent must not use remembered/hardcoded sprint IDs.

For every data-backed row compare exact task-key sets with Oracle B.

## Phase 7 — bare sprint interpretation
Fresh session. Send exactly:
`DMS-SPRNT-2`

This value is a source-backed sprint ID on the approved test surface. Trace semantic interpretation and routing.

Allowed behavior:
- interpret it as sprint context/task-sprint request where the product contract supports that shorthand; or
- ask one targeted Russian clarification about what the user wants to know/do with this sprint.

Forbidden behavior:
- route to a task-key capability requiring `task_key`;
- return `Missing required slot: task_key`;
- ask in English what `DMS-SPRNT-2` means when the source already confirms it is a sprint;
- invent another identifier.

Classify forbidden routing as `BARE_SPRINT_MISROUTED_TO_TASK_KEY` or the earliest proven semantic/skill boundary.

## Phase 8 — correction/resume loop
Using a clean session, create a legitimate clarification/correction situation around a REAL member+sprint request. Then exercise natural Russian replies such as:
- `Нет. Покажи открытые задачи Александра Шалдунова в спринте OLP-SPRNT-5`
- `Да, выведи открытые задачи из этого спринта`
- `Вывести задачи из спринта`

Trace dialogue classification, pending clarification/correction state, cached previous frame, new interpretation, grounding and final execution.

The Agent may ask one targeted clarification if a genuinely required slot is unknown. It must **not** repeatedly return variations of `Что именно нужно исправить в предыдущем запросе или результате?` after the user has already supplied an executable request.

If the same correction prompt repeats without incorporating explicit new constraints, classify `CORRECTION_LOOP_STUCK` and identify the earliest state-machine boundary.

## Phase 9 — response-language audit
Across all Russian-input turns in Phases 1–8, enumerate every visible Agent string:
- answer;
- clarification question;
- validation/error message;
- correction prompt;
- source-unavailable message.

Required: Russian prose. Technical IDs/logins/source values are exempt. Any English prose is a `RUSSIAN_LANGUAGE_CONTRACT_VIOLATION`.

Trace whether English originated from:
- LLM semantic clarification;
- deterministic runtime template;
- source error passthrough;
- frontend fallback.

Do not merely recommend translating strings; prove source/boundary.

## Phase 10 — first failing boundary matrix
For every defect/counterexample create a separate row. Allowed boundaries include:
- SESSION_CONTEXT
- SEMANTIC_INTERPRETATION
- CLARIFICATION_GENERATION
- CLARIFICATION_LANGUAGE
- CLARIFICATION_STATE_APPLICATION
- CORRECTION_STATE_CLASSIFICATION
- CORRECTION_STATE_APPLICATION
- ENTITY_GROUNDING
- SLOT_RETENTION
- SLOT_REPLACEMENT
- SKILL_RESOLUTION
- CAPABILITY_ARGUMENT_BUILDING
- TASK_SOURCE_HYDRATION
- SOURCE_CONTRACT
- RESPONSE_LANGUAGE
- FRONTEND_RENDERING
- QA_METHODOLOGY

Do not collapse multiple symptoms into one generic `semantic issue`.

## Phase 11 — regression/safety controls
At minimum preserve:
- exact DMS-271 lookup;
- DMS-SPRNT-2 full scope exact set;
- one member+sprint query on DMS;
- one independent OLP-SPRNT-5 query;
- no fake/mock/frozen authoritative data;
- no AS21 writes;
- Learning Loop exact policy state unchanged before/after.

## Output
Write only QA/forensic artifacts under `po-agent-platform-v2/qa_reports/`.

Primary report:
`po-agent-platform-v2/qa_reports/AGENT_SEMANTIC_CONTEXT_LANGUAGE_FORENSIC_109.md`

Optional evidence prefix:
`AGENT_SEMANTIC_CONTEXT_LANGUAGE_FORENSIC_109_`

Allowed final verdicts:
- `AGENT_QUALITY_DEFECTS_PROVEN`
- `MIXED_AGENT_AND_SOURCE_DEFECTS`
- `STATUS_FIX_GREEN_AGENT_DEFECTS_REMAIN`
- `NO_NEW_DEFECTS_AFTER_RETEST`
- `BLOCKED_BY_ENVIRONMENT`

A GREEN-like verdict requires the owner status fix to pass A/B and every owner-reported semantic/context/language counterexample either to pass or to be disproven with stronger live evidence. English prose on Russian turns, invented sprint context, lost explicit filters, correction loops, or wrong exact task sets prohibit GREEN.

Commit/push only allowed QA artifacts, report final SHA, then STOP. Do not modify production/frontend code and do not start any later assignment.