# GigaCode — Current Action

## ACTIVE: Assignment 223 — UI widget/state/lineage remediation batch 1

Role: QA/adversarial tester only. Do not modify production/frontend/backend/plugin/test/config code.

### Frozen backend baseline
- full functional checkpoint: checkpoint/v4-full-functional-green-a221r3
- competency checkpoint: checkpoint/v4-team-competency-green-a222r2
- canonical skills remain 54/54 GREEN
- competency skills remain SOURCE_READY

This assignment validates frontend-only/product-presentation remediation. Do not reopen backend skill certification unless the UI change demonstrably affects execution contracts.

### Owner changes to audit
Commits:
- 3debd7c1d34854f8eb0d680c3eb6efcee3784613 — shared result-state adapter
- 90e435daa0aef41b8f1ddf62333e384df347dc62 — rich answer renderer
- 057c986a666f962aa5ade842d80612a974395d93 — chat uses rich answer renderer
- c7153e735f8e57199a3271ecbf33a5b34e6c68f2 — V4ResultPanel typed state adapter
- ac985739eb3b449f3c05553cfadf73c4c5ca218d — reusable ResultStatePanel
- 84b81b58556e0c82ebedc0959dbfe1eb1f415f0d — Overview state semantics
- 5bbcc9c267cb5c3476087e15b903b7c8943583d0 — Team widget lineage/capacity semantics
- dd82e74154e9484f1acaef9779fe94070ec36aa8 + bfa0ce00eb06058b98cf3d89f67e2ad83b78ccb4 — Quality state semantics
- 74f72b433aaac693e7a95f9fded38be889101ecd — Tasks/Sprints/Releases state semantics

### Product rules under test
The UI must distinguish:
NOT_RUN / LOADING / SUCCESS_WITH_DATA / REAL_EMPTY / NEEDS_CLARIFICATION / SOURCE_CONDITIONAL / SOURCE_UNAVAILABLE / NOT_FOUND / ERROR.

Rules:
1. Zero is business data, never a placeholder.
2. Empty collection means REAL_EMPTY only when the backend/source result proves it.
3. SOURCE_CONDITIONAL/UNAVAILABLE must never render as 0, empty success or "no risks".
4. Widget metrics must come from the actual V4 payload; no stale legacy field names.
5. Chat answers must not display raw markdown syntax such as ##, **, or markdown table pipes.
6. UI may format results but must not recompute business semantics from unrelated page state.
7. No frontend change may cause extra tenant-wide backend reads or mutations.

## P0 — static/build gate
1. Pull branch, clean worktree, record START_HEAD.
2. Diff from competency checkpoint.
3. Prove changes are frontend/docs only after A222R2.
4. Run frontend:
   - npm install only if already required by lockfile/environment; do not change dependencies
   - npm run build
   - npm run lint if configured/available
5. Run existing relevant e2e smoke.
6. Zero TypeScript/build errors.

Any build failure => RED STOP.

## P1 — shared state adapter unit/behavior review
Review resultState.ts and prove:
- FAILED source-unavailable -> SOURCE_UNAVAILABLE;
- PARTIAL/source-limited -> SOURCE_CONDITIONAL;
- NEEDS_CLARIFICATION -> NEEDS_CLARIFICATION;
- completed non-empty -> SUCCESS_WITH_DATA;
- completed explicitly empty collection + scalar zero count -> REAL_EMPTY;
- scalar business zero without an empty collection is NOT automatically REAL_EMPTY;
- missing response while loading is LOADING, not REAL_EMPTY.

Record any ambiguous backend state that the adapter cannot classify without string inference. Treat as finding; block only if it produces wrong UI behavior in P2-P7.

## P2 — Agent drawer / answer rendering
Use Browser C with representative answers containing:
- headings;
- bold text;
- bullet list;
- markdown table;
- competency recommendation table.

Require:
- no visible raw "##", "**", or separator row "|---|";
- tables are readable and scrollable in drawer;
- original answer content is preserved;
- V4ResultPanel still shows structured result and evidence;
- clarification buttons still work;
- feedback buttons still work;
- no session regression.

## P3 — Overview
Validate:
- attention queue;
- daily brief;
- status report/product cards;
- portfolio metrics.

Required:
- raw markdown eliminated in Daily Brief;
- if attention query is source-limited/error, UI does NOT say "Нет элементов";
- source-proven empty may say no items;
- product status does not default missing values to zero;
- Skill/Evidence/Trace lineage visible.

## P4 — Tasks + Sprints
Tasks:
- source-backed non-empty search;
- source-proven empty search;
- one source-unavailable/conditional or controlled equivalent.

Sprints:
- health/scope;
- throughput;
- WIP;
- predictability;
- risk queue.

Required:
- no false zero or false "Риски не выявлены";
- source-limited metric renders state panel/—;
- source-backed real zero remains visible as 0;
- task drawer/local task flow remains functional.

## P5 — Releases
This is the highest-risk semantic UI gate because current REAL AS21 release->task linkage is source-conditional.

Test WMB 24Q1 and OLP 1.6.0 (or current known source-conditional releases).

Require:
- Scope/Completed/Blocked/Readiness are NOT shown as 0 when linkage is unavailable;
- risk queue does NOT say "Риски не выявлены" from missing release membership;
- dependencies do NOT show 0/0 as if proven;
- blockers do NOT say none unless source proves empty;
- explicit source-limitation state is visible;
- no pseudo forecast.

## P6 — Team
Validate:
- workload;
- WIP;
- blocked;
- bottlenecks;
- distribution;
- capacity;
- competency/recommendation via drawer.

Require:
- workload rows use V4 fields active_tasks/wip/blocked, not stale tasks/estimated_hours;
- default hardcoded 40h baseline is gone;
- empty baseline invokes owner policy path;
- explicit entered baseline still works;
- if capacity is SOURCE_CONDITIONAL due missing estimates, UI shows source limitation, not 40h or 0 utilization;
- competency note no longer claims source is unavailable.

## P7 — Quality
Before/while requests unresolved or source-limited:
- no 0/100 placeholder;
- no Acceptance 0/100 placeholder;
- no REWORK verdict produced from missing data;
- no "0 gaps" success implication.

When source-backed results arrive:
- real scores and gaps render;
- READY/REWORK appears only after all required quality/missing/acceptance results are source-backed;
- aging queue shows zero only when source proves empty.

## P8 — source/write/session audit
During Browser C run require:
- 0 mutations;
- 0 local factual fallback reads;
- 0 tenant-wide broadening introduced by UI;
- session isolation/new-dialog still GREEN.

## P9 — regression summary
Retain compact smoke:
- canonical task search;
- sprint health;
- team workload;
- competency recommendation;
- release SOURCE_CONDITIONAL;
- quality task.

Do not rerun full 54/54 unless a backend contract regression is observed.

## Verdict
Use exactly one:
- AGENT_CORE_V4_UI_STATE_LINEAGE_GREEN_A223
- AGENT_CORE_V4_UI_STATE_LINEAGE_RED_A223

If GREEN:
- recommend checkpoint/v4-ui-state-lineage-green-a223
- next owner phase = UI visual design system + slide-derived backgrounds
- do NOT start Learning Reviewer yet.

If RED:
- identify first failing UI boundary and STOP; preserve screenshots and exact backend response that caused it.

Do not modify code.
