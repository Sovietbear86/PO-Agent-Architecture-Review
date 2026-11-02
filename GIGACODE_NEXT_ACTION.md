# GigaCode — CURRENT NEXT ACTION

## A230R3.25-P31-D2-R9-EXPLICIT-FORECAST-POLICY-QA

**Independent QA ONLY**. Do not edit any code, tests, docs, configuration, frozen Core V4 or AS21. No commits/pushes/merges or destructive cleanup, broad source scans or mutations. Preserve all running Review/Public services and user dirty files. Fetch origin, report LOCAL=REMOTE=TESTED_HEAD.

### Baseline
A230R3.24 `D2_R8_GREEN + LIVE_ADAPTER_BLOCKED(terminal-set)`, tested HEAD `5f2ded2`. Independent source-status binding 60/60 focused, 36/36 adversarial, source A/B 5/5 DMS-SPRNT-5, Agent V4 299, Task API 164 passed/25 known baseline failures, frontend build 0, frozen Core V4 6/6. AS21 gives source-declared statusType values lowercase `done`, `in_progress`, `pause`, but TQL/metadata do NOT enumerate authoritative terminal categories. Consequently owner must supply *approved terminal-type product policy*, not infer from observed `done` samples.

### Owner patch not yet QA certified
- `0324c87` NEW pure `task-api/app/services/sprint_forecast_policy.py`, a `SprintForecastPolicy` with *explicit* authority string, timezone name, approved_at tz-aware, canonical working weekdays and exact terminal frozenset. `validate_forecast_policy` fails closed if missing/invalid policy; it does not set defaults, infer from display names or call AS21.
- `891b127` NEW `task-api/tests/test_sprint_forecast_policy.py` offline policy contract tests including missing approval/authority, invalid timezone/workdays, absent/invalid terminal type.
- **IMPORTANT: No actual PO approval has been granted for specific statuses, calendar, or time zone in production by these test fixtures.** The sample `frozenset({"done"})` and Europe/Moscow appear ONLY in synthetic tests, NOT deployed settings. Do not claim live forecast. The pure validator is not yet connected to route, projector, plugin or UI. No Core changes.

### Gate 0 — audit
Verify delta from `5f2ded2` exactly new policy module, test module, this QA spec. All six frozen Core V4 files byte-identical to checkpoint `6fb335d`; preserve worktree. Scan source for unauthorized defaults/credentials/PII or hardcoded sprint keys. Confirm policy is not auto-enabled.
### Gate 1 — contract tests + adversarial
Run `pytest -q task-api/tests/test_sprint_forecast_policy.py` (expected 11 pytest cases; calculate actual collected count). Independently test malformed policy object, dates, timezone values and missing tzdb, duplicate weekdays, bool weekdays, non-frozenset terminal list, blanks/spaces, policy authority missing, unapproved policy and local/AS21 source unavailable. Distinguish a valid syntax contract from actual business-approved policy provenance. Any TypeError/AttributeError on malformed caller input = RED fail-closed defect. In particular invalid *unhashable* weekday items might trigger TypeError from `set(weekdays)`; check robust validation.
### Gate 2 — regressions and design contract
Run existing source/projection 16+ tests, collector 6, route 6, calculator 11, V4 full (~299), Task API source-backed and broad (25 existing baseline failures), frontend build. Check Core V4 6/6 and Public unaffected.
Confirm smallest owner integration after GREEN: (1) explicit authorized product policy source and as_of status snapshot, (2) internally bind current statusType and terminal set to `bind_source_status_types`, (3) map verified closures to `SprintForecastInput` using product timezone + weekdays, (4) bounded safe GET projection and V4 Plugin, then UI tile replacement. Historical committed Predictability remains N/A absent baseline. Real AS21 values must be read, no invented numeric forecasts.
### Verdict
`D2_R9_GREEN` if independent tests pass and fail-closed policy mechanism sound, else RED first boundary. **Live integration remains blocked on product approval/configuration and future wiring even if green.** QA only, report and STOP.

### Short command
Execute A230R3.25-P31-D2-R9-EXPLICIT-FORECAST-POLICY-QA from Review GIGACODE_NEXT_ACTION.md. Independent QA: validate explicit terminal status / TZ / weekday policy guards, adversarial, full regression, Core 6/6. No changes or commits; report and STOP.
