# LEARNING LOOP CONTRACT DISCOVERY - Assignment 094B

**Date:** 2026-08-26  
**Branch:** `feat/core8-real-query-hardening-v2`  
**Target HEAD:** `ea39619`  
**QA Role:** FORENSICS ONLY  
**Action:** Determine persistent learning capabilities from codebase

---

## EXECUTIVE SUMMARY

**VERDICT:** **NO_LEARNING_LOOP**

**Key Finding:** PO Agent (harness-dialogue-v2) does NOT have a persistent learning loop. It only provides runtime feedback/recheck via `CorrectionAwareHarnessRuntime`. All learned artifacts are transient (session-only) or require explicit human approval through governed promotion workflow.

---

## 1. CURRENT ARCHITECTURE ANALYSIS

### 1.1 Runtime Feedback Only

**Location:** `po_agent/harness/correction_runtime.py`

```python
class CorrectionAwareHarnessRuntime:
    """Force evidence revalidation on negative feedback and retain session context."""
    
    def __init__(self, inner) -> None:
        self.inner = inner
        self._last: dict[str, _PreviousTurn] = {}  # Session-only memory
        self._pending: dict[str, _CorrectionPending] = {}  # Session-only pending
```

**Evidence:**
- `self._last` - Session-only dictionary (in-memory)
- `self._pending` - Session-only dictionary (in-memory)
- Data lost on service restart

### 1.2 `persistent_skill_mutation = False`

**Evidence from 4 locations:**
- `correction_runtime.py:85`
- `correction_runtime.py:152`
- `semantic_correction_runtime_v2.py:47`
- `semantic_correction_runtime_v2.py:181`

```python
"harness": {
    "correction": {
        "persistent_skill_mutation": False,  # ALWAYS FALSE
    }
}
```

**Meaning:** Corrections are never persisted as skill mutations. They are only used for runtime feedback.

### 1.3 Failure Pattern Store

**Location:** `po_agent/evaluation/failure.py`

```python
class FailureStore:
    """Store for classified failures."""
    
    def __init__(self):
        """Initialize failure store."""
        self.failures: list[dict] = []  # In-memory only
```

**Evidence:**
- Failures stored in `self.failures` (in-memory list)
- No file persistence
- No database
- Lost on restart

### 1.4 Failure Miner

**Location:** `po_agent/evaluation/miner.py`

**Purpose:** Analyze historical failures to identify clusters/patterns

**Capabilities:**
- Routing confusion clustering
- Adapter/mapping issues
- Missing knowledge
- LLM schema issues
- Empty sprint edge cases
- Entity extraction issues

**Output:** Report only - NO automatic behavior changes

```python
class FailureMinerReport:
    """Report from failure mining."""
    def to_dict(self) -> dict:
        return {
            "total_failures": self.total_failures,
            "clusters": clusters,
            "timestamp": self.timestamp.isoformat(),
        }
```

### 1.5 Learned Semantics Store

**Location:** `po_agent/harness/learned_semantics.py`

**Purpose:** Versioned configuration learning for dialogue semantics

**Mechanism:**
```python
def learn_explicit_definition(
    self,
    *,
    term: str,
    meaning: str,
    source_trace_id: str,
    scope: str = "global",
) -> LearnedSemanticRule:
    # Stores rules in var/learned_semantics.json
    # Active rules stored with status="active"
    # Conflicting rules stored with status="pending"
```

**Evidence:**
- Rules stored in `var/learned_semantics.json` file
- Versioned rules with `status: active | pending`
- Scope: `global` or specific scope
- **BUT:** Only for explicit semantic definitions (term=meaning pairs)
- **NOT** for routing/source-selection policy updates

### 1.6 Learning Loop

**Location:** `po_agent/evolution/learning_loop.py`

**Purpose:** Controlled learning without production mutation

**Mechanism:**
```python
class LearningLoop:
    """Orchestrates candidate comparison without production mutation."""
    
    def compare(
        self,
        baseline: EvaluationSnapshot,
        candidate: EvaluationSnapshot,
    ) -> PromotionDecision:
        return self.gate.evaluate(baseline, candidate)
    
    def can_promote(self, decision: PromotionDecision, human_approved: bool = False) -> bool:
        """Promotion requires both a green gate and an explicit human decision."""
        return decision.decision == GateDecision.RECOMMEND and human_approved
```

**Evidence:**
- Baseline/candidate comparison
- Promotion gate with configurable thresholds
- **Human approval required** for production promotion
- Never auto-promotes

### 1.7 Shadow Cycle

**Location:** `po_agent/evolution/shadow_cycle.py`

**Purpose:** Failure → Proposal → Frozen Shadow Comparison

**Mechanism:**
```python
class LearningCycle013:
    """Create and shadow-evaluate a candidate from failure evidence."""
    
    def run_shadow(
        self,
        *,
        skill_id: str,
        skill_version: str,
        failures: Iterable[Mapping[str, Any]],
        baseline: EvaluationSnapshot,
        candidate: EvaluationSnapshot,
        corpus_id: str,
    ) -> ShadowCycleArtifact:
        # Validates frozen corpus
        # Builds proposal from failure cluster
        # Compares baseline vs candidate
        # Returns decision
```

**Evidence:**
- Requires `controlled_learning_orchestrator`
- Shadow evaluation on frozen corpus
- **Stops before production mutation**
- Delegates promotion policy to `LearningLoop` gate

### 1.8 Dialogue Runtime - Semantic Learning

**Location:** `po_agent/harness/dialogue_runtime.py`

**Mechanism:**
```python
if hint == "learn_semantic":
    rule = self.semantics.learn_explicit_definition(
        term=term, meaning=meaning, source_trace_id=trace, scope=scope
    )
    answer = (
        f"Запомнил правило «{rule.term}» = «{rule.meaning}»."
        if rule.status == "active"
        else "Новое правило конфликтует с уже активным. "
             "Я сохранил его как candidate и не изменил текущее поведение."
    )
```

**Evidence:**
- Only for explicit semantic definitions (`learn_semantic` intent)
- Creates versioned rules
- Conflicts stored as pending (no silent override)
- **NOT** for task lookup, routing, or source-selection rules

---

## 2. REQUIRED LEARNING CONTRACT - STATUS

| Requirement | Status | Evidence |
|-------------|--------|----------|
| User correction → failure classification | ⚠️ PARTIAL | `FailureClassifier.classify()` exists, but no automatic classification from runtime corrections |
| Failure classification → candidate behavior rule | ⚠️ PARTIAL | `FailureMiner.mine()` clusters failures, but no automatic rule synthesis from single corrections |
| Candidate behavior rule → safe validation against real source | ✅ EXIST | `ShadowCycle.run_shadow()` does offline shadow evaluation |
| Persistent learned rule | ❌ MISSING | No persistent storage of learned rules from runtime corrections |
| Future routing/source strategy uses rule | ❌ MISSING | No mechanism to apply learned rules to future routing/source-selection |
| Restart preserves rule | ❌ MISSING | Session memory lost; learned semantics only for explicit `learn_semantic` intent |
| Same semantic mistake avoided on DIFFERENT task | ❌ MISSING | No semantic generalization from corrections |
| Offline/shadow evaluation support | ✅ EXIST | `LearningCycle013` with shadow evaluation |
| Version promotion support | ✅ EXIST | `PromotionGate` with human approval workflow |
| Regression gate prevents degradation | ✅ EXIST | `PromotionGate.evaluate()` checks error rate and pass rate |

---

## 3. GAPS IDENTIFIED

### Gap 1: No Runtime→Persistent Learning Path

**Current Flow:**
```
User correction
  ↓
CorrectionAwareHarnessRuntime._attach_correction_meta()
  ↓
Sets persistent_skill_mutation=False
  ↓
Session-only correction metadata stored
  ↓
Next query starts fresh (session memory may persist, but no skill mutation)
```

**Required Flow (NOT IMPLEMENTED):**
```
User correction
  ↓
Failure classification
  ↓
Candidate behavior rule synthesis
  ↓
Offline/shadow evaluation on fresh corpus
  ↓
Promotion gate approval
  ↓
Persistent rule stored (file/db)
  ↓
Future routing uses learned rule
  ↓
Restart preserves rule
```

### Gap 2: No Semantic Generalization

**Current:** Corrections only apply to exact query/task

**Required:** Learn generalized rules like:
```
"When user says 'Нет, задача X не найдена, но она существует',
 THEN for future queries like 'Покажи Y' where Y is any task key,
 USE direct SWTR lookup instead of cache"
```

**Current Implementation:** None. Each correction is isolated.

### Gap 3: Session Memory ≠ Learning

**Session Memory (Present):**
```python
self._last: dict[str, _PreviousTurn] = {}
self._pending: dict[str, _CorrectionPending] = {}
```
- Lost on restart
- Per-session only
- Not applicable to other users/sessions

**Learned Rules (Limited):**
- Only via `learn_semantic` intent
- Only for term→meaning definitions
- Not for routing/source-selection

### Gap 4: No Automatic Rule Synthesis

**Current:** Rules only created via explicit `learn_semantic` intent

**Missing:** Automatic rule synthesis from:
- Repeated failure patterns
- User corrections
- Failure miner clusters

---

## 4. FORENSIC CONCLUSION

### 4.1 PO Agent Current Capabilities

| Capability | Status | Description |
|------------|--------|-------------|
| Runtime feedback/recheck | ✅ YES | `CorrectionAwareHarnessRuntime` provides recheck on negative feedback |
| Session memory | ✅ YES | Tracks previous queries/responses per session |
| Failure classification | ✅ YES | `FailureClassifier.classify()` categorizes failures |
| Failure mining | ✅ YES | `FailureMiner.mine()` clusters failures by pattern |
| Shadow evaluation | ✅ YES | `LearningCycle013` does offline comparison |
| Promotion gate | ✅ YES | `PromotionGate` enforces thresholds |
| Version promotion | ✅ YES | `PromotionManager` with human approval |
| Semantic learning | ⚠️ LIMITED | Only via explicit `learn_semantic` intent |
| Persistent learning | ❌ NO | No persistent storage from runtime corrections |
| Semantic generalization | ❌ NO | No pattern-to-rule synthesis from corrections |
| Routing rule updates | ❌ NO | No mechanism to update routing based on corrections |

### 4.2 Learning Loop Architecture (Present but Not Active)

```
┌─────────────────────────────────────────────────────────────┐
│                   LEARNING LOOP (Present)                    │
│  1. Failure → FailureMiner → Clusters → Proposal            │
│  2. Proposal → ShadowCycle → Baseline vs Candidate          │
│  3. ShadowCycle → LearningLoop → PromotionGate              │
│  4. PromotionGate → HumanApproval → PromotionManager        │
└─────────────────────────────────────────────────────────────┘
                        ▲
                        │
        ┌───────────────┴───────────────┐
        │  NOT INVOKED BY RUNTIME       │
        │  (Requires explicit trigger)  │
        └───────────────────────────────┘
```

### 4.3 Current Runtime Behavior (No Learning)

```
┌─────────────────────────────────────────────────────────────┐
│                   RUNTIME (Current)                          │
│  User correction → CorrectionAwareRuntime                    │
│    - Sets persistent_skill_mutation=False                    │
│    - Performs recheck                                        │
│    - Returns correction metadata (not persisted)             │
│    - Session memory only                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. VERDICT: NO_LEARNING_LOOP

**Rationale:**

1. ❌ **User correction does NOT create persistent learned rules**
   - `persistent_skill_mutation=False` hardcoded
   - Corrections only stored in session memory (`_last`, `_pending`)
   - Session memory lost on restart

2. ❌ **No semantic generalization**
   - Corrections only apply to exact query/task
   - No pattern-to-rule synthesis
   - No automatic rule creation from failure clusters

3. ✅ **Learning loop infrastructure exists but is NOT activated**
   - Shadow evaluation works
   - Promotion gate works
   - Human approval workflow exists
   - BUT: Requires explicit trigger, not invoked by runtime

4. ✅ **Offline learning paths exist but require manual intervention**
   - `LearningCycle013` can build proposals from failures
   - `FailureMiner` can cluster failures
   - BUT: No automatic invocation from runtime corrections

---

## 6. RECOMMENDATIONS

### To Implement Persistent Learning Loop:

1. **Add persistent storage** for learned rules (beyond `learn_semantic`)
   - File: `var/learned_routing_rules.json`
   - Database: SQLite/PostgreSQL for routing rules

2. **Auto-invoke learning cycle** on failure
   - `CorrectionAwareHarnessRuntime` → `LearningCycle013` on negative feedback
   - Generate proposals from failure patterns

3. **Enable semantic generalization**
   - Extract patterns from corrections (e.g., "task not found" → "use direct SWTR")
   - Apply patterns to similar future queries

4. **Add automatic rule promotion**
   - After shadow evaluation passes, auto-promote (configurable)
   - Or require human approval for each rule

5. **Document learning contract explicitly**
   - What can be learned?
   - What cannot be learned?
   - How to inspect learned rules?
   - How to revert learned rules?

---

## 7. APPENDIX A: KEY CODE LOCATIONS

### Runtime Feedback (Present)
- `po_agent/harness/correction_runtime.py` - Session-only correction handling
- `po_agent/harness/semantic_correction_runtime_v2.py` - Session-only correction

### Failure Handling (Present)
- `po_agent/evaluation/failure.py` - FailureStore (in-memory)
- `po_agent/evaluation/failure.py` - FailureClassifier
- `po_agent/evaluation/miner.py` - FailureMiner (pattern clustering)

### Learning Infrastructure (Present but Not Activated)
- `po_agent/evolution/learning_loop.py` - PromotionGate, LearningLoop
- `po_agent/evolution/shadow_cycle.py` - ShadowCycle (offline evaluation)
- `po_agent/evolution/improvement_synthesizer.py` - Proposal synthesis

### Explicit Semantic Learning (Limited)
- `po_agent/harness/learned_semantics.py` - LearnedSemanticsStore
- `po_agent/harness/dialogue_runtime.py` - `learn_semantic` intent handler

### Promotion Workflow (Present)
- `po_agent/shadow/promotion.py` - PromotionManager
- `po_agent/shadow/gate.py` - RegressionGate
- `po_agent/api/orchestrator.py` - `/api/v1/promotions/promote` endpoint

---

**Report Generated:** 2026-08-26  
**QA Forensics By:** GigaCode  
**Branch:** `feat/core8-real-query-hardening-v2`  
**Commit:** `ea39619ed7287651b405bdb6f02193fbeb4757e6`
