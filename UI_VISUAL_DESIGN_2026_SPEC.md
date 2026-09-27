# PO Agent V4 — UI Visual Design 2026

## Status

Owner implementation active after `A224R2 GREEN`.

This document governs the visual redesign only. It MUST NOT change Agent Core,
planner/runtime behavior, capability contracts, source semantics, result-state
classification, or the already certified browser workflows.

## Source visual language

The design cookbook is the 27-page presentation `2026-Счетчиков`.

The product UI should reuse its visual language, not literal slide copy:

- deep navy / near-black canvas;
- cyan / blue luminous accents;
- translucent dark glass cards;
- thin cyan dividers;
- high-contrast white typography;
- soft glow, never neon overload;
- sparse crystalline / lens-like 3D decoration;
- readable structured cards placed over decorative backgrounds;
- different background composition per product page while keeping one shared token system.

Do NOT paste slide text, slide logos or screenshots behind operational UI.

## Page-to-slide visual mapping

| Page | Primary cookbook reference | Secondary reference | Background motif |
|---|---|---|---|
| Overview | slide 13, "Пилот AI-ассистента" | slide 1 | lens / circular crystal forms at edges, central dark working area |
| Tasks | slides 21–22, DB Triage Assistant | slide 18 | framed application/workspace composition + glass fins |
| Sprints | slide 4, Frontend 2026 | slide 17 | timeline / milestones + right-side crystalline object |
| Releases | slide 23, Risks and constraints | slide 26 | structured table/grid field + top-right fins |
| Team | slide 18, Result for operator | slide 15 | structured cards + right-side crystalline object |
| Quality | slide 17, Safe assistant model | slide 25 | timeline points + top-right fins / KPI language |

## Central theme tokens

Implemented in `workspace.css`:

- canvas: `#03111f / #020a13`
- cyan accent: `#22d8f5`
- blue accent: `#168fd0`
- primary text: `#f4fbff`
- muted text: `#9eb5c8`
- good: `#42e8bc`
- warning: `#ffb56b`
- error: `#ff8291`
- cards: dark translucent glass with cyan border
- shadow/glow must remain subtle enough for dense data screens

## Background assets

Generated slide-derived presentation assets:

- `/design/overview-bg.svg`
- `/design/tasks-bg.svg`
- `/design/sprint-bg.svg`
- `/design/releases-bg.svg`
- `/design/team-bg.svg`
- `/design/quality-bg.svg`

These are abstract derivatives, not copies of the slide text or branding.

## Required component behavior

### Navigation

- Stable WORKS / PO Space / DB Tribe chrome.
- Dark fixed sidebar, dark translucent sticky topbar.
- Active nav = cyan accent and left-edge highlight.
- Do not use different navigation styling per page.

### Cards

- All metric and content cards use shared glass treatment.
- Do not sacrifice text contrast for transparency.
- Dense tables and collections may use stronger dark opacity than decorative areas.
- Existing internal scrolling remains intact.

### Source and state semantics

Visual redesign MUST preserve:

- NOT_RUN
- LOADING
- SUCCESS_WITH_DATA
- REAL_EMPTY
- NEEDS_CLARIFICATION
- SOURCE_CONDITIONAL
- SOURCE_UNAVAILABLE
- NOT_FOUND
- ERROR

A warning/source-limited state must remain more prominent than background decoration.

### Responsive

Desktop target: 1440 px.
Narrow acceptance viewport: 480 px.

Known A224R2 finding to fix:
- long PO Attention titles + score badge caused ~14–75 px horizontal overflow at 480 px.

Required:
- no document-level horizontal overflow;
- long titles wrap;
- score/risk badge remains readable and does not force row width;
- internal vertical scrolling continues to reach the final queue row.

## Page expectations

### Overview

- Background: lens/circular motif from slide 13 family.
- Attention + Daily Brief keep equal/comparable visible height.
- "Задачи по пространствам" cards remain readable above background.

### Tasks

- Background derived from DB Triage Assistant frame composition.
- Search/status filters should read as one coherent control surface.
- Local tasks may be visually distinguished with a subtle secondary cyan treatment, not a different product theme.

### Sprints

- Timeline motif should support sprint semantics without becoming a literal chart.
- Metric row and risk queue remain dominant content.

### Releases

- Structured table/grid motif reflects source-limited status.
- SOURCE_UNAVAILABLE/CONDITIONAL panels must be especially legible.
- Do not visually imply data completeness when source linkage is absent.

### Team

- Structured-card motif.
- Capacity source limitation should look intentional, not broken.
- Workload/WIP/Bottleneck lists remain data-first.

### Quality

- Timeline/KPI motif.
- READY/REWORK and source-state semantics dominate decoration.
- Aging queue must retain scroll/readability for long lists.

## Non-goals

- No backend/API changes.
- No skill changes.
- No new data computation.
- No new external dependencies.
- No font embedding.
- No replacement of V4 state adapter.
- No redesign that hides Evidence / Trace / Skill lineage.

## Acceptance gate

GigaCode must validate:

1. frontend build/TS clean;
2. all six page backgrounds are distinct and mapped correctly;
3. shared theme tokens are used consistently;
4. 1440 px and 480 px Browser C screenshots for every page;
5. no horizontal overflow;
6. source-state semantics unchanged;
7. functional smoke retained from A224R2;
8. drawers/chat remain usable;
9. 0 AS21 mutations and no extra source reads caused by presentation changes.

