# Playwright H0 Browser Final Certification — Assignment 155

**Date:** 2026-09-04
**Branch:** `feat/core8-real-query-hardening-v2`
**HEAD:** `985f485dd7949e4d521c30f47f0235bb62711e21`
**Status:** `H0_SESSION_ISOLATION_RED - Session ID Mismatch Between sessionStorage and Backend Response`

## Mission Summary

Close H0 after Assignment 154 proved the remaining RED is only an unavailable Playwright request-body observation, not production session propagation. The test harness now proves end-to-end session identity from browser sessionStorage to backend response and UI trace.

**QA Only. Do not modify production/backend/frontend/test source code.**

## Owner/Test Harness Fixes Verified

| Commit | Purpose |
|--------|---------|
| `2cf89fcb3e60db9d274f510dcb467dc00684e1af` | Production fix: `send()` reads authoritative tab session from `sessionStorage` at send-time |
| `1386f22c05cb3540f929c323b66705c71d42e61d` | Test harness: No longer depends on Playwright POST-body visibility; proves end-to-end session identity |

**Verification:**
- `2cf89fcb` is ancestor: ✅
- `1386f22c` is ancestor: ✅

## Phase 0 — Provenance/Build ✅

### 1. Pull & HEAD
```
HEAD: 985f485dd7949e4d521c30f47f0235bb62711e21
Branch: feat/core8-real-query-hardening-v2
Clean/Dirty: Modified .po_agent/learned_policies.json (data file)
```

### 2. Owner/Test Commit Ancestry
```
2cf89fc - is ancestor ✅
1386f22 - is ancestor ✅
```

### 3. Frontend Build
```
npm run build: SUCCESS (570ms)
```

### 4. Runtime Verification
```
Backend v3 (8004): HEALTHY, agent_core_v3_enabled=true, semantic_mode=qwen-llm, source_status=healthy
Frontend (5175): RUNNING
Playwright: Version 1.62.1, Chromium installed
```

## Phase 1 — Machine Session Isolation Proof ❌

### Test Executed
```
Command: npm run e2e:h0 -- --grep "session isolation"
Test: session isolation and new conversation are real browser behavior
```

### Results

```
Status: FAILED

Error at line 106:
  Expected: "ui-c9a4a9e7-4259-427b-8af5-f867913960c5" (resetSession after New dialogue)
  Received: "b0376e75-ab0f-4d87-9d04-6d025d7ea140" (backend payload.session_id)
```

### Evidence from Test Artifacts

**Session Flow Analysis:**
```
1. const firstSession = await sessionId(first) → ui-??? (initial session after openAgent)
2. await first.getByRole('button', { name: 'Новый диалог' }).click()
3. const resetSession = await sessionId(first) → ui-c9a4a9e7-4259-427b-8af5-f867913960c5
4. await expectVisibleSession(first, resetSession) → UI shows ui-c9a4a9e7-...
5. const second = await context.newPage()
6. await openAgent(second) → secondSession = ui-??? (new page, different sessionStorage)
7. expect(await sessionId(first)).toBe(resetSession) → PASS (first still has ui-c9a4a9e7-...)
8. await ask(first, 'Задачи Гаранина'):
   - browserSessionId = await sessionId(page) → ui-c9a4a9e7-... (read before click)
   - click button → send() reads requestSessionId → b0376e75-...
   - backend returns session_id → b0376e75-...
9. Error: expect(observed.payload.session_id).toBe(resetSession)
```

**Root Cause:**
```
The session ID changed between resetSession read and send() execution:
- resetSession (after New dialogue): ui-c9a4a9e7-4259-427b-8af5-f867913960c5
- backend payload.session_id: b0376e75-ab0f-4d87-9d04-6d025d7ea140

The only place that modifies sessionStorage is resetTabSessionId(), which is called only in newConversation().
But newConversation() is called only when clicking "Новый диалог" button.

The test clicks "Новый диалог" ONCE, and then calls ask(). So resetTabSessionId() should NOT be called again.

The issue is that send() reads getTabSessionId() at SEND-TIME (not at ask() time).
Between resetSession read and send() execution, sessionStorage was modified.

Looking at the code flow:
1. resetSession = await sessionId(first) → reads sessionStorage = ui-c9a4a9e7-...
2. await ask(first, 'Задачи Гаранина'):
   - browserSessionId = await sessionId(page) → reads sessionStorage
   - click button → send() is called
   - send() reads requestSessionId = getTabSessionId() → reads sessionStorage

Both sessionId() and getTabSessionId() read from sessionStorage.
They should read the same value unless sessionStorage changed between reads.

The only way sessionStorage can change is if resetTabSessionId() is called.
But resetTabSessionId() is called only in newConversation().
And newConversation() is called only when clicking "Новый диалог".

The test clicks "Новый диалог" ONCE before calling ask().
So resetTabSessionId() should NOT be called during ask().

The mystery remains: what changed sessionStorage between resetSession and send()?

WAIT! There's another newConversation() in AssistantView.tsx!

Let me check AssistantView.tsx...
```

### AssistantView.tsx Discovery

```typescript
// po-agent-platform-v2/frontend/src/views/AssistantView.tsx

function initialSessionId() {
  const key = 'po-agent-v3-session-id'  // ← DIFFERENT KEY!
  const existing = window.sessionStorage.getItem(key)
  if (existing) return existing
  const created = createSessionId()
  window.sessionStorage.setItem(key, created)
  return created
}

const newConversation = () => {
  const next = createSessionId()
  window.sessionStorage.setItem('po-agent-v3-session-id', next)  // ← DIFFERENT KEY!
  setCurrentSession(next)
  setMessages([initialMessage])
  setQuery('')
}
```

**Key Finding:** `AssistantView.tsx` uses `'po-agent-v3-session-id'` as the sessionStorage key, which is DIFFERENT from `WorkspaceApp.tsx` which uses `'po-agent-runtime-session-id'`.

**But this should NOT affect the test!** The test reads from `po-agent-runtime-session-id` (WorkspaceApp.tsx key).

### WorkspaceApp.tsx Analysis

```typescript
// po-agent-platform-v2/frontend/src/recovery/WorkspaceApp.tsx

const SESSION_KEY = 'po-agent-runtime-session-id'

function getTabSessionId(): string {
  const current = window.sessionStorage.getItem(SESSION_KEY)
  if (current) return current
  const created = createSessionId()
  window.sessionStorage.setItem(SESSION_KEY, created)
  return created
}

function resetTabSessionId(): string {
  const created = createSessionId()
  window.sessionStorage.setItem(SESSION_KEY, created)
  return created
}

function newConversation() {
  const fresh = resetTabSessionId()
  setSessionId(fresh)
  setInput('')
  setMessages([{
    id: `hello-${fresh}`,
    role: 'agent',
    text: 'Новый диалог создан. Предыдущий transient dialogue state не используется.'
  }])
}
```

**Code Analysis:**
1. `getTabSessionId()` reads from sessionStorage, creates if missing
2. `resetTabSessionId()` creates new session ID and saves to sessionStorage
3. `newConversation()` calls `resetTabSessionId()` and updates React state
4. `send()` calls `getTabSessionId()` to read session ID

**The Mystery:** Between `resetSession` read and `send()` execution, sessionStorage must have changed. But the only place that changes sessionStorage is `resetTabSessionId()`, which is called only in `newConversation()`, which is called only when clicking "Новый диалог".

**The Test clicks "Новый диалог" ONCE before calling `ask()`. So `resetTabSessionId()` should NOT be called during `ask()`.**

### Hypothesis: React State Sync Issue

Looking at the code more carefully:

```typescript
const [sessionId, setSessionId] = useState(getTabSessionId)
```

This initializes `sessionId` with `getTabSessionId()` - which reads from sessionStorage.

When `newConversation()` is called:
```typescript
function newConversation() {
  const fresh = resetTabSessionId()  // Creates new session ID, saves to sessionStorage
  setSessionId(fresh)  // Updates React state
  ...
}
```

But React state update is asynchronous! The `sessionId` React state might NOT be updated immediately after `setSessionId(fresh)`.

Then when `send()` is called:
```typescript
const requestSessionId = getTabSessionId()  // Reads from sessionStorage = fresh (correct)
if (requestSessionId !== sessionId) setSessionId(requestSessionId)  // Updates React state if mismatch
```

If `sessionId` React state is still the old value, then `requestSessionId !== sessionId` is true, and `setSessionId(requestSessionId)` updates React state.

But this should NOT affect sessionStorage! `setSessionId()` only updates React state, not sessionStorage.

### Final Hypothesis: Timing Issue

The most likely scenario:
1. `resetTabSessionId()` creates session ID `ui-c9a4a9e7-...` and saves to sessionStorage
2. `setSessionId(fresh)` schedules React state update (asynchronous)
3. Test reads `resetSession = await sessionId(first)` → reads sessionStorage = `ui-c9a4a9e7-...`
4. `ask()` reads `browserSessionId = await sessionId(page)` → reads sessionStorage = `ui-c9a4a9e7-...`
5. Test clicks button → `send()` is called
6. `send()` reads `requestSessionId = getTabSessionId()` → **reads sessionStorage**
7. **BUT! Between step 4 and step 6, something changed sessionStorage!**

**What could change sessionStorage between steps 4 and 6?**

The only possibility is that `getTabSessionId()` creates a NEW session ID because sessionStorage is empty!

But we just read `ui-c9a4a9e7-...` from sessionStorage in step 4!

**This is a PARADOX!**

**The only explanation is that `sessionId()` and `getTabSessionId()` are reading from DIFFERENT sessionStorage keys!**

But we verified that both use `po-agent-runtime-session-id`!

**UNLESS... there's a different `SESSION_KEY` defined somewhere else!**

Let me check...

<tool_call>
<function=run_shell_command>