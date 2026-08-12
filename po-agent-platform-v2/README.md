# PO Agent Platform v2.1

Harness-based assistant for product owner with AI PDLC, memory, and evaluation.

## Overview

PO Agent Platform v2.1 is a new application built next to the existing legacy project. It provides:

- Intelligent task search in AS21/SWTR
- Task search by text, attachment type, and metadata
- Task summarization and quality analysis
- Sprint health, velocity, throughput, WIP, cycle time, lead time analysis
- Team capacity and competency matching
- Release scope, risk, and forecast
- Product/team/workflow knowledge
- Execution history and conversation memory
- Evaluation datasets and failure mining
- Controlled self-improvement with shadow mode and human approval

## Architecture

```
                     PO Workspace
                          |
                          v
                   PO Orchestrator
                          |
          +---------------+---------------+
          |               |               |
          v               v               v
   Task Intelligence  Sprint Intelligence  Team Intelligence
          |               |               |
          +---------------+---------------+
                          |
                   Release Intelligence
                          |
                          v
                   Shared Services
          +---------------+---------------+
          |               |               |
          v               v               v
     AS21 Adapter      Metrics Engine    Knowledge Layer
          |
          v
       AS21/SWTR
```

AI PDLC / learning loop:
- Runtime execution → Trace recorder → Session memory + History + Feedback
- Eval store → Failure miner → Improvement candidate generator
- Shadow evaluation → Regression gate → Human approval → Version registry

## Project Structure

```
po-agent-platform-v2/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── docs/
│   ├── architecture/
│   ├── adr/
│   ├── metrics/
│   ├── ai_pdlc/
│   └── runbooks/
├── config/
│   ├── products.yaml
│   ├── team.example.yaml
│   ├── workflow.yaml
│   └── quality_rules.yaml
├── data/
│   └── .gitkeep
├── src/
│   └── po_agent/
│       ├── api/
│       ├── config/
│       ├── domain/
│       ├── contracts/
│       ├── adapters/
│       ├── workflow/
│       ├── metrics/
│       ├── capabilities/
│       ├── orchestration/
│       ├── llm/
│       ├── knowledge/
│       ├── memory/
│       ├── history/
│       ├── feedback/
│       ├── evaluation/
│       ├── improvement/
│       ├── versions/
│       └── observability/
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── golden/
│   ├── integration/
│   ├── regression/
│   └── fixtures/
├── scripts/
│   ├── inspect_legacy.py
│   ├── validate_config.py
│   ├── run_eval.py
│   ├── compare_versions.py
│   └── run_dev.py
└── frontend/
```

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
cd po-agent-platform-v2

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Copy environment template
cp .env.example .env

# Edit .env and set your values (especially SWTR_TOKEN and LLM_API_KEY)
```

### Running the Application

```bash
# Start development server
uvicorn po_agent.main:app --reload --port 8004

# Run tests
pytest
```

### API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /version` - Version info
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | `po-agent-platform-v2` |
| `APP_VERSION` | Application version | `0.1.0` |
| `APP_ENV` | Environment (development/production) | `development` |
| `APP_PORT` | Application port | `8004` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Log format (json/text) | `json` |
| `CORRELATION_ID_HEADER` | Request ID header | `X-Request-ID` |
| `SWTR_BASE_URL` | SWTR API base URL | `https://portal.works.prod.sbt/swtr` |
| `SWTR_TOKEN` | SWTR personal access token | - |
| `LLM_API_BASE_URL` | LLM API base URL | `https://api.ai.sbt/v1` |
| `LLM_API_KEY` | LLM API key | - |
| `LLM_MODEL_NAME` | LLM model name | `qwen-coder-3.7` |
| `DATABASE_URL` | SQLite database path | `sqlite:///data/app.db` |

## Development Stages

See `PO_AGENT_PLATFORM_V2_GIGACODE_MASTER_SPEC_V2_1.md` for full specification.

1. ✅ **Step 01** - Create application skeleton (this step)
2. **Step 02** - Legacy discovery tool
3. **Step 03** - Canonical domain models
4. **Step 04** - Workflow configuration
5. **Step 05** - AS21 adapter contract
6. **Step 06** - Legacy AS21 bridge
7. **Step 07** - Workflow engine
8. **Step 08** - Metrics engine core
9. **Step 09** - Task intelligence search
10. **Step 10** - LLM client abstraction
11. **Step 11** - Task summary
12. **Step 12** - Task quality analysis
13. **Step 13** - Sprint intelligence
14. **Step 14** - Team config
15. **Step 15** - Team intelligence
16. **Step 16** - Release intelligence

## Contributing

1. Follow the development stages in the master specification
2. Write tests for all new functionality
3. Update documentation
4. Run `pytest` before committing

## License

MIT License - see LICENSE file for details.
