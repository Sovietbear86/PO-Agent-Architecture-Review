# CORE8_REAL_DATA_SEMANTIC_ARCHITECTURE_ACCEPTANCE_026

## Purpose
This is the consolidated acceptance run after the production semantic-core refactor.
It supersedes narrow 024-style phrase patches. The goal is to prove that production
natural-language understanding no longer depends on enumerating Russian keyword/
regex variants and that execution is grounded against real AS21/SWTR evidence.

## Tester role
GigaCode is QA/adversarial reviewer only. Do not change production code, tests,
fixtures, configuration, AS21/SWTR data, learning state or skill definitions.
Only create/update the assigned QA report.

## Mandatory environment
- branch: `feat/core8-real-query-hardening-v2`
- `PO_AGENT_AS21_MODE=task-api`
- semantic LLM enabled and API key loaded
- restart Task API and PO Agent from CURRENT HEAD
- use real AS21/SWTR for oracle and agent execution
- do NOT substitute FakeAS21Adapter for any acceptance claim

## Architecture preflight
Prove from the running process/import graph:
1. task-api production uses `EvidenceValidatedProductionTaskApiAS21Adapter`.
2. task-api production uses `LLMFirstSemanticInterpreter` wrapped by `ConversationAwareSemanticInterpreter`.
3. task-api production uses `ProductionEntityResolverV2`.
4. task-api production uses `SemanticCorrectionRuntimeV2`.
5. `Core8SemanticPrecisionInterpreter`, `deterministic_core8_frame` and the legacy `DeterministicRouter` are NOT the production natural-language path in task-api mode.
6. when semantic LLM is disabled/unavailable, production fails closed instead of returning a regex-routed business result.

Any failure above => RED immediately, but continue collecting evidence.

## Independent oracle rules
For every source-backed task query:
- independently derive the expected set from live SWTR/task-api source capabilities;
- exhaust pagination / complete corpus;
- compare by task key;
- report EXPECTED_KEYS, AGENT_KEYS, MISSING_KEYS, EXTRA_KEYS;
- never use the agent's own result as oracle;
- `COMPLETED + 0` is PASS only when the independent complete oracle is also empty.

## A. Known positive anchors
Re-prove current source truth first; do not rely only on old reports.

A1. `DMS-SPRNT-1` complete corpus exists and is non-empty.
A2. `DMS-SPRNT-2` complete corpus exists and is non-empty.
A3. Derive all tasks assigned to Garanin in `DMS-SPRNT-1` using raw identity fields.
A4. Derive all tasks assigned to Garanin in `DMS-SPRNT-2`.

Old QA observed 4 and 0 respectively; current live source truth wins if it changed.

## B. Paraphrase invariance — same semantics, same result
For the same current Garanin + DMS-SPRNT-1 oracle, run ALL variants below in fresh sessions.
They must produce the same task-key set without code/config changes between queries.

B1. `Покажи задачи Гаранина в DMS-SPRNT-1`
B2. `Что висит на Гаранине в спринте DMS-SPRNT-1?`
B3. `Какие тикеты у Гаранина относятся к DMS-SPRNT-1?`
B4. `Выведи работу Родиона Гаранина за DMS-SPRNT-1`
B5. `По DMS-SPRNT-1 что назначено Гаранину?`
B6. `Мне нужен список задач пользователя Гаранин в DMS-SPRNT-1`
B7. `Покажи, пожалуйста, задачи по DMS-SPRNT-1, которые сейчас на Гаранине`
B8. `DMS-SPRNT-1: что у Гаранина?`

Acceptance: all independently equivalent variants yield identical grounded task keys.
A new wording MUST NOT require a new regex/pattern patch.

## C. Person/product/status wording robustness
Use real people/products/statuses proven from source. Include at minimum the user's observed Moiseev-style case if that identity exists in current live source; if not, select another real team member and record the substitution.

C1. `Покажи задачи пользователя <PERSON> в пространстве DMS со статусом OPEN`
C2. `Найди OPEN-задачи <PERSON> по DMS`
C3. `Что в DMS сейчас висит на <PERSON> со статусом OPEN?`
C4. `По пространству DMS покажи работу <PERSON>, статус OPEN`
C5. `У <PERSON> какие задачи в DMS имеют статус OPEN?`

For each, compare exact keys to an independent oracle using person identity + product + status.
No requirement for the words `исполнитель`, `статус`, `пространство` in fixed grammatical forms.

## D. Multi-filter preservation
Run real queries combining 2, 3 and 4 filters. Verify no selector is silently dropped.

D1. person + sprint
D2. person + product
D3. person + status
D4. person + product + status
D5. person + product + sprint
D6. person + product + sprint + status (choose a combination with a non-empty oracle if possible)

Report the semantic frame/grounded filters exposed in harness metadata if available and exact key diffs.

## E. Explicit identifier safety
E1. `Покажи задачи в DMS-SPRNT-1` => full sprint ID preserved; not `SPRNT-1`, not task lookup.
E2. `Покажи задачи в DMS-SPRNT-2` => same.
E3. `Покажи задачи в DMS-SPRNT-999999` => MUST NOT return successful empty result. Expected fail-closed clarification/failure because echo alone is not existence proof.
E4. Exact real task key lookup such as `DMS-<N>` still works and is not confused with sprint ID.

## F. Natural correction / recheck loop
Use ONE session for each scenario. First obtain an answer, then send the follow-up exactly as written.

F1. `Покажи задачи Гаранина в DMS-SPRNT-1`
    -> `Ты не прав, проверь ещё раз`
Expected: source recheck is performed and agent asks a relevant clarification rather than treating the phrase as an unrelated task search.

F2. Start with Garanin query
    -> `Нет, я имел в виду Моисеева`
Expected: person slot is corrected semantically and the query is re-grounded/re-executed.

F3. Start with a real person
    -> `Опечатался. Речь идет о пользователе <OTHER_REAL_PERSON> в пространстве DMS`
Expected: no `semantic_interpretation_failure`; previous request context is used.

F4. Start with status OPEN
    -> `Стоп, статус имел в виду IN PROGRESS`
Expected: only status meaning changes; other grounded selectors remain.

F5. Start with DMS-SPRNT-1
    -> `Не этот спринт, возьми DMS-SPRNT-2`
Expected: sprint changes, other independent filters remain.

F6. Start with any task query
    -> `Перепроверь источник, кажется ты что-то потерял`
Expected: semantically classified recheck; fresh source evidence before clarification/result.

For all F tests report previous trace, recheck trace, whether source_recheck_performed=true, and whether persistent_skill_mutation=false.

## G. Typo/paraphrase tolerance without guessing
Use minor human typos that remain semantically obvious, e.g. one missing/extra character in ordinary words, NOT source identifiers.
G1-G5: create five variants of B/C queries with minor ordinary-language typos/reordered words.
Expected: same semantic result when meaning remains clear. If ambiguity is real, targeted clarification is acceptable. Inventing a source entity is not.

## H. Ambiguity and fail-closed
H1. Ambiguous person surname matching multiple people => clarification, not arbitrary choice.
H2. Unknown person => clarification/failure, not successful empty.
H3. Unknown status => clarification/failure, not normalization to OPEN.
H4. Semantic LLM disabled for task-api production => explicit semantic-model unavailable clarification/failure; no DeterministicRouter business answer.
H5. Source unavailable => source_unavailable/source_protocol error; not empty success.

## I. Core-8 business smoke on real data
Execute at least two materially different real queries for EACH of the eight current Core-8 skills. Oracle every source-backed factual result. Include both ordinary and paraphrased wording.
No skill earns PASS solely because HTTP=200 or status=COMPLETED.

## J. Regression
Run:
- focused semantic-core-v2 tests;
- explicit sprint tests;
- source readiness tests;
- correction tests;
- full regression suite.

Classify failures exactly as:
- NEW_PRODUCTION_REGRESSION
- STALE_TEST_EXPECTATION
- TEST_INFRA/MOCK_DEFECT
- PRE_EXISTING_NONPRODUCTION_DEBT
Do not count the same failure in contradictory categories.

## Hard acceptance gate
Set `READY_TO_RERUN_017_V2 = YES` only if ALL are true:
- production semantic preflight 6/6;
- QUERY_HTTP_500_COUNT = 0;
- paraphrase invariance B = 8/8;
- person/product/status robustness C = 5/5;
- multi-filter D = 6/6;
- explicit identifier E = 4/4;
- correction loop F = 6/6;
- typo/reorder robustness G = 5/5 (clarification allowed only for genuine ambiguity);
- fail-closed H = 5/5;
- Core-8 real smoke = 8/8 skills, no false-green;
- NEW_HIGH_PRODUCTION_REGRESSIONS = 0;
- no acceptance result depends on FakeAS21Adapter;
- no new natural-language regex/pattern was added during QA.

## Report
Write `qa_reports/CORE8_REAL_DATA_SEMANTIC_ARCHITECTURE_ACCEPTANCE_026.md` with:
- HEAD and service PIDs/ports;
- architecture preflight evidence;
- independent source oracles;
- every query + response status + intent + grounded filters + exact key diff;
- correction traces;
- regression classification;
- `SEMANTIC_CRUTCH_COUNT_PRODUCTION` assessment (natural-language phrase regex dependencies on task-api production path; structural ID regexes do not count);
- final hard gate table;
- `READY_TO_RERUN_017_V2 = YES|NO`.

Commit and push ONLY the report, then STOP.
