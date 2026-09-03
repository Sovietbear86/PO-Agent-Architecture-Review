# PO Agent — Hermes Architecture Rebaseline

**Date:** 2026-09-03  
**Status:** AUTHORITATIVE REBASELINE  
**Branch:** `feat/core8-real-query-hardening-v2`

## Why this rebaseline exists

The current Agent Core v3 work proved useful safety primitives (immutable turn contract, postconditions, live source routing), but the real Workspace UI still runs a legacy `recovery/WorkspaceApp` chat path with persistent localStorage session state and legacy correction behavior. Real browser evidence therefore contradicts the assumption that the product has already been migrated to a Hermes-style agent.

Decision: preserve the certified REAL AS21/source plane and the v3 safety primitives, but change the migration order. We will now build the actual Hermes-style core loop, memory/skills/learning loop and single UI entry point before broad skill migration.

## 1. What Hermes means for this project

Hermes is not just a safer router. The architectural properties we want to reuse are:

1. One agent core loop for every entry channel/UI.
2. Explicit tool/capability registry rather than scattered routing logic.
3. Progressive skill disclosure: compact skill index first, full skill loaded only when selected.
4. Persistent sessions and searchable history separated from active turn state.
5. Distinct durable memory vs procedural skills.
6. Agent-managed skills: create/patch skill procedures after proven experience.
7. Background review / learning loop outside the foreground turn.
8. Skill lifecycle governance: provenance, usage, staleness, archive/rollback.
9. Subagents only for genuinely multi-step/multi-domain work.
10. Hooks/health checks around startup, turn completion and session completion.

For PO Agent, source facts remain authoritative in REAL AS21. Self-learning may change procedure/policy/skill instructions, never task IDs, counts, statuses or other live source facts.

## 2. Preserve vs replace

### Preserve
- REAL AS21 -> MCP-SWTR transport.
- Task API live read facades.
- canonical source normalization.
- exact task point read and NOT_FOUND semantics.
- authoritative assignee + space server-side filtering.
- evidence primitives.
- Agent Core v3 immutable accepted-turn contract.
- constraint preservation and result postcondition validation.
- deterministic calculations that have source-backed certification.

### Replace / retire progressively
- legacy `recovery/WorkspaceApp` chat session ownership.
- localStorage conversation identity.
- legacy correction runtime as the primary dialogue controller.
- overlapping semantic recovery/grounding/routing layers.
- implicit skill labels and duplicated capability logic.
- foreground "learning" that only asks the user what to fix.
- UI widgets reading unrelated legacy/local data paths.

## 3. Target architecture

```text
Browser / API
   |
   v
Unified Entry Adapter
   |
   v
Hermes-style Agent Core Loop
   |-- session context
   |-- LLM reasoning / semantic frame
   |-- tool + capability registry
   |-- progressive skill loader
   |-- clarification tool
   |-- deterministic executor
   |-- response synthesis
   |
   +--> REAL source plane -> Task API -> MCP-SWTR -> AS21
   |                       -> evidence + postcondition validator
   |
   +--> Session Store / session_search
   |
   +--> Memory Store (declarative, curated)
   |
   +--> Skill Store (procedural, versioned)

After-turn / background learning plane
   |
   +--> trajectory snapshot
   +--> feedback + source recheck
   +--> mismatch / success pattern extraction
   +--> skill candidate create/patch
   +--> sandbox replay + independent Oracle validation
   +--> promote / reject / rollback
   +--> usage tracking + curator
```

## 4. Core learning contract

The agent must learn from BOTH corrections and successful non-trivial workflows.

### Allowed durable learning
- how to resolve a source-backed person identity safely;
- always push accepted `space` into authoritative collection queries before pagination;
- how to interpret a stable business phrase or workflow;
- which capability sequence solved a recurring PO workflow;
- project conventions and user preferences in bounded memory.

### Forbidden durable learning
- `Kalachanov has 5 WMB tasks`;
- `Garanin has 16 tasks`;
- `DMS-380 belongs to X`;
- cached source answers treated as future truth.

### Promotion gate
A learned skill/policy is usable only when:
1. provenance exists (turn/trace/feedback);
2. the source-backed cause is proven where factual behavior is involved;
3. candidate is generalized (no entity-specific truth unless it is a user/project convention);
4. replay passes protected tests;
5. independent Oracle A/B passes for affected factual scenarios;
6. rollback snapshot/version exists;
7. the skill can actually be discovered and loaded on a later fresh session.

The last requirement is mandatory: writing a skill that is never rediscovered/applied is not learning.

## 5. Revised ordered stages

### H0 — Real Workspace Cutover and single entry point (P0)
Goal: stop testing one assistant while the user runs another.

Deliverables:
- real `WorkspaceApp` drawer uses the same Agent Core entry adapter as certification;
- remove/retire duplicate assistant implementation or make it impossible to route production traffic;
- sessionStorage/new-conversation lifecycle instead of global localStorage transient state;
- explicit `conversation_id`, `runtime_session_id`, `memory_scope_id`;
- visible runtime badge and trace (`Agent Core v3/Hermes` vs legacy during cutover);
- first visible turn of a fresh conversation can never inherit correction/recheck state.

Exit: real browser proves fresh-session behavior and the four pilot task queries through the intended core.

### H1 — Hermes Core Loop + Tool/Capability Registry (P0)
Goal: move from a specialized task router to one extensible agent loop.

Deliverables:
- one foreground loop: model -> tool/capability call -> result -> continue/synthesize;
- self-registering tool/capability registry;
- capability contracts declare source, constraints, oracle, postconditions and availability;
- clarification is a tool/typed action, not a hidden side state;
- progressive skill index and lazy full-skill loading;
- existing immutable turn contract remains enforced at source execution boundaries.

Exit: pilots run only through registry/core loop; no hidden legacy semantic route.

### H2 — Persistent Sessions, Memory and Recall (P0)
Goal: real cross-session intelligence without contaminating active dialogue state.

Deliverables:
- persistent session store (SQLite/FTS5-style or equivalent);
- session search tool returning real past messages;
- bounded curated USER/PROJECT/MEMORY context;
- active turn state is separate from durable memory;
- fresh conversation starts clean while memory remains available;
- memory write provenance + injection/safety checks.

Exit: restart/fresh-session tests prove recall works while correction state does not leak.

### H3 — Self-Learning Skills / Learning Reviewer 2.0 (P0)
Goal: make self-improvement a first-class closed loop, not a feedback form.

Deliverables:
- procedural skill store with create/patch/view/list;
- after-turn/background reviewer triggered by corrections, tricky recoveries, complex successful workflows and periodic review;
- automatic source recheck for factual complaints;
- mismatch localization to first failing boundary;
- generalized skill/policy candidate generation;
- sandbox replay + protected regression + Oracle validation;
- versioned promotion, rollback, provenance;
- skill usage counters and curator (active/stale/archive, never silent destructive delete);
- fresh-session proof that a promoted skill is discovered, loaded and changes behavior correctly.

Exit: at least 5 controlled learning scenarios demonstrate `experience -> candidate -> validation -> promotion -> fresh-session application -> rollback`.

### H4 — Migrate 54 skills by capability family (P0/P1)
Migration order:
1. task point read/search/assignee/space/status;
2. current sprint and sprint factual queries supported by source;
3. team/member/competency;
4. releases/version factual queries supported by source;
5. quality/portfolio/PO aggregations;
6. history-dependent skills only when authoritative historical contracts exist.

A family retires legacy routing only after focused A/B/C GREEN.

### H5 — Exhaustive 54-skill × spaces × team-member certification (P0 release gate)
Goal: no catalog blind spots.

Inputs are discovered at runtime/repo config, never hardcoded:
- production skill catalog: exactly 54 currently expected, but discovery count is recorded each run;
- approved spaces: `WMB`, `STS`, `OLP`, `DMS`, `CRPV`;
- all canonical team members from team config + live identity resolution.

Build an applicability matrix rather than blindly executing an invalid Cartesian product:

```text
skill x space x member x query-variant -> APPLICABLE | NOT_APPLICABLE(reason)
```

Every applicable cell must terminate PASS/FAIL/BLOCKED with evidence. NOT_APPLICABLE requires a contract reason; it is not a skip.

For task collections:
- Agent A exact task-key set == independent REAL AS21 Oracle B exact set;
- Browser C exact displayed/evidence task-key set == Oracle B;
- constraints preserved; no wrong-space/member rows.

For metric/aggregate skills:
- normalized business facts/inputs/formula/output match independent Oracle calculation.

Identity-language variants must include where relevant:
- canonical login;
- nominative surname/name;
- common Russian grammatical cases from natural user phrasing;
- product aliases only when explicitly supported by config/grounding.

Execution rules:
- checkpointed batches;
- concurrency=1 for heavy AS21 calls unless a later source contract explicitly permits more;
- 180-300s timeouts as appropriate;
- transient retry with backoff;
- no timeout may advance a test to PASS or silently skip it;
- resumable manifest records every cell.

Exit: zero unclassified applicable cells; all 54 skills have explicit certification coverage across relevant spaces/members.

### H6 — Full UI Data Plane migration and acceptance (P0 release gate)
Goal: eliminate the current empty cards/0%/dashboards with unknown provenance.

Inventory every route/widget/action:
`UI element -> frontend call -> API/core capability -> source -> Oracle contract`.

Required explicit UI states:
`LOADING`, `SUCCESS_WITH_DATA`, `REAL_EMPTY`, `PARTIAL_DATA`, `SOURCE_UNAVAILABLE`, `NOT_FOUND`, `ERROR`.

No unexplained `—`, `0`, `0%` or empty widget.

Exit: 100% UI inventory + lineage + interaction tests (filters, pagination, refresh, drill-down, feedback, new conversation, restart).

### H7 — Full browser E2E + learning E2E (P0)
- all critical product flows in real browser;
- fresh tab/new conversation/session isolation;
- feedback -> learning reviewer -> validated skill -> fresh-session reuse;
- service restart/recovery;
- source outage/fail-closed behavior;
- browser C cannot be replaced by API evidence.

### H8 — Release hardening
- read-only AS21 guarantee;
- secrets/security;
- performance/latency budgets;
- packaging/startup checks;
- full protected regression;
- release readiness.

## 6. Immediate next action

Do NOT expand additional skills on the current mixed UI/runtime.

Next owner work is **H0 REAL WORKSPACE CUTOVER**, followed immediately by H1/H2/H3. The self-learning plane is deliberately moved forward before the 54-skill migration so we do not migrate the full catalog onto another static router.

GigaCode remains QA-only and must not modify production code. Its next certification starts only after the H0 owner changes exist.

## 7. Current gate state

```text
REAL_SOURCE_PLANE = FOCUSED_GREEN
V3_SAFETY_CONTRACTS = GREEN_FOR_PILOT
REAL_WORKSPACE_ENTRYPOINT = LEGACY/MIXED_RED
SESSION_ISOLATION_IN_REAL_UI = RED
HERMES_CORE_LOOP = PARTIAL/NOT_COMPLETE
PERSISTENT_SESSION_SEARCH = NOT_IMPLEMENTED
DURABLE_MEMORY = NOT_IMPLEMENTED_OR_NOT_IN_PRIMARY_PATH
AGENT_MANAGED_SKILLS = NOT_IMPLEMENTED
BACKGROUND_LEARNING_REVIEW = NOT_IMPLEMENTED
SKILL_PROMOTION_ROLLBACK = NOT_IMPLEMENTED
FULL_54_SKILL_MIGRATION = NOT_STARTED_ON_HERMES_CORE
FULL_54_X_SPACE_X_MEMBER_CERTIFICATION = MANDATORY_NOT_DONE
FULL_UI_DATA_WIRING = RED/INCOMPLETE
RELEASE_READY = NO
```
