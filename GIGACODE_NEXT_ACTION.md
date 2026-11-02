# GigaCode — CURRENT NEXT ACTION

## A230R3.21-P31-D2-R5-SOURCE-TRANSITION-PROJECTION-QA

**INDEPENDENT QA ONLY.** No code changes, no commits/push/merge, no modifications to Core, AS21, Public, or user's running services. Preserve dirty/untracked files. Fetch origin; record LOCAL_HEAD=REMOTE_HEAD=TESTED_HEAD.

### Prior gate
A230R3.20-R2 **D2_R4_GREEN** on `67b5556`: fixed source-proof GET tests 4/4, collector 6/6, validator 16/16, calculator 11/11, HTTP adversarial 18/18, bounded REAL AS21 A/B DMS-SPRNT-5 exact 34/34, V4 299 passed, frontend build exit 0, Core V4 6/6. Task API 141 passed / 25 previously existing failures. Source route returns counts only; forecast remains null.

### Owner D2 projection-preflight patch (NOT yet independently certified)
- `20af57d`: NEW `task-api/app/services/sprint_forecast_projection.py`. Pure boundary: accepts collector complete evidence and *explicit authoritative current statusType + event statusType mappings*, validates terminal closure event, monotonic timestamp order, reopened tasks, completeness, identity, snapshot time and no future data. Returns only INTERNAL source-proven closed_at map plus counts; `forecast=None`, `committed_predictability=None`. No runtime route/adapter/plugin/UI wiring, no AS21 requests, no changes to 6 frozen Core files.
- `83a58ca`: NEW `task-api/tests/test_sprint_forecast_projection.py` synthetic offline tests (expected 14 pytest cases, verify exact count).
- StatusType mapping is **NOT implemented** in production source adapter; caller must prove it from AS21, not infer from text labels. Product-local time zone and working-day calendar also not connected yet. Never claim UI forecast is working.

### Gates
1. Source-diff vs `67b5556`: only 2 new projection files and this QA spec. Core 6/6 exactly vs `6fb335d`, no source writes, no secrets, no forbidden data scans.
2. Run projection tests, collector tests 6/6, source validation 16/16, REST route 4/4, forecast calculator 11/11. Independently adversarial test missing/malformed status maps, non-dict histories, duplicate canonical task IDs, empty sprint, missing event_id (AS21 may omit it!), repeated event ids, timestamps at UTC/local midnight, non-monotonic event ordering, reopened-then-done vs done-then-reopened, future close, history beyond snapshot, unknown statusType (must not be mistaken for nonterminal). If any exact contract is unmet, RED with first failure, no edits.
3. **Critical check**: Does REAL AS21 `HistoryEvent.event_id` always exist? In model it is Optional; if live events have `event_id=None`, current projection fails closed. Determine from sanitized real DMS-SPRNT-5 evidence without user identifiers; specify safest stable source-event identity strategy (no invented ID). Does current sprint source provide statusType for each event, or only status display names? If unavailable this is a **SOURCE_CONTRACT_BLOCKED** gate for live projection and must be reported without inventing source provenance.
4. Check semantics: `current_status_types` authoritative *as-of* current status, not future/recent cache; event mapping completeness; statuses with unknown type must fail closed. A terminal task with history not covering transition must fail, no updated_at fallback. Do not send raw `closed_at_by_task` or event names/IDs to UI.
5. Run full V4 (~299), source-backed Task API and broad Task API baseline (25 known failures), frontend build, Core 6/6. First failing boundary with exact evidence. Distinguish pure module QA from live feature.
6. Verdict `D2_R5_GREEN` if pure tests/probes pass and source contract identified; `D2_R5_SOURCE_BLOCKED` if mandatory real statusType/event ID cannot be sourced; `RED` if pure correctness regression. Independently report what is required for next *smallest* owner source adaptation patch. No changes, STOP.

### Short command
Run A230R3.21-P31-D2-R5-SOURCE-TRANSITION-PROJECTION-QA from Review GIGACODE_NEXT_ACTION.md. Verify new pure projection adapter/tests, real AS21 statusType and event_id contracts, strict fail-closed, full regression/Core 6/6. QA-only, no fixes/commits. Report and STOP.
