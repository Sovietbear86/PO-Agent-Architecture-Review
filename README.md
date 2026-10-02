# PO Agent Harness — Community Distribution

Reusable, read-only product-owner agent built around **Agent Core V4**, plugin Skills/Capabilities, a read-only Task API facade and REAL AS21/SWTR as the factual source.

This distribution is intentionally separated from the product-development repository:

- no QA reports/artifacts or historical assignment logs;
- no employee knowledge files;
- no real team roster;
- no tokens, API keys or workstation paths;
- no development-team product configuration;
- no Git history from the development repository in the final community repo.

## Configure your deployment

The two deployment-owned configuration files are:

- `task-api/config/products.yaml` — product/space codes visible to the agent;
- `task-api/config/team_members.yaml` — team members, roles and competencies.

Credentials and endpoints live only in environment variables / local `.env` files. See [DEPLOYMENT.md](DEPLOYMENT.md).

Architecture and extension rules: [ARCHITECTURE.md](ARCHITECTURE.md).

## Runtime

```text
Browser / PO Workspace
        |
        v
PO Agent (Agent Core V4)
        |
        v
Plugin Skill / Capability Registry
        |
        v
Read-only Task API
        |
        v
MCP-SWTR
        |
        v
REAL AS21
```

The LLM plans; it does not become the factual source. Business facts must be backed by AS21 evidence or the agent fails closed.

## Safety defaults

The community Task API exposes only read-only SWTR routes. Local browser tasks remain local browser data and are not written to AS21.

Before publishing your own fork/repository, run:

```bash
python scripts/prepublish_scan.py
```
