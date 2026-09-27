# GigaCode — Current Action

## ACTIVE: Assignment 225 — visual design system + slide-derived backgrounds

Role: QA/adversarial tester only. Do NOT modify production/frontend/backend code.

## Frozen functional baseline

A224R2 is GREEN:
- checkpoint: `checkpoint/v4-ui-usability-green-a224r2@612116894572f72af4f024486799458d3870d539`
- state/lineage/usability semantics are frozen
- visual work must not reopen backend functionality

## Design contract

Read:
`UI_VISUAL_DESIGN_2026_SPEC.md`

The source visual language is the 2026 design cookbook. The implementation uses abstract slide-derived assets, not literal slide screenshots/text/logos.

Expected page mapping:
- Overview -> slide-13 family: lens / circular crystal composition
- Tasks -> slides-21/22 family: framed application composition + glass fins
- Sprints -> slide-4/17 family: timeline + crystalline object
- Releases -> slide-23/26 family: structured table/grid + fins
- Team -> slide-18/15 family: structured cards + crystalline object
- Quality -> slide-17/25 family: timeline/KPI composition + fins

## Owner implementation under test

Visual-only changes include:
- `frontend/public/design/overview-bg.svg`
- `frontend/public/design/tasks-bg.svg`
- `frontend/public/design/sprint-bg.svg`
- `frontend/public/design/releases-bg.svg`
- `frontend/public/design/team-bg.svg`
- `frontend/public/design/quality-bg.svg`
- route-specific `page-*` classes
- shared dark navy/cyan glass theme in `workspace.css`
- ResultStatePanel dark-glass adaptation
- responsive Attention row wrapping fix
- `UI_VISUAL_DESIGN_2026_SPEC.md`

No backend/Core/planner/runtime/source contract changes are expected.

## P0 — diff / build / architecture

1. Pull current branch; record START_HEAD and clean worktree.
2. Diff from A224R2 checkpoint.
3. Prove all production changes after A224R2 are frontend/static-assets/docs only.
4. Prove:
   - 0 Agent Core/planner/runtime/plugin/source changes;
   - 0 new npm dependencies;
   - 0 AS21 mutation path;
   - no V4 state adapter semantics changed.
5. Run:
   - `tsc --noEmit`
   - `vite build`
   - existing frontend/e2e smoke
6. Require zero build/type/runtime errors.

Any backend semantic delta => RED STOP.

## P1 — asset and page mapping

For all six pages, Browser C must prove that the distinct background asset loads successfully:

1. Overview -> `/design/overview-bg.svg`
2. Tasks -> `/design/tasks-bg.svg`
3. Sprints -> `/design/sprint-bg.svg`
4. Releases -> `/design/releases-bg.svg`
5. Team -> `/design/team-bg.svg`
6. Quality -> `/design/quality-bg.svg`

Require:
- no 404s;
- each page uses a different background;
- background is decorative only and does not contain operational copy;
- route navigation does not retain the previous page background.

Capture one 1440px screenshot per page.

## P2 — shared visual language

Across all six pages require:
- dark navy / near-black canvas;
- cyan/blue accents;
- translucent dark glass cards;
- thin cyan borders/dividers;
- high-contrast white primary text;
- consistent muted secondary text;
- stable WORKS / PO Space / DB Tribe chrome;
- stable sidebar/topbar styling across pages;
- active nav clearly visible;
- visual hierarchy remains data-first.

Reject:
- white legacy card surfaces dominating the page;
- unreadable low-contrast text;
- excessive glow that competes with data;
- six unrelated page styles.

## P3 — readability / state semantics

Re-run representative typed states:
- SUCCESS_WITH_DATA
- REAL_EMPTY
- NEEDS_CLARIFICATION
- SOURCE_CONDITIONAL or SOURCE_UNAVAILABLE
- ERROR if safely reproducible

Require:
- state remains semantically distinguishable after styling;
- source-unavailable/conditional text is more legible than background decoration;
- zero/empty semantics from A224R2 unchanged;
- no state hidden only by color; text labels remain present;
- Evidence / Trace / Skill lineage remains readable.

## P4 — functional retained smoke

Do not rerun full 54/54.

Retain A224R2 scenarios:
- Overview: team-scoped by-space exact cards + 107-row attention internal scroll
- Tasks: AS21/local status filters + local CRUD
- Sprints: source-correct metrics/risk queue + honest predictability limitation
- Releases: honest sparse SOURCE_CONDITIONAL/UNAVAILABLE behavior
- Team: space selector + workload/WIP/blocked; capacity source limitation
- Quality: WMB-102 quality semantics + scoped Aging queue
- Chat: rich markdown/table rendering + competency recommendation

Require identical business values/states to current source truth.

## P5 — responsive desktop + 480px

For EVERY page capture:
- 1440px screenshot
- 480px screenshot

Require:
- no document-level horizontal overflow;
- content remains reachable;
- metric cards reflow cleanly;
- toolbar/select/input controls remain usable;
- drawers fit viewport;
- internal vertical scroll areas remain usable.

Mandatory regression for A224R2 finding:
PO Attention at 480px:
- document scrollWidth == viewport width (or no meaningful >2px overflow);
- long task titles wrap;
- score badge does not force the row wider;
- can scroll vertically to final attention item.

If the previous ~14–75px overflow remains => RED.

## P6 — drawer / overlay styling

Test:
- PO Agent drawer
- Task details drawer
- Local task create drawer
- evidence panel
- clarification options
- feedback controls

Require:
- dark theme is coherent with main workspace;
- no white legacy drawer shell dominating;
- text/forms remain readable;
- overlay/scrim layering correct;
- open/close and session behavior unchanged.

## P7 — visual regression by page

### Overview
- Attention and Daily Brief remain comparable visible height.
- By-space cards readable over lens background.
- Decorative lens shapes do not obscure content.

### Tasks
- Search/filter surface reads as one coherent control area.
- Local tasks visually distinct but still same product system.
- Large result card grids readable.

### Sprints
- Timeline/crystal background does not look like actual metric data.
- risk queue and sprint metrics remain dominant.

### Releases
- source-limited panels look intentional, not broken.
- decorative table/grid does not imply fake release data.

### Team
- long workload/WIP/bottleneck lists remain readable.
- Capacity source-unavailable state looks intentional.

### Quality
- READY/REWORK and Quality/Aging information dominate the background.
- warning/acceptance states retain visual priority.

## P8 — performance / asset hygiene

Browser/network audit:
- six SVG backgrounds load locally from Vite/static assets;
- no external image/font/network dependency added;
- no huge raster background payload;
- route switch does not repeatedly leak requests or accumulate overlays;
- no console errors caused by SVG/CSS.

## P9 — source/write audit

Require:
- 0 AS21 mutations;
- 0 new source reads attributable to visual styling;
- 0 local factual fallbacks;
- no change to A224R2 team-scoped task reads;
- localStorage still only used for LOCAL tasks.

## Verdict

Use exactly one:

- `AGENT_CORE_V4_UI_VISUAL_DESIGN_GREEN_A225`
- `AGENT_CORE_V4_UI_VISUAL_DESIGN_RED_A225`

If GREEN:
- recommend `checkpoint/v4-ui-visual-design-green-a225`;
- next owner phase = PO visual acceptance + final Browser UX re-gate;
- Learning Reviewer still does NOT start until owner/PO acceptance.

If RED:
- identify first failing visual/functional boundary;
- preserve screenshot at 1440 and/or 480 plus computed-style/network evidence;
- STOP.

Do not modify code.
