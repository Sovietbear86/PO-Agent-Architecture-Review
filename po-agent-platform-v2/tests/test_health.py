"""Health and version endpoint tests for PO Agent Platform v2."""

import pytest
from fastapi.testclient import TestClient

from po_agent import __app_name__, __version__
from po_agent.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert __app_name__ in data["message"]
    assert "version" in data
    assert data["version"] == __version__
    assert "docs" in data


def test_health_endpoint(client):
    """Root health endpoint reports runtime/source readiness."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "timestamp" in data
    assert data["service"] == __app_name__
    assert data["runtime"] == "harness-dialogue-v2"
    assert "source_status" in data
    assert "skill_readiness" in data


def test_live_endpoint(client):
    """Liveness endpoint remains a process-only ping."""
    response = client.get("/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == __app_name__
    assert data["check"] == "liveness"


def test_version_endpoint(client):
    """Test version endpoint."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == __app_name__
    assert data["version"] == __version__
    assert data["app_version"] == __version__
    assert "timestamp" in data


def test_health_returns_timestamp(client):
    """Test readiness health endpoint returns ISO timestamp."""
    response = client.get("/health")
    data = response.json()
    timestamp = data["timestamp"]
    # Check timestamp format (ISO 8601)
    assert "T" in timestamp
    assert timestamp.endswith("Z")


def test_version_returns_timestamp(client):
    """Test version endpoint returns ISO timestamp."""
    response = client.get("/version")
    data = response.json()
    timestamp = data["timestamp"]
    # Check timestamp format (ISO 8601)
    assert "T" in timestamp
    assert timestamp.endswith("Z")
