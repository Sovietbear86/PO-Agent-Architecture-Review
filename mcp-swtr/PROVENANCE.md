# MCP-SWTR — Provenance & Redaction Record

## Source

| Field | Value |
|-------|-------|
| Origin remote | `https://INTERNAL_GIT/MCP-SWTR.git` (GitVerse, redacted) |
| Branch | `master` |
| Source commit | `ea7f75f2b2f21fab0d3a262b2494a48309892cab` |
| Source date | 2026-08-25 |
| Import date | 2026-10-23 |
| Import method | `git archive` of tracked files at exact HEAD (no history, no .git, no .env) |

## Redaction applied (data/docs/metadata only — NOT functional code)

Six files were modified to remove PII and internal infrastructure identifiers. All MCP-SWTR functional code (`mcp_server.py`, `models/*`, `npx-version/src/*`) is byte-identical to source.

| File | Redactions |
|------|-----------|
| `api-docs.json` | 7 (corp emails → `redacted@sbertech.ru`, internal hosts → `AS21_INTERNAL_URL_PLACEHOLDER`, private IP → `10.0.0.1`) |
| `README.md` | 1 (internal host → `AS21_INTERNAL_URL_PLACEHOLDER`) |
| `npx-version/README.md` | 11 (internal hosts) |
| `npx-version/LOCAL_SETUP.md` | 7 (internal hosts) |
| `pyproject.toml` | 1 (author email → `redacted@sbertech.ru`) |
| `npx-version/package.json` | 2 (author emails → `redacted@sbertech.ru`) |

## Files byte-identical to source HEAD (38 files)

All files except the 6 redacted above are bit-for-bit identical to the GitVerse source at `ea7f75f`.

## No credentials, tokens, .env, .git, or private keys in this import.
