# Core-8 Team-Driven Sprint Discovery Contract

**Purpose:** define the authoritative team sources and the deterministic strategy for discovering real sprint data for Core-8 skills in AS21/SWTR.

## Authoritative team sources

Use these files as the primary team knowledge sources:

1. `task-api/knowledge/team/team.md`
   - canonical human-readable team roster;
   - real AS21 login for each team member;
   - role / product team / professional profile.

2. `task-api/knowledge/team/competencies.md`
   - evidence-based competency catalog;
   - real login mapping;
   - explicitly confirmed skills/directions;
   - competency levels are not invented when evidence is absent.

3. `task-api/knowledge/employees/*.md`
   - individual evidence files used when a skill requires deeper competency/achievement context.

### Important warning

`task-api/config/team_members.yaml` currently contains anonymized/stale placeholder identity values for a number of members (`example.com`, Ivanov/Petrov/etc.) even though some evidence-file paths point to real employee documents. It MUST NOT be treated as the source of truth for real AS21 identity during sprint discovery until reconciled against `knowledge/team/team.md`.

## Real team roster relevant to OLAP / DataMarts

The canonical roster currently contains, among others, these real AS21 logins:

### Platform V DataMarts / cross-product participants
- `Kalachanov.V.V` — PO, OLAP Analytics + DataMarts
- `Garanin.R.V` — product lead / technical lead
- `Agataeva.A.Z`
- `Alekseev.K.S`
- `Galtsov.A.A`
- `Dolgovskoy.E.N`
- `Zhdanov.A.Ni`
- `Kondratchikova.P.I`
- `Kryukov.V.A`
- `Makoshina.V.V`
- `Moiseev.A.N`
- `Semavin.M.M`

### Platform V OLAP Analytics
- `Goncharov.A.O`
- `Reshetnik.A`

Additional cross-product contributors may be included only when supported by the canonical team/evidence files.

## Sprint discovery spaces

For Core-8 sprint discovery, the primary real AS21 spaces are:

- `DMS` — DataMarts work;
- `OLP` — OLAP Analytics work.

Do not use WMB as the primary sprint-discovery space merely because earlier task-filter tests used WMB. WMB remains useful for task/attachment source-contract tests, but sprint-health/velocity acceptance should be based on the team's actual delivery spaces DMS and OLP.

## Deterministic discovery strategy

Sprint discovery MUST be team-driven rather than random-corpus-driven.

### Step 1 — build login set

Load the active real login list from `task-api/knowledge/team/team.md`. Use `competencies.md` only to enrich team/skill context, not to override login identity.

### Step 2 — query real work by member + space

For each relevant team member, query the real read-only SWTR/MCP source in BOTH `DMS` and `OLP` where appropriate.

Preferred source path already present in the repository:

`find_units_by_filter` with TQL similar to:

```text
space = "DMS" AND assigned_to = "<LOGIN>"
space = "OLP" AND assigned_to = "<LOGIN>"
```

This pattern existed in the historical/current synchronization code and is preferable to scanning arbitrary cached `/api/v1/tasks` rows.

### Step 3 — full task read

For each discovered real task, use read-only `read_unit` where necessary and inspect:

- `scrum_board_plugin_sprint`;
- derived sprint field/code/name;
- workflow status;
- created/updated/deadline;
- estimate / effort fields when present;
- project/space;
- assignee externalId/login.

### Step 4 — derive real sprint candidates

Collect unique non-empty sprint identifiers separately for:

- DMS;
- OLP.

For each candidate record:

- sprint code/id;
- sprint name if present;
- source task keys;
- member logins observed in that sprint;
- source attribute/value shape;
- source path that proved the relation.

### Step 5 — verify sprint-level read path

For a discovered sprint ID, test the existing read-only sprint capability (`get_sprint_tasks` / corresponding task-api read route) and cross-check the returned tasks against the task-level `scrum_board_plugin_sprint` evidence.

If `get_current_sprint(space)` continues to fail with invalid parameters, that does NOT by itself block sprint discovery. A real sprint discovered from team tasks can be used to validate `get_sprint_tasks` and the Core-8 sprint relation.

## Core-8 usage

The first real sprint corpus for `sprint_health` and `velocity` should preferentially include:

- at least one real DMS sprint containing current/recent work by actual DataMarts team members;
- at least one real OLP sprint containing current/recent work by actual OLAP team members;
- if one of the spaces has no real sprint data, record that fact explicitly rather than substituting another project silently.

`team_workload` must use the same canonical login roster, so sprint and workload tests refer to the same team identities.

`competency_match` must join task facts to `knowledge/team/competencies.md` / employee evidence, not to anonymized placeholders in `config/team_members.yaml`.

## Acceptance criteria

Sprint source discovery is considered sufficiently proven when:

1. at least one real team task in DMS or OLP has a non-empty sprint relation;
2. the sprint identifier/value shape is frozen from real source evidence;
3. a sprint-task read returns a deterministic set that can be cross-checked against task-level evidence;
4. assignee identities are matched through real AS21 login/externalId;
5. no task/sprint fact is inferred by LLM;
6. all calls are read-only;
7. absence of a current-sprint endpoint does not create a fabricated current sprint.

## QA handoff rule

Do not alter an in-progress attachment-only QA assignment. When the next sprint-focused QA assignment is authored, it MUST instruct GigaCode to read this file and use the team-driven DMS/OLP discovery strategy above.
