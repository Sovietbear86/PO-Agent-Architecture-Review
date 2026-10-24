# Harness Dialogue & Learning Contract

## Purpose

The PO Agent must behave as a real conversational harness agent, not as a phrase-to-function router. Natural-language variability, morphology, partial references, ambiguous statuses, people names, sprint names, releases and follow-up turns must be handled through dialogue, grounded resolution and bounded LLM reasoning.

The agent may use an LLM to interpret user intent and propose structured candidates. It must not use the LLM to invent source facts, calculate deterministic metrics, silently guess ambiguous entities, bypass source-readiness rules, or mutate production code/configuration without the governed improvement lifecycle.

## Core architecture

User message -> Dialogue Orchestrator -> LLM Semantic Interpreter -> Entity/Policy Resolvers -> Clarification Gate -> Skill Planner -> deterministic/read-only Capabilities -> grounded answer -> Satisfaction/Feedback -> Learning Loop.

### 1. LLM Semantic Interpreter

The LLM is allowed to:
- infer one or more candidate intents from free-form language;
- extract candidate entities and constraints: person, task, sprint, release, product, status semantics, time range, attachment type;
- normalize colloquial language into semantic constraints (for example `открытые задачи` -> unresolved status category candidate);
- detect ambiguity or missing slots;
- draft a concise clarification question;
- interpret follow-up answers in the context of the current session;
- summarize grounded capability outputs into natural language.

The LLM is NOT allowed to:
- decide that an AS21 entity exists without resolver evidence;
- fabricate a login, FIO, sprint, release or status;
- calculate velocity, predictability, WIP, aging, quality scores or other deterministic metrics;
- turn unavailable source data into a successful answer;
- execute write actions without explicit approval;
- change production code directly as part of online learning.

### 2. Structured semantic frame

Each turn must produce an internal frame similar to:

```json
{
  "intent_candidates": [{"intent": "task_search", "confidence": 0.88}],
  "slots": {
    "person": {"raw": "Гаранина", "value": null, "confidence": 0.55},
    "sprint": {"raw": "OLP 4", "value": null, "confidence": 0.62},
    "status_semantics": {"raw": "открытые", "value": "unresolved", "confidence": 0.72}
  },
  "missing_slots": [],
  "ambiguities": ["person", "sprint", "status_semantics"],
  "requires_clarification": true
}
```

The exact schema may evolve, but intent, slots, confidence, ambiguities and missing required information must remain explicit and testable.

### 3. Entity resolution

The agent must resolve candidates against authoritative sources.

Person resolution:
- search canonical team profile / directory by login, FIO, surname, transliteration and declared aliases;
- morphology is an input hint, not a hard-coded exhaustive table;
- one exact grounded match -> resolve;
- several plausible matches -> ask the user to choose;
- no grounded match -> ask who the user means and optionally show nearest source-backed candidates;
- never invent a person/login.

Sprint/release/task resolution follows the same rule. A colloquial `OLP 4` may be mapped to candidates by the LLM, but the final identifier must be confirmed by the source resolver.

### 4. Semantic policy resolution

Terms such as `открытые`, `активные`, `проблемные`, `просроченные`, `свежие`, `почти готовые` are business semantics, not fixed strings.

The agent may infer a candidate interpretation from configured business semantics. If exactly one configured interpretation is sufficiently confident, use it and state the applied interpretation when material. If several interpretations are reasonable, ask a clarification.

Example:

User: `Покажи открытые задачи Гаранина в спринте OLP 4.`

Possible clarification sequence:
1. `Под Гараниным вы имеете в виду Родиона Гаранина (login ...)?`
2. `Под открытыми считать все незавершённые статусы или только To Do/In Progress?`
3. `Я нашёл два подходящих спринта OLP ... Какой использовать?`

Clarifications should be minimal: ask only for information required to execute the correct Skill.

### 5. Clarification Gate

A clarification is mandatory when any required entity or semantic constraint is materially ambiguous, missing, unsupported by source facts, or below configured confidence.

The response must use Harness `NEEDS_CLARIFICATION`/equivalent structured state, include the unresolved slot, question and grounded options where available, and persist the pending frame in session context.

The next user message is interpreted as a continuation of that frame unless the user clearly starts a new request.

### 6. Dialogue/session behavior

Session state must retain:
- last semantic frame;
- resolved task/person/sprint/release/product entities;
- pending clarification slot;
- source evidence references;
- prior answer summary;
- feedback state.

Examples that must work:
- `Покажи задачи Гаранина в текущем спринте.` -> clarify person/sprint if needed.
- `Только незавершённые.` -> fill status constraint in the same frame.
- `А из них какие заблокированы?` -> reuse prior result scope, do not perform unrelated global search.
- `Нет, я имел в виду другого Гаранина.` -> reopen person resolution.

### 7. Answer completion and satisfaction loop

After a substantive answer the agent should offer a lightweight satisfaction prompt, for example:
`Ответ помог? Да / Нет / Хочу уточнить.`

For negative or improvement feedback, collect a reason or free-text comment when possible. Do not annoy the user after every tiny clarification; request satisfaction after a completed task/answer or at a configurable cadence.

Feedback must be linked to trace/session/skill/version/source readiness and the semantic frame that produced the answer.

### 8. Self-learning / AI-PDLC

Online learning means configuration/skill evolution under governance, not uncontrolled self-modifying code.

Allowed automatic learning artifacts:
- new utterance examples for an existing intent;
- entity aliases confirmed by the user;
- business-semantic aliases/rules (for example how the team uses `открытые`), scoped to product/team where appropriate;
- clarification templates;
- ranking weights or confidence thresholds within approved ranges;
- eval cases generated from failed/negative-feedback conversations;
- candidate skill/config versions.

Required lifecycle:
1. observe conversation + feedback;
2. mine failure/ambiguity pattern;
3. propose a configuration/skill candidate;
4. create regression/eval cases from the conversation;
5. run offline/shadow eval against baseline;
6. reject automatically if regressions or grounding violations appear;
7. promote only within the configured approval policy;
8. preserve version history and rollback.

Production source contracts, deterministic metrics, security boundaries and write permissions cannot be changed by online learning.

### 9. LLM freedom boundary

Use the LLM for interpretation and synthesis where language is fuzzy. Use deterministic code and source resolvers where correctness is measurable.

LLM freedom: intent candidates, slot extraction, ambiguity detection, follow-up interpretation, clarification phrasing, grounded summarization.

Deterministic boundary: entity existence, source readiness, source queries, status IDs/categories, metrics, counts, dates, write approval, evidence, regression gates, version promotion rules.

### 10. Acceptance principle

Testing must validate conversations, not dictionaries of every possible Russian declension.

A test succeeds when the agent either:
- resolves the request correctly and groundedly; or
- recognizes that it cannot safely resolve it and asks the right minimal clarification.

A test fails when the agent:
- silently guesses;
- routes an ambiguous request to a different Skill;
- invents a source entity;
- returns zero instead of a source error;
- asks unnecessary questions despite an unambiguous grounded match;
- loses session context;
- claims to have learned without producing a versioned learning artifact and evaluation evidence.

## Mandatory conversational acceptance scenarios

1. Ambiguous FIO: `Покажи задачи Гаранина.` -> choose/clarify from grounded candidates.
2. Inflected surname: `Покажи задачи Гаранина в спринте OLP-SPRNT-4.` -> no morphology-specific hard-coded route required; LLM + resolver handles it.
3. Ambiguous business term: `Покажи открытые задачи ...` -> configured semantic interpretation or clarification.
4. Missing sprint: `Покажи задачи Гаранина в текущем спринте.` -> resolve current sprint by product/context or ask product/sprint.
5. Unknown person -> ask, never fabricate login.
6. Unknown sprint -> ask/show grounded candidates, never fabricate ID.
7. Multi-turn slot fill: user answers only `Все незавершённые` -> continue pending request.
8. Correction: `Нет, другого Гаранина.` -> reopen resolver.
9. Follow-up scope: `А какие из них заблокированы?` -> reuse prior result scope.
10. Source outage during dialogue -> preserve frame and return typed source error; no zero result.
11. Post-answer feedback -> feedback linked to trace/skill/version.
12. Negative feedback -> improvement/eval candidate produced; production code unchanged.
13. Confirmed alias -> versioned alias/config candidate, regression eval, governed promotion.
14. Prompt injection asking to invent data -> refuse invention and remain grounded.
15. Skill not source-ready -> explain missing source capability instead of semantic rerouting.

## Merge gate

The recovery PR is not merge-ready until the runtime implements this dialogue contract at least for intent/slot interpretation, entity resolution, clarification state, multi-turn continuation, satisfaction feedback and governed learning artifacts. A purely deterministic keyword router is acceptable only as a fallback/safety path, not as the primary natural-language interface.
