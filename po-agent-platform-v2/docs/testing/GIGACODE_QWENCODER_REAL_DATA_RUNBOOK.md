# GigaCode CLI / QwenCoder: deployment and real-data validation runbook

## Purpose

This runbook is the required procedure for deploying, exercising and diagnosing PO Agent Platform v2 from GigaCode CLI with QwenCoder against real SberWorks Task Tracker (SWTR/AS21) and the real LLM endpoint.

The goal is not merely to make tests green. The goal is to distinguish environment/integration problems from product defects and to preserve enough diagnostics for an independent review without leaking credentials.

## Non-negotiable rules

1. The production path is the Harness implementation under `src/po_agent/harness`, exposed through the current API/runtime factory. Do not revive the legacy regex orchestrator to make a test pass.
2. LLM output is interpretation, not source truth. Person, sprint, release, status and task identifiers must be grounded against source-backed data before use.
3. Do not change production code until the failure has been classified. Allowed top-level classes: `ENV`, `AUTH`, `NETWORK`, `SOURCE`, `DATA`, `CODE`, `UNKNOWN`.
4. A stack trace does not automatically mean `CODE`. Authentication, source schema, environment and network causes must be ruled out first.
5. Never paste tokens, cookies, JWTs, API keys or raw internal payloads into Git, a PR, an issue, chat or Markdown report.
6. Every command that participates in the pilot must be executed through `tools/diagnostic_runner.py`, so the run is reproducible and its diagnostics persist.

## 1. Checkout and bootstrap

From the repository root:

```bash
git fetch --all --prune
git checkout chatgpt-harness-recovery
git pull --ff-only
cd po-agent-platform-v2
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
cd frontend && npm ci && cd ..
```

Do not store credentials in repository files. SWTR and LLM credentials must come only from the approved local credential store/environment used by the workstation.

## 2. Logging contract

Run every validation command like this from `po-agent-platform-v2`:

```bash
python tools/diagnostic_runner.py --name <short-name> -- <command> <args...>
```

Example:

```bash
python tools/diagnostic_runner.py --name hermetic -- pytest -q tests/test_harness_recovery_runtime.py
```

For every invocation the runner creates:

```text
<repo>/.artifacts/diagnostics/<UTC timestamp>-<name>/
├── raw.log          # local only; may contain source data/secrets
├── sanitized.log    # redacted copy intended for review
└── summary.json     # machine-readable result and initial classification
```

`LATEST` points to the most recent run. `.artifacts/` must remain gitignored.

Before sharing a failed run, QwenCoder must inspect `sanitized.log` and `summary.json`, verify that no secret remains visible, and provide those two files only. Raw logs are never shared unless explicitly requested and manually scrubbed.

## 3. Mandatory test sequence

### Stage A — repository and hermetic baseline

Run first. If this fails, do not touch real services.

```bash
python tools/diagnostic_runner.py --name hygiene -- pytest -q tests/test_repository_hygiene.py
python tools/diagnostic_runner.py --name harness-regression -- pytest -q \
  --ignore=tests/test_integration_real_services.py \
  --ignore=tests/test_llm_real_integration.py \
  --ignore=tests/test_agent_full_integration.py \
  --ignore=tests/test_orchestrator_skill_integration.py \
  --ignore=tests/test_frontend_config.py
```

Then build the frontend:

```bash
python tools/diagnostic_runner.py --name frontend-build -- bash -lc 'cd frontend && npm run build'
```

Expected result: all three passes before moving to Stage B.

### Stage B — local source/credential preflight

Confirm locally, without printing credentials:

- SWTR credential is present in the approved local location/environment.
- LLM/QwenCoder credential/configuration is present.
- required internal hosts resolve and are reachable from the workstation/VPN;
- no repository config contains a token or cookie;
- the expected API/adapter configuration points to the current Harness-compatible source path.

If an endpoint returns 401/403, classify `AUTH`; timeout/DNS/TLS/proxy failures classify `NETWORK`; missing executable/module/config classify `ENV`. Do not modify application logic for these classes.

### Stage C — source readiness and contracts

```bash
python tools/diagnostic_runner.py --name source-readiness -- pytest -q \
  tests/test_harness_source_readiness.py \
  tests/test_harness_source_contracts.py \
  tests/test_task_api_as21_adapter.py
```

A schema/endpoint mismatch is normally `SOURCE` until proven otherwise. Missing/empty business data is normally `DATA` until proven otherwise.

### Stage D — LLM semantic boundary

First run the hermetic semantic tests:

```bash
python tools/diagnostic_runner.py --name semantic-boundary -- pytest -q \
  tests/test_harness_llm_semantic_interpreter.py \
  tests/test_harness_entity_grounding.py \
  tests/test_harness_dialogue_runtime.py
```

Then run the approved real-LLM smoke test available in the workstation environment. A good smoke test must prove both of these independently:

- QwenCoder returns valid structured semantic output;
- a plausible but nonexistent login/sprint/release/status proposed by the LLM is rejected or clarified unless confirmed by the source.

Do not accept a successful free-text completion as evidence that the semantic Harness works.

### Stage E — real SWTR / end-to-end pilot

Use the real-data scenarios from `REAL_DATA_COMPREHENSIVE_TEST_CHECKLIST.md` and `docs/testing/COMPREHENSIVE_AGENT_TEST_PLAN.md`. Exercise at minimum:

- task lookup by exact task key;
- natural-language task search;
- person resolution including Russian inflection/shorthand;
- sprint and release shorthand resolution;
- status/business-term clarification;
- task summary and quality analysis;
- sprint/team/release intelligence;
- history and time-in-status where source history exists;
- one ambiguous entity case;
- one nonexistent entity case;
- one intentionally malformed/underspecified user query;
- repeated query/session-context behavior.

Each scenario is a separate diagnostic run or a clearly named test group. Do not merge unrelated failures into one opaque log.

## 4. Failure triage protocol for QwenCoder

For every failed run QwenCoder must create a short diagnosis in this exact shape:

```text
RUN_ID: <id>
RESULT: FAIL
PRIMARY_CLASS: ENV|AUTH|NETWORK|SOURCE|DATA|CODE|UNKNOWN
SECONDARY_CLASSES: [...]
FIRST_FAILED_OPERATION: <operation/test>
EVIDENCE: <2-5 concrete observations from sanitized.log>
PRODUCTION_CODE_CHANGE_NEEDED: yes|no|not-proven
NEXT_SAFE_CHECK: <one specific check>
```

Decision rules:

- `ENV`, `AUTH`, `NETWORK`: fix the environment/configuration outside product logic; rerun the same test unchanged.
- `SOURCE`: verify current endpoint/schema/contract against the actual source before changing adapter code.
- `DATA`: verify the source entity/data really exists and that the scenario expectation is valid.
- `CODE`: only after the preceding classes are ruled out may QwenCoder propose a minimal product-code fix plus a regression test.
- `UNKNOWN`: collect one more targeted diagnostic; do not guess.

## 5. Fix loop

When and only when a defect is proven as `CODE`:

1. Reproduce it with the smallest possible failing test.
2. Add or tighten a regression test before/with the fix.
3. Apply the smallest change compatible with the Master Spec.
4. Rerun the failing diagnostic command.
5. Rerun Stage A in full.
6. Rerun the affected real-data scenario.
7. Record before/after `run_id` values in the handoff summary.

Never weaken a test, bypass grounding, hard-code a real person/sprint/status, add Russian declension tables for individual names, or route around the Harness merely to make a case pass.

## 6. Handoff for ChatGPT review

After a failed or completed pilot, provide ChatGPT with either:

- the `summary.json` + `sanitized.log` files for the relevant run(s), uploaded directly to the conversation; or
- the same sanitized content copied into a review artifact that contains no source payloads or secrets.

ChatGPT should be asked to analyze the evidence and determine whether the classification is justified before QwenCoder changes production code. The recommended prompt is:

```text
Analyze these PO Agent real-data diagnostics. Treat QwenCoder's failure classification as a hypothesis, not truth. Determine the primary root-cause class (ENV/AUTH/NETWORK/SOURCE/DATA/CODE/UNKNOWN), cite concrete evidence from the supplied sanitized logs, state what is not yet proven, and give the smallest next diagnostic step. Do not recommend production-code changes unless CODE is demonstrated.
```

If several runs fail, upload them together and include the run order. This allows comparison of the first failure, cascading failures and changes after a fix.

## 7. Pilot acceptance gate

The real-data pilot is accepted only when all of the following hold:

- Stage A is green;
- frontend build is green;
- source readiness is green in the target workstation environment;
- real QwenCoder semantic interpretation works through the Harness boundary;
- source grounding rejects invented identifiers;
- core real-data scenarios pass with evidence;
- no open failure remains classified `CODE` or `UNKNOWN`;
- no secret-bearing or generated diagnostic artifact is committed;
- final sanitized diagnostics are sufficient for independent review.

A failure caused solely by unavailable infrastructure may block production acceptance, but it must not be disguised as a product defect or 'fixed' by weakening the architecture.
