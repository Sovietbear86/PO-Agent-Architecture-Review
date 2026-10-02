# Security and sanitization

## Distribution rules

This community tree is prepared as a clean snapshot. The final shared repository must be created as a **new repository with new Git history**.

Do not publish the staging branch history from the original development repository.

## Never commit

- SWTR/API tokens;
- LLM API keys;
- cookies/session IDs;
- private certificates;
- real employee e-mails unless explicitly approved;
- workstation-specific absolute paths;
- REAL AS21 response dumps;
- QA screenshots/reports containing personal or project data.

## Read-only contract

The community `task-api/main.py` exposes only SWTR read-facade routers. Any future write capability must be separately designed, explicitly approved and gated.

## Pre-publish

Run:

```bash
python scripts/prepublish_scan.py
```

Then inspect:

```bash
git diff --cached
git ls-files
```

A secret scanner such as your organization's approved scanner should also run before publication.
