# Assignment 060 — Semantic Contract Repair Targeted Retest

## Role

QA/tester only. Do not modify production code, prompts, tests, fixtures, runners, wrappers, config, `.env`, AS21/SWTR data or acceptance expectations.

The owner/developer has already published the production semantic fix and contract tests. Your job is execution and evidence only.

## Required baseline

Branch:

`feat/core8-real-query-hardening-v2`

Before testing:

```bash
git fetch origin
git pull --ff-only origin feat/core8-real-query-hardening-v2
git status --short
git rev-parse HEAD
git merge-base --is-ancestor 9ba842e49ed5406e8f456893f2e533edf0a7f258 HEAD
git merge-base --is-ancestor 81fce0e218edbf08cdaf5d571a8b145ce407480d HEAD
```

Both ancestry checks must succeed and tracked working tree must be clean. Otherwise report BLOCKED and stop.

## Fix under test

Production commit:

`9ba842e49ed5406e8f456893f2e533edf0a7f258`

Contract-test commit:

`81fce0e218edbf08cdaf5d571a8b145ce407480d`

The fix adds:

- synthetic semantic extraction examples that are not QA026 values;
- machine-checkable raw-slot contract validation;
- a focused LLM contract-repair pass when slots contain foreign/full-query text or a derived login;
- fail-closed clarification if repair still violates the slot contract.

## Phase 1 — semantic unit/contract suite

Run the existing semantic-core test module on the current HEAD:

```bash
cd po-agent-platform-v2
python3 -m pytest tests/test_semantic_core_v2.py -q
```

If the environment requires the repository's documented venv/uv invocation, use it without changing dependencies or tracked files.

Record exact pass/fail count and tracebacks. Do not edit tests if anything fails.

## Phase 2 — independent source oracle anchors

Verify source independently of PO Agent semantic interpretation.

Required anchors:

- DMS-SPRNT-1 direct/bounded SWTR oracle readable;
- DMS-SPRNT-2 direct/bounded SWTR oracle readable;
- task keys extracted from actual SWTR structure;
- no fake adapter/source contributes to oracle evidence.

Do not classify a PO Agent clarification as SOURCE_ORACLE failure. The source oracle must use the direct independent SWTR path.

Record:

```text
ORACLE_SPRINT1 = PASS|FAIL|BLOCKED
ORACLE_SPRINT2 = PASS|FAIL|BLOCKED
SOURCE_ORACLE = PASS|FAIL|BLOCKED
```

## Phase 3 — rerun the same 19 PRODUCT_FAIL cases

Use the exact 19 cases from the last QA026 V3 root-cause analysis / V4 targeted report. Do not alter queries or expected filters.

For every case collect:

```text
CASE_ID
QUERY
EXPECTED_FILTERS
ACTUAL_INTENT
ACTUAL_SEMANTIC_FRAME
SELECTED_SKILL
ACTUAL_RESULT_KEYS (when applicable)
ORACLE_KEYS (when applicable)
MISSING_KEYS
EXTRA_KEYS
STATUS = PASS|PRODUCT_FAIL|BLOCKED|TIMEOUT
```

The semantic frame must demonstrate the contract itself, not merely a coincidentally correct final count.

Specific checks:

- human natural-language reference is present as `person_raw` when requested;
- a derived `member_login` must not replace `person_raw` unless the login itself was literally supplied by the user;
- `status_raw`, `product`, `sprint_raw`, `release_raw` must not contain a whole/foreign query;
- compound person/product/status/sprint constraints must not be silently dropped;
- structural sprint IDs remain exact after overlay.

## Phase 4 — regression sample

Rerun a representative sample of previously PASS cases, including:

- explicit task lookup;
- sprint-only search;
- Section G cases previously passing;
- fail-closed unknown sprint/source case.

Do not weaken acceptance criteria.

## Stop rule

Do NOT run the full 42-case QA026 in Assignment 060.

Do NOT repair any failure.

If a product failure is found, capture evidence and continue other independent targeted cases. The owner/developer will make any next fix.

## Required metrics

```text
START_HEAD = <sha>
CONTAINS_PRODUCTION_FIX_9BA842E = YES|NO
CONTAINS_CONTRACT_TESTS_81FCE0E = YES|NO
CLEAN_TREE_GUARD = PASS|FAIL
SEMANTIC_UNIT_TESTS = x/y PASS
PERSON_CLUSTER = x/12 PASS
STATUS_CLUSTER = x/4 PASS
PRODUCT_CLUSTER = x/3 PASS
TOTAL_RECOVERED = x/19
PRODUCT_FAIL_REMAINING = n
NEW_REGRESSIONS = n
SOURCE_ORACLE = PASS|FAIL|BLOCKED
SILENT_SLOT_DROP_COUNT = n
UNSAFE_FULL_QUERY_SLOT_COUNT = n
DERIVED_LOGIN_WITHOUT_PERSON_RAW_COUNT = n
READY_FOR_FULL_QA026 = YES|NO
060_VERDICT = GREEN|RED|BLOCKED
```

`READY_FOR_FULL_QA026 = YES` only when:

- semantic unit suite passes;
- all 19 targeted product failures pass;
- independent source oracle passes;
- no new regression is found;
- all three semantic-contract violation counters are zero.

## Report allowlist

Create, commit and push only:

`qa_reports/CORE8_SEMANTIC_CONTRACT_REPAIR_TARGETED_RETEST_060.md`

No JSON/helper scripts/test-runner changes may be committed.

## Autonomous execution

Routine QA actions are pre-authorized: fetch/pull, read-only inspection, service restart, test execution, direct read-only SWTR oracle calls, report creation, allowed report commit and push. Do not ask for confirmation after each such step.

Ask only for missing credentials, unavoidable platform approval, destructive action, write outside the report allowlist or scope expansion.

After push, return report commit SHA, concise verdict and full report text, then stop.