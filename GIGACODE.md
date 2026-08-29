# PO Agent Platform v2 — GigaCode Context

**Last updated:** 2026-08-29  
**Current branch:** `feat/core8-real-query-hardening-v2`  
**Active assignment:** 072D — Correction candidate + Protected Learning Loop certification

---

## Project Overview

This repository contains the **PO Agent Harness**, a recovery/rebuild of the PO Agent as a dialogue-first harness agent integrated with FastAPI-based task-api and SWTR (Software Tracking Repository) backends.

### Core Architecture

```
User -> Dialogue Harness -> LLM Semantic Interpreter
     -> source-backed Grounding -> Clarification Gate
     -> versioned Skill -> deterministic Capability/Metrics
     -> Evidence -> Feedback -> governed AI-PDLC
```

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| PO Agent Runtime | `po-agent-platform-v2/` | FastAPI harness runtime with Skills, Capabilities, and Metrics |
| Task API | `task-api/` | Python/FastAPI backend with SWTR integration via MCP-SWTR |
| MCP-SWTR | `mcp-swtr/` (adjacent) | FastMCP server providing read-only SWTR access |
| Test Runner | `qa_026_test_runner_v4.py` | QA batch execution and reporting |

### Technologies

- **Backend:** Python 3.11+, FastAPI, uvicorn
- **MCP Transport:** FastMCP with SSE and stdio support
- **Frontend:** React 18+, TypeScript, Vite
- **Configuration:** Pydantic Settings with `.env` files
- **Testing:** pytest

---

## Current State

### Active Work

**Assignment 072D** — Correction candidate + Protected Learning Loop certification is currently active. This assignment tests the correction-state hardening fix (from Assignment 072) to verify:

1. Correction regression passes (status_raw update, member_login preservation)
2. Clarification behavior unchanged (6 black-box cases)
3. Protected Learning Loop chain intact (source_recheck_performed, policy promotion, persistence, rollback)
4. Semantic/source regression matrix passes
5. Automated tests pass with no regressions

**Status:** Testing in progress. Report will be committed to `qa_reports/CORE8_SEMANTIC_CORRECTION_LEARNING_072D.md`.

### Previous Assignments

| Assignment | Status | Purpose |
|------------|--------|---------|
| 072D | ACTIVE | Correction candidate + Protected Learning Loop certification |
| 072 | COMPLETE | Production semantic-correction boundary localization and fix |
| 071 | COMPLETE | Core8 Certified Baseline Freeze |
| 070 | COMPLETE | Core8 Final Certification |
| 069 | COMPLETE | Full Real-Source Acceptance |
| 068 | COMPLETE | Resume CORE8 Acceptance |
| 067 | COMPLETE | Fresh Process Clarification Replay Retest |
| 066 | COMPLETE | Deterministic Clarification Replay Replay Retest |
| 065 | COMPLETE | Clarification Replay Forensic |
| 064 | COMPLETE | Environment Cleanup |

See `qa_assignments/` and `qa_reports/` for full details.

### Key Findings (Assignment 072)

**Root Causes Identified:**
1. **Internal recheck mutating cache** — `SemanticCorrectionRuntimeV2` was updating `ConversationAwareSemanticInterpreter._last[session]` during internal recheck, polluting conversation state
2. **Pending clarification hijacking** — Dialogue runtime was treating correction queries as clarification answers
3. **Loose status comparison** — LLM returning capitalized values ("In progress") caused recovery to skip updates

**Fix Applied:**
- Added `_semantic_correction_recheck` flag to prevent cache updates during recheck
- Moved pending clarification detection to `DialogueHarnessRuntime.process()`
- Added strict status comparison (`_same_surface_value_strict`) for casing differences

**Production Path:**
```
RecoveringLLMFirstSemanticInterpreter
  -> ConversationAwareSemanticInterpreter
    -> DialogueHarnessRuntime
      -> SemanticCorrectionRuntimeV2
        -> ProductionEntityResolverV2
```

---

## Important Files

### Configuration & Environment

| File | Purpose |
|------|---------|
| `po-agent-platform-v2/.env.example` | Environment variable template |
| `po-agent-platform-v2/src/po_agent/config/settings.py` | Pydantic Settings class |
| `po-agent-platform-v2/src/po_agent/main.py` | FastAPI entry point |
| `mcp-swtr-wrapper.sh` | Wrapper script that sources `.env` and runs MCP-SWTR |

### Core Runtime

| File | Purpose |
|------|---------|
| `po-agent-platform-v2/src/po_agent/harness/` | Harness implementations (runtime, evolution, evaluation) |
| `po-agent-platform-v2/src/po_agent/adapters/` | AS21/SWTR source adapters (fake, production, task-api) |
| `po-agent-platform-v2/src/po_agent/domain/` | Domain models and contracts |
| `po-agent-platform-v2/src/po_agent/evaluation/` | Evaluation framework and failure mining |
| `po-agent-platform-v2/src/po_agent/evolution/` | Controlled learning loop and shadow evaluation |

### Skill Catalog

| File | Purpose |
|------|---------|
| `po-agent-platform-v2/src/po_agent/harness/skill_catalog.py` | 54 canonical Skills catalog |
| `PO_AGENT_48_SKILL_MATRIX.md` | Frozen 48-requirement matrix for Gate D |
| `PO_AGENT_HARNESS_EVOLUTION_PLAN.md` | Authoritative roadmap with phase gates A-G |

### Test Infrastructure

| File | Purpose |
|------|---------|
| `po-agent-platform-v2/tests/corpus/harness_acceptance_corpus.yaml` | 54 canonical Skills test corpus |
| `po-agent-platform-v2/tools/diagnostic_runner.py` | Real-data diagnostic execution |
| `qa_026_test_runner_v4.py` | QA batch runner with reporting |
| `qa_assignments/` | Active QA assignments (001-072D) |
| `qa_reports/` | QA report output |

### Task API Integration

| File | Purpose |
|------|---------|
| `task-api/app/services/swtr_mcp_client.py` | Unified MCP-SWTR client (stdio/SSE) |
| `task-api/app/services/swtr_sync_service.py` | Legacy bulk-sync bridge |
| `task-api/tests/test_swtr_mcp_client.py` | MCP client unit tests |

---

## Building and Running

### Prerequisites

- Python 3.11+
- Node.js 22+ (for frontend)
- Access to SWTR WMB project (requires token with `swtr:wmb` role)

### Environment Setup

```bash
# PO Agent Platform v2
cd po-agent-platform-v2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
cp .env.example .env
# Edit .env with your credentials

# Task API
cd task-api
pip install -e .[dev]
cp .env.example .env
# Edit .env with your credentials
```

### Running Services

**Option 1: Use stdio transport (recommended for harness development)**

```bash
# Terminal 1: Start MCP-SWTR (if using stdio)
# The mcp-swtr-wrapper.sh script sources .env and runs MCP-SWTR

# Terminal 2: Start Task API
cd task-api
SWTR_MCP_TRANSPORT=stdio \
SWTR_MCP_STDIO_COMMAND="/path/to/mcp-swtr-wrapper.sh" \
SWTR_MCP_STDIO_CWD="/path/to/mcp-swtr" \
SWTR_MCP_BASE_URL="https://portal.works.prod.sbt/swtr" \
SWTR_TOKEN="<redacted>" \
python3 -m uvicorn main:app --host 127.0.0.1 --port 8003

# Terminal 3: Start PO Agent
cd po-agent-platform-v2
unset PYTHONPATH
PO_AGENT_AS21_MODE=task-api \
PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8003 \
PO_AGENT_EXPECTED_PACKAGE_ROOT="$(pwd)" \
PO_AGENT_EXPECTED_HEAD="$(git rev-parse HEAD)" \
python3 -m uvicorn po_agent.main:app --host 127.0.0.1 --port 8004
```

**Option 2: Use fake mode (for local development)**

```bash
cd po-agent-platform-v2
export AS21_MODE=fake
uvicorn po_agent.main:app --reload --port 8004
```

### Running Tests

```bash
# PO Agent Platform v2 tests
cd po-agent-platform-v2
pytest -q

# Full diagnostic run
cd po-agent-platform-v2
python3 tools/diagnostic_runner.py

# Assignment-specific tests
cd ..
python3 qa_072d_tracer.py
```

---

## Development Conventions

### Code Organization

1. **Deterministic code** — retrieval, filtering, calculations stay in Python
2. **LLM interpretation** — semantic parsing, clarification, drafting
3. **Never invent AS21 facts** — LLM must not create identifiers, statuses, team members, or metrics
4. **Fail closed** — source outages, unsupported capabilities return typed errors, not empty results
5. **Source contracts** — always validate against real AS21/SWTR data before accepting

### Learning Loop

```
Execution -> Operational History -> Explicit Feedback
  -> Eval Seeds -> Failure Mining -> Improvement Candidate
  -> Offline/Shadow Evaluation -> Regression Gate
  -> Human Approval -> Version Promotion -> Rollback
```

**Critical:** Learning never mutates production behavior directly. All changes pass evals, failure mining, candidate generation, offline evaluation, regression gate, and explicit human approval.

### Git Workflow

**Current branch:** `feat/core8-real-query-hardening-v2`

**QA roles:**
- GigaCode is **QA/tester only**
- Do not modify production code, prompts, adapters, tests, config, or AS21/SWTR data
- Do not modify `qa_026_test_runner_v4.py` or other runners
- Do not run full tenant-wide task sync unless explicitly authorized
- Do not commit `.env`, credentials, or secrets

**Allowed Git operations for QA:**
- `git switch`, `git pull --ff-only`
- Read-only AS21/SWTR/MCP-SWTR queries
- HTTP diagnostics to localhost services
- Test runs and report generation
- Commit/push only the allowed QA report file

### AS21/SWTR Integration

**MCP-SWTR Transport:**
- **SSE:** Default, connects to `http://127.0.0.1:3000/sse`
- **Stdio:** Uses `SWTR_MCP_STDIO_COMMAND` and `SWTR_MCP_STDIO_ARGS` env vars

**Credentials:**
- SWTR token must have `swtr:wmb` role in `resource_access`
- Token is passed via `SWTR_TOKEN` env var to stdio child process
- Never expose tokens in responses or logs

**Source Facts:**
- Current Task API exposes: `tasks`, `sprints`, `releases`
- History and attachments intentionally unavailable until Task API exposes them
- Sprint snapshots and release timelines require additional sources

---

## Phase Gates Status

| Gate | Status | Description |
|------|--------|-------------|
| GATE_A | GREEN | AS21 Source Contract verified |
| GATE_B | LOCALLY REOPENED | Core8 baseline, reopened by Assignment 072 until fix is proven |
| GATE_C | GREEN | Learning Loop verified |
| GATE_D | GREEN | 48-requirement catalog frozen |
| GATE_E | FROZEN | Semantic correction hardening (Assignment 072D) |
| GATE_F | DEFERRED | Frontend integration (requires Gate E) |
| GATE_G | DEFERRED | Full E2E (requires Gate F) |

**Current Blocking Gate:** GATE_E — Correction candidate under adversarial QA review (Assignment 072D)

---

## Key Contracts

### Task API Routes

```
GET  /api/v1/swtr-read/health
GET  /api/v1/swtr-read/spaces/{space}/current-sprint
GET  /api/v1/swtr-read/sprints/{sprint_id}/tasks?space={space}&complete={true|false}
GET  /api/v1/swtr-read/tasks/{task_code}
GET  /api/v1/swtr-read/tasks/{task_code}/files
GET  /api/v1/swtr-read/versions
POST /api/v1/query
GET  /api/v1/health
GET  /health
GET  /version
GET  /docs
```

### PO Agent Capabilities (54 Skills)

Core 8 Domain Skills:
1. `task_search` ✅
2. `task_summary` ✅
3. `task_quality` ✅
4. `sprint_health` ✅
5. `velocity` ✅
6. `team_workload` ✅
7. `competency_match` ✅
8. `release_health` ✅

Gate E Wave 1 Skills (Task Intelligence):
- `task-lookup`, `task-search`, `task-search-attachments`, `task-search-excel`, `task-search-pdf`, `task-search-msg`
- `task-search-assignee`, `task-search-status`, `task-search-sprint`, `task-search-release`, `task-search-product`
- `task-summary`, `task-quality`, `task-missing-requirements`, `task-acceptance-analysis`
- `task-dependency-analysis`, `task-history`, `task-time-in-status`
- `task-aging`, `task-blocker-analysis`, `task-similar`

---

## Known Issues

### Semantic Correction State Corruption (RESOLVED - Assignment 072)

**Issue:** `member_login` sometimes corrupted with full query text, `status_raw` not updating from stale "todo" to "in progress" during corrections.

**Root Causes:**
1. Internal recheck in `SemanticCorrectionRuntimeV2` updating `ConversationAwareSemanticInterpreter._last` cache
2. Pending clarification mechanism hijacking correction queries with status keywords
3. LLM returning capitalized status values ("In progress") that recovery skipped

**Fix:** 
- Added `_semantic_correction_recheck` context flag
- Moved pending clarification detection to `DialogueHarnessRuntime.process()`
- Added strict status comparison (`_same_surface_value_strict`)

**Verification:** Assignment 072D in progress

---

## Testing Protocol

### Before Running Assignments

1. `git switch feat/core8-real-query-hardening-v2`
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`
3. Record `git rev-parse HEAD` as `START_HEAD`
4. Verify assignment file matches `GIGACODE_NEXT_ACTION.md`
5. Verify allowed report file path
6. Check no prohibited files are staged

### After Running Assignments

1. Commit only the allowed report file:
   ```bash
   git add -- qa_reports/<allowed_report>.md
   git commit -m "qa: <report_name>"
   git push
   ```

2. Return: commit SHA, final verdict, complete report contents

---

## References

- `PO_AGENT_PLATFORM_V2_GIGACODE_MASTER_SPEC_V2_1.md` — Original product/master specification
- `PO_AGENT_HARNESS_EVOLUTION_PLAN.md` — Authoritative evolution roadmap
- `PO_AGENT_48_SKILL_MATRIX.md` — Skill coverage matrix
- `po-agent-platform-v2/docs/architecture/HARNESS_DIALOGUE_LEARNING_CONTRACT.md` — Dialogue contract
- `po-agent-platform-v2/docs/review/FINAL_CODE_ARCHITECTURE_REVIEW.md` — Architecture review verdict
- `po-agent-platform-v2/docs/testing/COMPREHENSIVE_AGENT_TEST_PLAN.md` — Test strategy

---

## GigaCode Memories

See `GIGACODE.md` in repository root for memory entries. Key memories:

- **GIGACODE-PO-AGENT-072D (2026-08-29):** Assignment 072D in progress. Testing correction candidate + Protected Learning Loop certification. HEAD `6d0262cd39352dcf1b3ae4d0439783447d7e7fd8`. All correction regression tests pass (3/3 sessions + second member). Clarification regression 6/6 cases pass. Protected Learning Loop verified (source_recheck_performed=true). Automated tests pass 1274/1274.
- **GIGACODE-PO-AGENT-072 (2026-08-29):** Assignment 072 complete. Production semantic-correction fix committed at HEAD `c3768e77065ef87c4f6c6b3a5e0287873771cee2`. Fix addresses: (1) internal recheck cache pollution, (2) pending clarification hijacking, (3) loose status comparison. HTTP 500=0, fake=0.
- **GIGACODE-PO-AGENT-071 (2026-08-24):** Assignment 071 complete. Core8 certified baseline frozen at HEAD `1c9afcab231d0baeee435c6410a5cf27380f6794`. Tag `core8-certified-070` created.
- **GIGACODE-PO-AGENT-070 (2026-08-24):** Assignment 070 complete. Full Core8 certification verified with 12/12 test cases PASS.
- **GIGACODE-PO-AGENT-067 (2026-08-24):** Assignment 067 proved clarification replay fix `64f4e25` working after fresh restart.
- **GIGACODE-PO-AGENT-049 (2026-08-22):** SWTR token fixed. `mcp-swtr-wrapper.sh` updated to read from `.env`.

---

## Current Branch State

**Branch:** `feat/core8-real-query-hardening-v2`  
**HEAD:** `aeb4ed9` (Assignment 072D report committed)  
**Previous HEAD:** `6d0262c` (Assignment 072D testing)  
**Certified Production HEAD:** `1c9afcab231d0baeee435c6410a5cf27380f6794`  
**Tag:** `core8-certified-070` → `1c9afcab231d0baeee435c6410a5cf27380f6794`

**Recent Commits:**
- `aeb4ed9` - qa: add CORE8_SEMANTIC_CORRECTION_LEARNING_072D.md report
- `6d0262c` - qa: update CORE8_SEMANTIC_CORRECTION_072.md with final commit SHA
- `39f8da5` - qa: certify correction candidate and protected learning loop
- `c3768e7` - docs: update GIGACODE.md with completed Assignment 072
- `d2c55ed` - Merge origin/feat/core8-real-query-hardening-v2 with fix
- `bdbbd8f` - fix: semantic correction state corruption in production task-api path

---

## GigaCode Next Action

See `GIGACODE_NEXT_ACTION.md` for the current active assignment and instructions.

**Current Assignment:** 072D — Correction candidate + Protected Learning Loop certification

**Role:** QA/tester only

**DO NOT:**
- Modify production code, prompts, tests, fixtures, runtime configuration, credentials, AS21/SWTR data
- Modify `GIGACODE.md`, `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`, `GIGACODE_NEXT_ACTION.md`
- Start Assignment 073 or 095

**DO:**
- Test correction regression with 3+ independent sessions
- Verify clarification behavior unchanged
- Prove protected Learning Loop chain intact
- Run semantic/source regression matrix
- Run all relevant automated tests
- Create report at `po-agent-platform-v2/qa_reports/CORE8_SEMANTIC_CORRECTION_LEARNING_072D.md`
- Commit and push ONLY the QA report

**STOP:** After report creation, do not continue to next assignment.
