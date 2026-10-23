# Public-safe MCP-SWTR image: credentials must be supplied only at runtime.
# Keep Python aligned with pyproject.toml (requires-python >=3.13).
FROM python:3.13-slim

ARG PORT=8000
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=${PORT}

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

# Explicit sources only: never copy local .env, credentials, git metadata, or caches.
COPY mcp_server.py ./mcp_server.py
COPY models/ ./models/

RUN useradd --system --create-home --shell /usr/sbin/nologin app \
    && chown -R app:app /app
USER app

EXPOSE ${PORT}
CMD ["python", "mcp_server.py"]
