# Architecture Review 025 — Semantic Robustness and Harness Correctness

## Status

**FREEZE: do not expand to 017_V2 / 48 skills until this review is closed.**

## Trigger

Real-user tests exposed that successful Core-8 execution still depends too heavily on narrow deterministic phrase patterns. Examples include:
- assignee extraction depending on words such as `исполнитель/исполнителя`;
- status extraction depending on specific prepositions/forms;
- product/space extraction depending on specific phrases;
- correction utterances such as `Опечатался...` not reliably reopening the previous execution;
- FakeAS21 data being used in tests where real SWTR grounding is required.

The objective is to ensure the system behaves as a true Harness around an LLM/semantic agent rather than as an ever-growing regex grammar.

## Target architecture principle

Natural-language understanding must be **model-first, schema-constrained, source-grounded**.

Deterministic code is allowed primarily for:
1. exact identifiers and syntax that should never be hallucinated (task keys, sprint IDs, release IDs, URLs);
2. validation / normalization / conflict detection;
3. capability allow-listing and safety gates;
4. source-grounding and fail-closed behavior;
5. regression guards.

Deterministic phrase dictionaries/regexes must NOT be the primary mechanism for understanding arbitrary user wording such as person, status, product, temporal scope, correction, or intent.

## Review scope

### A. Semantic interpretation pipeline
Map the complete path from `/api/v1/query` to execution:
- deterministic router/interpreter;
- LLM semantic interpreter;
- Core8 precision wrappers;
- entity grounding;
- clarification;
- dialogue/correction runtime;
- capability selection.

For every layer document:
- responsibility;
- input/output schema;
- whether it can mutate intent/slots;
- precedence/order;
- failure semantics;
- duplicated responsibilities.

### B. Regex / pattern dependency inventory
Inventory all regexes, phrase dictionaries, marker lists and hand-coded Russian/English word forms used for semantic extraction/routing.
Classify each as:
- SAFE STRUCTURAL (exact IDs/URLs/etc.);
- VALIDATION ONLY;
- SEMANTIC CRUTCH (must be removed/reduced).

Required metric:
`SEMANTIC_CRUTCH_COUNT`.

### C. LLM-first structured semantic frame
Verify that the production LLM receives enough context and returns a typed schema containing at least:
- intent/capability goal;
- entities: person, product/space, sprint, release, status;
- temporal semantics;
- requested output/action;
- ambiguity/confidence;
- correction/reference-to-prior-turn signal.

The LLM should be able to interpret paraphrases without code changes.

### D. Entity resolution
Separate extraction from resolution:
- LLM extracts `person_raw = "Гаранина"` or `"Моисеев Андрей"`;
- resolver maps raw text to live team/contact/task identities;
- source evidence chooses `externalId/login/displayName`;
- ambiguity causes clarification, not guessed identity.

Do not hard-code employee names.

### E. Status ontology
User language such as `открытые`, `незавершённые`, `со статусом OPEN`, `в работе`, `не закрытые` must map through a status ontology/source metadata, not phrase-specific router branches.
Distinguish exact source status from semantic category.

### F. Product/space ontology
Understand `DMS`, `DataMarts`, `пространство DMS`, `по DMS`, `в DMS`, typos and aliases through alias/entity grounding, not exhaustive sentence templates.

### G. Dialogue and correction
A follow-up may refer to the prior turn without repeating the original query.
Required correction classes:
- `ты не прав, проверь еще раз`;
- `опечатался, имел в виду ...`;
- `нет, я говорил про ...`;
- `статус имел в виду ...`;
- `не текущий, а последний завершенный`.

The runtime must merge corrected slots with the prior semantic frame, re-ground source evidence, and only then re-execute.

### H. Real-vs-fake source boundary
Audit every acceptance test and runtime mode. FakeAS21 must never be used to claim correctness of a real employee/product/sprint query unless the fixture explicitly contains the required ground truth.

### I. Learning loop boundary
Learning loop may improve semantic policy/examples/prompts after evaluation and approval. It must not compensate for broken adapters/source contracts. A single user correction must not directly mutate production behavior.

### J. Evaluation architecture
Replace phrase-specific happy-path tests with paraphrase families and metamorphic tests.
For each semantic intent, generate variants across:
- synonyms;
- word order;
- inflection/cases;
- punctuation;
- typos;
- omitted prepositions;
- conversational context;
- correction turns.

Acceptance must compare semantic frame + grounded task keys, not merely HTTP/status.

## Required deliverables

1. `architecture_reviews/SEMANTIC_PIPELINE_MAP_025.md`
2. `architecture_reviews/REGEX_PATTERN_INVENTORY_025.md`
3. `architecture_reviews/TARGET_LLM_FIRST_ARCHITECTURE_025.md`
4. `architecture_reviews/REFACTOR_PLAN_025.md`
5. `qa_assignments/SEMANTIC_ROBUSTNESS_ACCEPTANCE_026.md`

## Hard gate

Do not resume exhaustive 017_V2 until all are true:
- primary semantic understanding is LLM/schema driven;
- deterministic semantic-crutch inventory is reduced to agreed structural/validation cases;
- real-source queries work without special sentence templates;
- correction/ellipsis/context tests pass;
- paraphrase/metamorphic acceptance is green;
- no real-source acceptance relies on FakeAS21 ground truth;
- no HTTP 500/new high production regressions.
