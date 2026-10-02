# Community Distribution Acceptance

Run this gate before copying the staging snapshot into a new repository.

## A. Sanitization

- [ ] `python scripts/prepublish_scan.py` returns GREEN.
- [ ] No real `.env` files.
- [ ] No SWTR/LLM tokens, cookies, private keys or certificates.
- [ ] No `knowledge/employees` directory.
- [ ] No QA reports, screenshots or REAL AS21 payload dumps.
- [ ] No real employee roster/e-mails.
- [ ] No development-repository product defaults or team-member names.
- [ ] No workstation-specific absolute paths.

## B. Configurability

Replace the templates with a throwaway configuration:

```yaml
# task-api/config/products.yaml
products:
  PAY:
    display_name: Payments
  CRM:
    display_name: CRM
```

and synthetic members in `team_members.yaml`.

Require:

- [ ] Agent health advertises V4 successfully.
- [ ] PAY/CRM are accepted as product spaces after restart.
- [ ] a space absent from products.yaml fails clarification/grounding rather than being silently accepted.
- [ ] Team page can select configured products.
- [ ] Quality aging product selector uses configured frontend labels.
- [ ] team/competency Skills read the configured synthetic roster.

## C. Runtime

- [ ] Task API exposes only the intended read-only SWTR routers.
- [ ] MCP stdio mode starts with environment-only credentials.
- [ ] MCP SSE mode connects when configured.
- [ ] Agent starts with OpenAI-compatible LLM endpoint/model/API key.
- [ ] `GET /api/v1/health` is ready.
- [ ] direct Agent query succeeds against a configured product.
- [ ] source outage returns typed unavailable/error, never factual zero.

## D. Frontend

```bash
cd po-agent-platform-v2/frontend
npm ci
npm run build
```

Require:

- [ ] build GREEN;
- [ ] configurable brand/context/product chips visible;
- [ ] no development-product branding/defaults;
- [ ] Tasks page submits raw text to Agent API;
- [ ] six workspaces render without old product assumptions.

## E. Fresh repository history

The final repository must be created from an exported working tree **without the original .git directory**.

- [ ] new empty GitHub repository exists;
- [ ] first commit is `Initial community distribution`;
- [ ] no commit ancestry from `PO-Agent-Architecture-Review`;
- [ ] repository visibility/access is explicitly chosen by the owner;
- [ ] organization secret scanning / dependency scanning is enabled where available.
