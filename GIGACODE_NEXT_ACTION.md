# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_141_ASSIGNEE_ZERO_RESULT_IDENTITY_FORENSIC`

## Mission
Assignment 140 did NOT prove the assignee route GREEN. It exposed two distinct unresolved defects and one internal contradiction:

1. Direct REAL MCP Oracle says `find_units_by_filter(assigned_to="Garanin.R.V")` returns task rows, while Task API and Agent A return **0 tasks**. This is NOT acceptable as "correct no tasks assigned" unless exact Oracle B proves an empty set.
2. Kalachanov identity resolution rejects natural/canonical-short forms with HTTP 409 because `_resolve_external_id()` only accepts exact `code/login` equality.
3. The Assignment 140 report did not publish the required exact Oracle task-key sets/counts, so A/B parity was not actually proven.

Your task is forensic localization only. Do NOT modify production code. Determine the exact first failing boundary for both defects so the owner can fix without guessing.

## Absolute rules
- REAL AS21/MCP-SWTR only. No local DB/sync/fake/mock/frozen truth.
- Current branch `feat/core8-real-query-hardening-v2`; record exact HEAD and hard restart Task API + Harness.
- Concurrency=1. Normal timeout 180s; paginated source calls 300s; transient retry 2 with 30s backoff.
- Never call zero correct unless Oracle exact key set is empty.
- Do not reuse historical counts as truth.
- Do not propose fuzzy matching without proving the live `search_users` response shape and uniqueness semantics.
- QA only; commit/push report/raw evidence only.

# PHASE 0 — provenance and source health
1. Record HEAD/worktree/PIDs/start commands.
2. Prove current MCP schemas for `search_users` and `find_units_by_filter`.
3. Prove two independent known-good `read_unit` calls from different approved spaces.

# PHASE 1 — Garanin Oracle B exact truth
Directly call REAL MCP:

1. `search_users({"request": {"text_search": "Garanin.R.V", "page": 0, "size": 100}})`
2. Resolve the authoritative user code.
3. Call `find_units_by_filter` with `assigned_to = "<authoritative code>"` using the live request schema.
4. Read ALL pages.

Persist:
- raw sanitized container shape;
- one complete sanitized task row;
- total source rows;
- exact task-key set before any approved-space filtering;
- exact task-key set after filtering to WMB/STS/OLP/DMS/CRPV;
- per-space counts/keys;
- DMS exact set.

If Oracle B is empty today, state that explicitly and prove it. If non-empty, zero from Task API is a product defect.

# PHASE 2 — trace Task API transformation row-by-row
For the SAME Garanin source response, trace the data through:

```text
MCP find_units_by_filter payload
 -> _parse_tool_content()
 -> _page_content()
 -> each raw row
 -> _canonical_row(row)
 -> row_space extraction
 -> _ALLOWED_SPACES filter
 -> optional DMS filter
 -> final canonical list
```

Instrument only via temporary QA-side monkeypatch/logging/scripts if needed; DO NOT edit production files.

For at least the first 5 Oracle rows record:
- raw task code location and value;
- raw attributes shape (list/dict/nested object);
- summary/title location;
- assigned_to location;
- space/project location and exact type/value;
- workflow_status location;
- result of `_attrs(row)`;
- result of `_canonical_row(row)`;
- reason row is retained or discarded.

Answer precisely:
- Does `_page_content()` lose rows?
- Does `_canonical_row()` return None?
- Does `space` normalize incorrectly or become None?
- Are rows discarded because `row_space not in _ALLOWED_SPACES`?
- Does pagination metadata incorrectly stop after page 0?
- Is task code/attributes schema different from assumptions?

Required output:
```text
LAST_CORRECT_ARTIFACT
FIRST_INCORRECT_ARTIFACT
FIRST_FAILING_BOUNDARY
EXACT_FILE
EXACT_FUNCTION
EXACT_EXPRESSION
WHY_ORACLE_ROWS_BECOME_ZERO
MINIMAL_OWNER_FIX_SCOPE
```

# PHASE 3 — direct Task API and Agent A parity
After Phase 1 truth is known, call:
- `/api/v1/swtr-read/assignee-tasks?assignee=Garanin.R.V`
- same with `space=DMS`
- Agent A `Задачи Гаранина`
- Agent A `Задачи Гаранина в DMS`

Capture exact key sets and compare to Oracle B. Do NOT describe a zero result as PASS if Oracle B is non-empty.

# PHASE 4 — Kalachanov identity forensic
Use repository config plus live MCP `search_users`. Run these independent searches where supported:
- `Kalachanov.V.V`
- `Kalachanov`
- `Калачанов`
- `Калачанова`
- full Russian FIO from config

For EACH search capture ALL returned rows and identity fields (`code`, `login`, `externalId`, FIO/display/name fields).

Then evaluate current `_resolve_external_id()` exactly:
```text
needle
 -> search rows
 -> candidate fields considered
 -> exact[]
 -> len(exact)
 -> returned code or 409
```

Determine the safest deterministic resolution rule from SOURCE evidence, considering:
- exact code/login match;
- exact FIO/display match;
- unique single search result fallback;
- unambiguous normalized surname/token match;
- ambiguity must still fail closed.

DO NOT simply recommend generic fuzzy matching. We need deterministic unambiguous identity grounding.

Test current Task API and Agent A for:
- canonical `Kalachanov.V.V`
- natural `Задачи Калачанова`

Capture the semantic frame too: determine whether the LLM/grounder could/should already map Russian natural name to canonical team login before Task API. If the first wrong boundary is actually semantic/team grounding, say so instead of patching Task API broadly.

# PHASE 5 — protected exact-task cluster
Confirm:
- DMS-380 point-read remains GREEN;
- DMS-999999999 remains authoritative NOT_FOUND/404.

# FINAL REPORT
Write:
`po-agent-platform-v2/qa_reports/ASSIGNEE_ZERO_RESULT_IDENTITY_FORENSIC_141.md`

Mandatory summary table:
| Cluster | Oracle truth | Agent/TaskAPI behavior | First failing boundary | Exact file/function | Owner fix ready? |

Allowed verdicts:
- `ASSIGNEE_ZERO_AND_IDENTITY_BOUNDARIES_PROVEN_OWNER_FIX_READY`
- `ASSIGNEE_ZERO_BOUNDARY_PROVEN_IDENTITY_MORE_FORENSIC`
- `ASSIGNEE_IDENTITY_BOUNDARY_PROVEN_ZERO_MORE_FORENSIC`
- `MORE_FORENSIC_REQUIRED`
- `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`

Final report MUST publish current exact Oracle B key sets/counts for Garanin and DMS, and enough sanitized Kalachanov identity rows to justify the resolution rule. No hand-waving and no skipped parity checks.

Commit/push QA evidence only and STOP.

## Start now
Execute Assignment 141 completely.