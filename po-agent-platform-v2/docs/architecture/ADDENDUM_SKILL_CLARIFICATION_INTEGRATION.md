# ADDENDUM SKILL CLARIFICATION INTEGRATION MAP
## PO Agent Platform v2.1 -> ADDENDUM 01 Mapping

**Date:** 2026-08-12  
**Current Version:** PO Agent Platform v2.1  
**Target:** ADDENDUM 01 - Clarification Engine + Skill Registry + Skill Evolution  
**Status:** AUDIT COMPLETE

---

## EXECUTIVE SUMMARY

| ADDENDUM Requirement | Current State | Reusability | Action |
|---------------------|---------------|-------------|--------|
| Intent Router | `DeterministicIntentRouter` | 90% | MINOR changes |
| Context Resolver | Implicit via entities + session_memory | 60% | MODERATE changes |
| Session Memory | `SessionMemory` with TTL | 70% | MODERATE changes |
| Clarification Engine | NOT IMPLEMENTED | 0% | NEW |
| Skill Registry | Hardcoded in orchestrator | 30% | MAJOR changes |
| Skill Resolver | `DeterministicIntentRouter` | 80% | REFACTOR |
| Skill Executor | `POOrchestratorV1._execute_capability()` | 50% | REFACTOR |
| Trace | `TraceRecord` model | 80% | EXTEND |
| Feedback | `FeedbackStore` | 70% | EXTEND |
| Eval/Metrics | `MetricsEngine` | 40% | MAJOR changes |
| Version Registry | `VersionRegistry` | 70% | MODERATE changes |
| Improvement Pipeline | `ImprovementCandidate` | 60% | MODERATE changes |

---

## DETAILED COMPONENT MAPPING

### 1. Intent Router / Orchestrator

| Aspect | Current (v2.1) | Target (ADDENDUM 01) | Mapping |
|--------|----------------|---------------------|---------|
| **Location** | `orchestration/router.py:DeterministicIntentRouter` | New `IntentRouter` + `SkillResolver` | **REUSE + MOD** |
| **Method** | Deterministic regex matching | Deterministic mapping with LLM fallback | **REUSE** |
| **LLM Fallback** | `LLIntentFallback` | Only for ambiguous requests | **REUSE** |
| **Allowlist** | Intent patterns dict | Explicit skill registry | **MOD** |
| **Intents** | task_search, task_summary, task_quality, sprint_health, velocity, team_workload, competency_match, release_health, help | skill_id with versioning | **MOD** |

**Risk:** LOW - Router already well-designed

---

### 2. Context Resolver

| Aspect | Current (v2.1) | Target (ADDENDUM 01) | Mapping |
|--------|----------------|---------------------|---------|
| **Model** | `IntentClassification.entities` | `ResolvedContext` model | **EXTEND** |
| **Fields** | entities list | `product`, `sprint_id`, `release_id`, `task_id`, `member_login`, `date_range`, `attachment_type` | **EXTEND** |
| **Source Tracking** | None | `current_request`, `clarification_answer`, `session_memory`, `deterministic_lookup`, `approved_curated_memory` | **NEW** |
| **Priority** | No explicit priority | `current > clarification > session > curated > default` | **NEW** |
| **Output** | `IntentClassification` | `ResolvedContext` + `needs_clarification` | **MOD** |

**Risk:** MEDIUM - Need to create `ResolvedContext` model with source tracking

---

### 3. Session Memory / Context Storage

| Aspect | Current (v2.1) | Target (ADDENDUM 01) | Mapping |
|--------|----------------|---------------------|---------|
| **Storage** | `SessionMemory` with TTL | File-based + in-memory | **MOD** |
| **Pending Request** | `clarification_state` | Full `pending_request` object | **EXTEND** |
| **Fields** | `current_sprint`, `current_product`, `selected_member`, `referenced_task`, `clarification_state` | `original_query`, `intent`, `extracted_entities`, `missing_fields`, `clarification_id`, `created_at`, `expires_at` | **EXTEND** |
| **Persistence** | In-memory only | File at `~/.task-tracker/pending_request.json` | **NEW** |
| **Expiration** | TTL (default 1hr) | TTL-based expiration | **REUSE** |

**Risk:** MEDIUM - Need to add file persistence

---

### 4. Clarification Engine

| Aspect | Current (v2.1) | Target (ADDENDUM 01) | Mapping |
|--------|----------------|---------------------|---------|
| **Existence** | NOT IMPLEMENTED | Full engine | **NEW** |
| **NEEDS_CLARIFICATION** | Not returned status | Status for `AnalysisResult` | **NEW** |
| **ClarificationRequest** | None | `clarification_id`, `reason`, `missing_fields`, `question`, `options`, `original_intent`, `original_query` | **NEW** |
| **Question Format** | Error messages | Short, specific, with deterministic options | **NEW** |
| **LLM Options** | N/A | Options from code (product list, sprint list, etc.) | **NEW** |

**Risk:** CRITICAL - New feature, major implementation required

---

### 5. Skill Registry / Resolver / Executor

| Aspect | Current (v2.1) | Target (ADDENDUM 01) | Mapping |
|--------|----------------|---------------------|---------|
| **Registry** | Hardcoded in `POOrchestratorV1.__init__()` | `SkillRegistry` class | **REFACTOR** |
| **Skill Model** | None | `SkillDefinition` model | **NEW** |
| **Fields** | None | `skill_id`, `name`, `version`, `status`, `intents`, `required_context`, `optional_context`, `clarification_policy`, `allowed_capabilities`, `workflow`, `output_contract`, `prompt_references`, `fallback_policy`, `eval_tags` | **NEW** |
| **Versioning** | None | `candidate/active/deprecated/rejected` | **NEW** |
| **Resolver** | `DeterministicIntentRouter` | Deterministic `intent -> skill` mapping | **REFACTOR** |
| **Executor** | `_execute_capability()` | Validate skill, check context, execute workflow, write trace | **REFACTOR** |

**Risk:** HIGH - Need new `SkillDefinition` model and registry

---

### 6. Trace / History

| Aspect | Current (v2.1) | Target (ADDENDUM 01) | Mapping |
|--------|----------------|---------------------|---------|
| **Existence** | `TraceRecord` | Full trace with metadata | **EXTEND** |
| **Fields** | trace_id, request_id, session_id, intent, confidence, entities, capability_calls, adapter_calls, llm_calls, evidence_refs, warnings, errors, latency_ms | + `skill_id`, `skill_version`, `context_sources`, `clarification_count`, `clarification_ids`, `pending_request_used`, `skill_execution_steps` | **EXTEND** |
| **Storage** | `TraceRecorder.traces` list | File-based or SQLite | **MOD** |

**Risk:** LOW - Existing trace model is flexible

---

### 7. Feedback / Failure Taxonomy

| Aspect | Current (v2.1) | Target (ADDENDUM 01) | Mapping |
|--------|----------------|---------------------|---------|
| **Existence** | `FeedbackStore` | Full feedback system | **EXTEND** |
| **Failure Types** | None | `CONTEXT_RESOLUTION_ERROR`, `MISSING_CLARIFICATION`, `UNNECESSARY_CLARIFICATION`, `CLARIFICATION_LOOP_ERROR`, `SKILL_SELECTION_ERROR`, `SKILL_CONTRACT_ERROR`, `SKILL_WORKFLOW_ERROR`, `SKILL_KNOWLEDGE_GAP` | **NEW** |
| **Linking** | `trace_id` | Link to `trace_id`, `skill_id`, `skill_version` | **EXTEND** |

**Risk:** LOW - Feedback model exists, needs taxonomy extension

---

### 8. Eval / Metrics

| Aspect | Current (v2.1) | Target (ADDENDUM 01) | Mapping |
|--------|----------------|---------------------|---------|
| **Existence** | `MetricsEngine` | Full eval system | **REFACTOR** |
| **Metrics** | None specified | `Task Success Rate`, `First-pass Correctness`, `Clarification Success Rate`, `Context Resolution Accuracy`, `Skill Selection Accuracy`, `Skill Success Rate`, `Human Correction Rate`, `Grounded Answer Rate`, `Deterministic Fast-path Rate`, `Regression Escape Rate` | **NEW** |
| **Shadow Eval** | `shadow/` module exists | Run candidate skills and compare | **REUSE + MOD** |

**Risk:** MEDIUM - Need new metric definitions

---

### 9. Skill Evolution

| Aspect | Current (v2.1) | Target (ADDENDUM 01) | Mapping |
|--------|----------------|---------------------|---------|
| **Existence** | `ImprovementCandidate` | Full evolution pipeline | **REUSE + MOD** |
| **Improvement Candidate** | `ImprovementCandidate` | `candidate_id`, `skill_id`, `base_version`, `proposed_version`, `linked_traces/evals`, `failure_categories`, `change_type`, `rationale`, `proposed_definition`, `expected_benefit`, `risk_level`, `status` | **REUSE + EXTEND** |
| **Trigger** | None specified | Repeated failure clusters, high severity, owner command | **NEW** |
| **Auto-activation** | `ImprovementCandidate.approve()` | NEVER - requires human approval | **REUSE POLICY** |

**Risk:** MEDIUM - Candidate model exists, needs workflow refinement

---

### 10. API / UI

| Aspect | Current (v2.1) | Target (ADDENDUM 01) | Mapping |
|--------|----------------|---------------------|---------|
| **Status Values** | N/A | `COMPLETED`, `NEEDS_CLARIFICATION`, `PARTIAL`, `FAILED` | **NEW** |
| **Clarification Response** | Error messages | `status`, `clarification_id`, `question`, `options`, `trace_id` | **NEW** |
| **UI Clarification** | N/A | Normal part of conversation | **NEW** |
| **Deterministic Options** | None | Button-based quick choices | **NEW** |
| **Admin UI** | `dashboard/` module exists | Active Skills, versions, candidates, eval scores, rollback | **REUSE + MOD** |

**Risk:** MEDIUM - UI changes required

---

## ARCHITECTURE IMPACT ANALYSIS

### Files to CREATE
1. `src/po_agent/models/resolved_context.py` - ResolvedContext model
2. `src/po_agent/models/skill_definition.py` - SkillDefinition model
3. `src/po_agent/clarification/engine.py` - Clarification Engine
4. `src/po_agent/clarification/models.py` - Clarification models
5. `src/po_agent/skill/registry.py` - Skill Registry
6. `src/po_agent/skill/executor.py` - Skill Executor
7. `src/po_agent/skill/models.py` - Skill models (with versioning)
8. `src/po_agent/evaluation/metrics.py` - Quality metrics
9. `src/po_agent/context/persistence.py` - Context persistence
10. `docs/architecture/ADDENDUM_SKILL_CLARIFICATION_INTEGRATION.md` - This file

### Files to MODIFY
1. `src/po_agent/orchestration/router.py` - Refactor to use SkillRegistry
2. `src/po_agent/orchestration/llm_fallback.py` - Update for new intent flow
3. `src/po_agent/orchestration/orchestrator.py` - Integrate SkillResolver, SkillExecutor
4. `src/po_agent/orchestration/__init__.py` - Export new modules
5. `src/po_agent/memory/session_memory.py` - Add pending_request fields, file persistence
6. `src/po_agent/observability/trace.py` - Extend TraceRecord with skill metadata
7. `src/po_agent/feedback/store.py` - Add failure taxonomy
8. `src/po_agent/evaluation/miner.py` - Update for new failure categories
9. `src/po_agent/improvement/candidate.py` - Add skill_id reference
10. `src/po_agent/versions/registry.py` - Add skill versioning
11. `src/po_agent/dashboard/api.py` - Add skill lifecycle UI

### Files to REUSE (NO CHANGES)
1. `src/po_agent/llm/client.py` - LLM client unchanged
2. `src/po_agent/llm/mock.py` - Mock LLM unchanged
3. `src/po_agent/domain/models.py` - Domain models unchanged
4. `src/po_agent/config/team.py` - Team config unchanged

---

## INTEGRATION RISK MATRIX

| Module | Complexity | Risk Level | Dependencies | Notes |
|--------|-----------|------------|--------------|-------|
| ResolvedContext model | Low | LOW | None | New model |
| Clarification Engine | High | CRITICAL | Context Resolver, Skill Registry | Major feature |
| Skill Registry | Medium | HIGH | SkillDefinition, models | New system |
| Skill Executor | Medium | MEDIUM | SkillRegistry | New execution model |
| Context Persistence | Medium | MEDIUM | SessionMemory | File-based |
| API Changes | Medium | MEDIUM | Dashboard | Status enum changes |
| Evaluation Metrics | Medium | MEDIUM | Eval | New metric definitions |

---

## PHASED IMPLEMENTATION PLAN

| Step | Component | Est. Files | Risk | Order |
|------|-----------|------------|------|-------|
| 1 | ResolvedContext Model | 1 file | LOW | First |
| 2 | Context Resolver Enhancements | 2 files | MEDIUM | After 1 |
| 3 | Clarification Engine | 4 files | CRITICAL | After 2 |
| 4 | Skill Definition Model | 3 files | MEDIUM | Parallel |
| 5 | Skill Registry | 2 files | HIGH | After 4 |
| 6 | Skill Executor | 2 files | HIGH | After 5 |
| 7 | Context Persistence | 1 file | MEDIUM | After 2 |
| 8 | API/UI Updates | 4 files | MEDIUM | After 3, 4 |
| 9 | Evaluation Metrics | 2 files | MEDIUM | After 5 |
| 10 | Full Integration | 10 files | HIGH | After 1-9 |

**Total Estimation:** 30 files created/modified across 10 phases

---

## NEXT STEPS

### Immediate (ADD-STEP 02)
1. Create `ResolvedContext` model
2. Implement context resolver with precedence policy
3. Add tests

### After ADD-STEP 02 approval:
1. Implement Clarification Engine
2. Add pending request management
3. Add tests

### And so on...

---

**AUDIT COMPLETED: YES**  
**READY FOR ADD-STEP 02: PENDING USER APPROVAL**  
**PRODUCTION IMPACT: NO CHANGES MADE**
