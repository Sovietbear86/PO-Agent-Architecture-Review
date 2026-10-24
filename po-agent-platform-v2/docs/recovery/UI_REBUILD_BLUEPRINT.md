# PO Workspace UI Rebuild Blueprint

## Decision

The Qwen UI is not the visual/runtime baseline. The new UI will reuse the proven interaction model and visual primitives from the legacy `task-api` S21 Task Agent while replacing its direct MCP coupling with the new typed Harness API.

## Source components to reuse/rebuild

Legacy reference (`task-api/src`):

- `components/AgentButton.tsx` — floating agent launcher behavior.
- `components/AgentChat.tsx` — persistent chat/drawer interaction model.
- `components/Drawer.tsx` — generic drawer mechanics.
- `components/CreateTaskDrawer.tsx` — button-triggered local task creation pattern.
- `components/TaskDetailsDrawer.tsx` — detail/evidence drawer pattern.
- `components/FilterBar.tsx` — dense S21-style filtering controls.
- `components/tasks/TaskCard.tsx` — task visual language.
- `components/tasks/TaskStatusBadge.tsx` — status rendering.
- `components/layout/Branding.tsx`, `Sidebar.tsx`, `TopBar.tsx`, `Layout.tsx` — application shell.
- `styles/global.css`, `theme.ts`, `statusColors.ts` — visual tokens and status semantics.

The current `po-agent-platform-v2/frontend` components may be reused only when they are cleaner than the legacy equivalent and comply with the contracts below.

## Product information architecture

The default route is **Обзор**, not a chat page.

Primary navigation target:

1. Обзор
2. Задачи
3. Спринты
4. Релизы
5. Команда
6. Качество
7. AI PDLC (hidden until runtime is stable)

The PO Agent is globally available from every route through a floating launcher and opens as a persistent right-side chat drawer. It is not a one-shot input embedded into the Overview page.

## Overview target

Overview is a PO dashboard fed by deterministic backend data. Initial mock-backed widgets:

- product selector;
- active sprint summary;
- release health summary;
- attention/risk queue;
- team workload snapshot;
- task quality snapshot;
- recent agent insights;
- data freshness / adapter state.

No widget may invent metrics client-side. The UI only renders typed backend data.

## Agent chat target

The new chat keeps the successful legacy interaction model but gets a clean state architecture.

Required behavior:

- persistent conversation during navigation;
- stable `session_id`;
- user / agent / system messages;
- loading state;
- clarification questions rendered inline with selectable options;
- structured task cards inside answers;
- structured metric cards/tables inside answers;
- evidence drawer/expander per answer;
- warnings and partial-result state;
- trace ID available in technical details;
- source freshness indicator;
- feedback controls on completed answers;
- Enter to send, Shift+Enter for newline;
- scroll-to-latest without destroying reading position unnecessarily;
- no direct calls to `/query`, `/tasks/summarize`, MCP or S21 from components.

## Stable frontend contract

All agent traffic goes through one API client.

```ts
export type QueryStatus =
  | 'COMPLETED'
  | 'NEEDS_CLARIFICATION'
  | 'PARTIAL'
  | 'FAILED'

export interface EvidenceItem {
  type: string
  source: string
  entityId?: string
  label: string
  value?: unknown
  freshness?: string
}

export interface QueryResponse {
  status: QueryStatus
  answer?: string
  question?: string
  options?: string[]
  clarificationId?: string
  intent?: string
  skill?: { id: string; version: string }
  data?: unknown
  evidence: EvidenceItem[]
  warnings: string[]
  traceId: string
  sessionId: string
}
```

The backend may use snake_case JSON; the API client owns normalization. React components never depend on backend naming quirks.

## Frontend layers

```text
App / Router
  -> WorkspaceProvider
     -> typed API client
     -> session/chat store
     -> adapter health store
  -> AppShell
     -> Sidebar
     -> TopBar
     -> route content
     -> AgentLauncher
        -> AgentChatDrawer
```

No page owns a second copy of agent conversation state.

## Component migration matrix

| Legacy S21 | Current Qwen | New target |
|---|---|---|
| AgentButton | components/agent/AgentButton | `agent/AgentLauncher` rebuilt from legacy behavior |
| AgentChat | AgentChat + AssistantView | one `agent/AgentChatDrawer`; AssistantView retired |
| Drawer | absent/generic layout | `ui/Drawer` reusable primitive |
| CreateTaskDrawer | CreateTaskForm always/page-coupled variants | `tasks/CreateTaskDrawer`, button-triggered |
| TaskDetailsDrawer | fragmented task views | `tasks/TaskDetailsDrawer` |
| TaskCard | TaskCard | rebuild using legacy density + typed v2 task |
| TaskStatusBadge | status color helpers | dedicated badge using workflow status semantics |
| Layout/Sidebar/TopBar | AppShell/MainLayout/Sidebar/TopBar | one coherent `workspace` shell |
| legacy global.css/theme | Tailwind + partial theme | consolidated design tokens, no duplicate styling systems |

## Visual principles

- S21/WORKS visual language: compact, functional, enterprise rather than marketing dashboard.
- Preserve the familiar green accent and neutral surfaces used by the earlier S21 UI.
- Dense task information is acceptable; large decorative cards are not.
- Typography and spacing must be consistent across all routes.
- Status colors come from one mapping.
- Tables/cards/drawers share the same radius, borders, shadows and spacing tokens.
- Responsive minimum: laptop-first, usable on tablet widths.

## Recovery implementation order

### UI-0 — inventory
Freeze current UI and classify every component: REUSE / REBUILD / RETIRE.

### UI-1 — design tokens
Consolidate theme/status tokens from legacy S21 and current frontend.

### UI-2 — shell
Rebuild Branding, Sidebar, TopBar, main content container and routing. Default route = Overview.

### UI-3 — global chat
Build WorkspaceProvider + AgentLauncher + persistent AgentChatDrawer. Use mock typed QueryResponse initially.

### UI-4 — structured chat results
Task cards, metric cards, evidence, clarification, warnings, trace details, feedback.

### UI-5 — Overview
Build dashboard against mock backend endpoint/fixtures. No client metric calculations.

### UI-6 — Tasks
Rebuild FilterBar, task list/cards, details drawer, create-local-task drawer.

### UI-7 — Sprint / Release / Team / Quality
One route at a time only after matching backend capability is executable.

### UI-8 — AI PDLC
Reintroduce only after feedback/eval/shadow/promotion runtime is verified.

## Acceptance gate for first UI slice

Without SWTR or a real LLM, using `FakeAS21Adapter` + mock LLM, a user must be able to:

1. open Overview;
2. navigate without page reload;
3. open the agent from the floating launcher;
4. ask for a fixture task;
5. receive a structured answer from the actual `/api/v1/query` harness endpoint;
6. see task evidence and trace metadata;
7. close/reopen chat without losing the session;
8. navigate to another page and retain chat history;
9. receive and answer a clarification request;
10. open task details in a drawer.

This is the first UI Definition of Done. Visual polishing comes after the functional gate.
