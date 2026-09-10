# Agent Core v4 — Skill-Native Radical Pivot

**Date:** 2026-09-10  
**Decision:** APPROVED  
**Reason:** Assignment 175 proves the current semantic-prepass/clarification seam is structurally too brittle for the product goal. We stop adding field/name/phrase exceptions and move to a skill-native Hermes-style agent runtime.

## 1. Product goal

PO Agent must solve user requests by selecting and composing its skills/capabilities, not by relying on a brittle mandatory semantic schema that has to perfectly extract every person, space, sprint, status or phrase before execution can begin.

Target user experience:

```text
User: Открытые задачи Гончарова в спринте OLP-SPRNT-5

Agent:
  1. understands the goal at a high level;
  2. discovers relevant skills;
  3. resolves/validates entities from source-backed tools;
  4. executes one or more typed capabilities;
  5. observes results and replans if needed;
  6. validates facts against deterministic postconditions;
  7. returns a concise final answer.
```

No preconfigured Goncharov, no preconfigured sprint, no phrase-specific route and no local script generation are required.

## 2. Radical architectural changes

### 2.1 Semantic pre-pass is demoted from gate to hint

OLD:

```text
query -> semantic JSON -> clarification gate -> grounding -> route -> capability
```

NEW:

```text
query -> optional lightweight goal/entity hints
      -> progressive skill catalog
      -> LLM planner
      -> typed capability call
      -> capability-level source grounding/validation
      -> observation
      -> re-plan or FINAL
```

Rules:
- empty/partial semantic hints do NOT fail a request by themselves;
- `clarifications` emitted by an optional semantic helper are advisory only;
- a clarification is user-visible only when the planner/capability layer proves that an executable required argument cannot be resolved safely from the query, prior observations or authoritative source metadata;
- no more expanding suppression sets for fields such as `filters`, `semantic_contract`, etc.;
- no surname-specific or phrase-specific semantic patches.

### 2.2 Capabilities own entity resolution requirements

Each registered capability declares what it needs and how unresolved arguments may be discovered.

Example:

```yaml
id: task.search
arguments:
  assignee:
    type: source_identity
    optional: true
    resolver: member.resolve
  space:
    type: source_space
    optional: true
    resolver: space.resolve
  sprint:
    type: source_sprint
    optional: true
    resolver: sprint.resolve
  status:
    type: semantic_enum
    optional: true
source: REAL_AS21
postconditions:
  - returned rows satisfy every resolved constraint
```

The planner may call a resolver first, or a capability may invoke a deterministic resolver as part of argument binding. Identity correctness no longer depends on whether a separate LLM semantic pre-pass emitted `person_raw`.

### 2.3 Skills are procedures, capabilities are tools

A skill is not a phrase router. A skill contains compact procedural knowledge such as:

```text
skill: tasks.by_person_and_sprint
purpose: find tasks for a person inside a sprint
likely capabilities:
  - member.resolve
  - sprint.resolve / sprint.inspect
  - task.search
validation:
  - exact assignee
  - exact sprint
  - requested status if present
```

Skills may be selected progressively and combined. The LLM decides the trajectory; executors and validators remain deterministic.

### 2.4 Planner receives compact catalog, not 54 full skill prompts

Initial context contains only compact metadata:

```text
task.lookup     — read one task by key
task.search     — search tasks by source-backed constraints
member.resolve  — resolve a human reference to source identity
space.resolve   — validate/resolve a product space
sprint.resolve  — validate/resolve sprint identity
sprint.inspect  — read sprint facts
release.inspect — read release facts
team.inspect    — read team facts
...
```

When the planner selects a candidate skill/capability, only then is the detailed contract/procedure loaded.

### 2.5 True plan -> act -> observe loop

Planner decision remains typed:

```json
{"call":{"capability_id":"member.resolve","arguments":{"reference":"Гончарова"}},"final":null}
```

Observation:

```json
{"member_login":"Goncharov.A.O","confidence":"source_exact","source":"REAL_AS21"}
```

Next planner decision may use `$obs` references. The loop continues until the requested goal is supported by validated observations.

### 2.6 Final answer synthesis is separated from tool selection

The planner should optimize for the next capability call, not spend its decision budget reproducing long final prose. After the trajectory is complete, a dedicated response synthesizer gets only validated compact facts and produces the user answer.

This separation is mandatory if planner reliability/latency benefits are confirmed in the v4 pilot.

## 3. What remains deterministic and strict

Radical simplification of orchestration does NOT weaken enterprise safety.

Keep:
- REAL AS21/MCP-SWTR authority;
- read-only source policy;
- typed capability contracts;
- deterministic source/entity resolvers;
- immutable user-request constraints once resolved;
- exact task-key postcondition checks;
- source-unavailable != empty;
- session isolation;
- trace/evidence;
- A/B Oracle certification;
- Browser C certification;
- no arbitrary generated code or credential-bearing endpoint calls.

## 4. Four implementation steps

### V4-1 — Skill-native runtime foundation

Build an additive `agent_core_v4` behind a feature flag.

Deliver:
- `SkillCatalogV4` compact metadata and lazy detail loading;
- `CapabilityRegistryV4` adapter over proven v3 capabilities initially;
- `SkillNativePlannerV4` receiving raw user query + compact catalog + observations;
- optional semantic hints, never a stopping gate;
- typed `CALL | FINAL/READY_FOR_SYNTHESIS`;
- bounded trajectory state with source-backed observations.

Acceptance smoke tests MUST prove that an empty semantic hint object does not stop:
- `Задачи Гаранина`
- `Открытые задачи Андрея Моисеева в DMS`
when the required entities can be resolved by capabilities.

### V4-2 — Source-backed resolver capabilities + task family cutover

Expose governed capabilities:
- `member.resolve`
- `space.resolve`
- `sprint.resolve`
- `task.lookup`
- `task.search`

`task.search` accepts combinations of assignee, space, sprint and status if the source contract supports them.

Mandatory benchmark:
- `Открытые задачи Гончарова в спринте OLP-SPRNT-5`
- same shape for several real team members and approved spaces/sprints;
- no names/sprint IDs hardcoded in routing or prompts;
- exact REAL AS21 parity.

At this point task-family requests must no longer choose between legacy and H1B based on entity/name.

### V4-3 — Progressive migration of all 54 skills

Convert the 54 existing user-facing skills into:
- procedural skill metadata;
- capability dependencies;
- deterministic validators/oracle contracts;
- optional analysis/synthesis instructions.

Do not create 54 unique executors where capability reuse is possible.

Families:
1. task;
2. sprint;
3. team/member;
4. release;
5. quality/velocity/carryover;
6. portfolio/PO analytics;
7. source-supported historical functions.

Each migrated family gets focused A/B/C before legacy retirement.

### V4-4 — Learning Reviewer / self-improvement

After skill-native execution is stable, implement reviewer-based learning:

```text
bad answer / user feedback / validator anomaly
 -> replay trajectory
 -> independent source recheck
 -> identify failing decision/procedure
 -> propose generalized skill/policy update
 -> sandbox A/B/C tests
 -> versioned promotion
 -> rollback
```

Learning examples:
- GOOD: learn that person+sprint task requests should resolve both source entities before task.search.
- BAD: remember that Goncharov has zero tasks in one particular sprint.

The runtime must become better at choosing/composing skills, not memorize mutable business facts.

## 5. Explicitly retired design assumptions

After v4 pilot begins, do not add new production dependencies on:
- exact LLM semantic field names (`person_raw`, `semantic_contract`, `filters`, etc.) as prerequisites to execution;
- mandatory pre-execution intent labels for every user phrase;
- person-name selectors;
- phrase-specific capability routing;
- per-name grammatical normalization as the primary resolution mechanism;
- legacy/H1B split based on model-selected intent;
- ad-hoc generated Python scripts as normal runtime tools.

The old semantic parser may temporarily remain for hints/backward compatibility, but v4 correctness cannot depend on it.

## 6. PVM Guru/Hermes benchmark suite

The following requests become architecture benchmarks rather than one-off bug cases:

```text
Открытые задачи Гончарова в спринте OLP-SPRNT-5
Открытые задачи Андрея Моисеева в DMS
Задачи Гаранина
Покажи DMS-380 и задачи его исполнителя
Какие открытые задачи у <member> в текущем спринте <space>?
Сравни незавершенные задачи двух членов команды в одном спринте
```

The agent must solve them by skill/capability composition. If a required source capability does not exist, it must state that limitation rather than force the query through a different route.

## 7. 54-skill release gate remains mandatory

After migration:
- all 54 skills are discovered from the real catalog;
- all applicable approved spaces: `WMB`, `STS`, `OLP`, `DMS`, `CRPV`;
- multiple authoritative team identities;
- A = Agent Core v4;
- B = independent REAL AS21 Oracle;
- C = real browser;
- exact key/fact parity;
- normal/empty/not-found/ambiguous/source-unavailable states;
- no skipped case because of timeout;
- resumable/checkpointed marathon;
- no local DB/sync/fake truth.

## 8. Definition of success

V4 is successful when a new real person, sprint or space appearing in the source can be used in natural-language requests **without adding that entity to production semantic rules or routing code**.

The key product test is not whether the parser recognizes a known phrase. It is whether the agent can inspect its skills, safely obtain the missing source-backed facts, compose the necessary calls, validate the result and answer correctly.
