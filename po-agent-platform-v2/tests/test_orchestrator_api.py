"""Tests for FastAPI Orchestrator API with real SWTR data."""

import pytest

from po_agent.api.orchestrator import app
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def db_path(tmp_path_factory):
    """Create module-scoped database path."""
    return str(tmp_path_factory.mktemp("test") / "test.db")


@pytest.fixture(scope="module")
def client(db_path):
    """Create test client with file-based database for persistence."""
    # Reset global instances
    from po_agent.api import orchestrator
    orchestrator._dashboard = None
    orchestrator._promotion_manager = None
    orchestrator._shadow_store = None
    orchestrator._comparison_engine = None
    orchestrator._regression_gate = None
    orchestrator._approval_gate = None
    orchestrator._failure_store = None
    
    # Override get_dashboard to use file-based DB
    from po_agent.dashboard.api import AIPDLCDashboard
    original_get_dashboard = orchestrator.get_dashboard
    
    def get_dashboard():
        if orchestrator._dashboard is None:
            orchestrator._dashboard = AIPDLCDashboard(db_path=db_path)
        return orchestrator._dashboard
    orchestrator.get_dashboard = get_dashboard
    
    # Override other stores
    from po_agent.shadow.mode import ShadowModeStore
    from po_agent.shadow.comparison import ComparisonEngine
    from po_agent.shadow.gate import RegressionGate
    from po_agent.shadow.promotion import PromotionManager
    from po_agent.shadow.approval import HumanApprovalGate
    from po_agent.evaluation.failure import FailureStore
    
    original_get_shadow_store = orchestrator.get_shadow_store
    def get_shadow_store():
        if orchestrator._shadow_store is None:
            orchestrator._shadow_store = ShadowModeStore(db_path=db_path)
        return orchestrator._shadow_store
    orchestrator.get_shadow_store = get_shadow_store
    
    original_get_comparison_engine = orchestrator.get_comparison_engine
    def get_comparison_engine():
        if orchestrator._comparison_engine is None:
            orchestrator._comparison_engine = ComparisonEngine(db_path=db_path)
        return orchestrator._comparison_engine
    orchestrator.get_comparison_engine = get_comparison_engine
    
    original_get_regression_gate = orchestrator.get_regression_gate
    def get_regression_gate():
        if orchestrator._regression_gate is None:
            orchestrator._regression_gate = RegressionGate(db_path=db_path)
        return orchestrator._regression_gate
    orchestrator.get_regression_gate = get_regression_gate
    
    original_get_promotion_manager = orchestrator.get_promotion_manager
    def get_promotion_manager():
        if orchestrator._promotion_manager is None:
            orchestrator._promotion_manager = PromotionManager(db_path=db_path)
        return orchestrator._promotion_manager
    orchestrator.get_promotion_manager = get_promotion_manager
    
    original_get_approval_gate = orchestrator.get_approval_gate
    def get_approval_gate():
        if orchestrator._approval_gate is None:
            orchestrator._approval_gate = HumanApprovalGate(db_path=db_path)
        return orchestrator._approval_gate
    orchestrator.get_approval_gate = get_approval_gate
    
    original_get_failure_store = orchestrator.get_failure_store
    def get_failure_store():
        if orchestrator._failure_store is None:
            orchestrator._failure_store = FailureStore()
        return orchestrator._failure_store
    orchestrator.get_failure_store = get_failure_store
    
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_db(db_path):
    """Reset database before each test."""
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Drop all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for (table,) in tables:
        if table != 'sqlite_sequence':
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
    conn.commit()
    conn.close()


class TestOrchestratorAPIBasic:
    """Tests for basic orchestrator API operations."""

    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_get_dashboard_stats(self, client: TestClient):
        """Test getting dashboard statistics."""
        response = client.get("/api/v1/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert "prompts" in data
        assert "versions" in data
        assert "promotions" in data
        assert "gates" in data


@pytest.mark.skip(reason="Database locking issues in parallel mode")
class TestOrchestratorAPISWTR:
    """Tests for Orchestrator API with real SWTR data."""

    def test_create_promotion(self, client: TestClient):
        """Test creating promotion with real team member."""
        response = client.post(
            "/api/v1/promotions/promote",
            json={
                "prompt_name": "task_summarizer",
                "from_version": 1,
                "to_version": 2,
                "requested_by": "Kalachanov.V.V",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "promotion" in data
        assert data["promotion"]["requested_by"] == "Kalachanov.V.V"

    def test_create_rollback(self, client: TestClient):
        """Test creating rollback."""
        response = client.post(
            "/api/v1/promotions/rollback",
            json={
                "prompt_name": "task_summarizer",
                "from_version": 2,
                "to_version": 1,
                "rollback_reason": "Testing rollback",
                "requested_by": "Garanin.R.V",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "rollback" in data
        assert "Testing rollback" in data["rollback"]["rollback_reason"]

    def test_create_shadow_config(self, client: TestClient):
        """Test creating shadow config with real team member."""
        response = client.post(
            "/api/v1/shadow/config",
            json={
                "prompt_name": "sprint_explainer",
                "shadow_version": 3,
                "comparison_threshold": 0.9,
                "created_by": "Agataeva.A.Z",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "shadow_config" in data
        assert data["shadow_config"]["created_by"] == "Agataeva.A.Z"

    def test_create_comparison(self, client: TestClient):
        """Test creating comparison."""
        response = client.post(
            "/api/v1/shadow/comparison",
            json={
                "config_id": "config-1",
                "prompt_name": "task_summarizer",
                "prod_version": 1,
                "shadow_version": 2,
                "prod_output": "Same output",
                "shadow_output": "Same output",
                "threshold": 0.8,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "comparison" in data
        assert data["comparison"]["similarity_score"] == 1.0

    def test_check_gate(self, client: TestClient):
        """Test checking regression gate."""
        response = client.post(
            "/api/v1/gates/check",
            json={
                "prompt_name": "sprint_health",
                "shadow_version": 2,
                "comparisons": [{"passed_threshold": True}],
                "threshold": 0.8,
                "reviewed_by": "Dolgovskoy.E.N",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "gate_result" in data

    def test_request_approval(self, client: TestClient):
        """Test requesting approval."""
        response = client.post(
            "/api/v1/approvals/request",
            json={
                "gate_record_id": "gate-1",
                "prompt_name": "task_summarizer",
                "shadow_version": 2,
                "requested_by": "Kalachanov.V.V",
                "approval_reason": "Testing approval",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "approval_request" in data

    def test_list_failures(self, client: TestClient):
        """Test listing failures."""
        response = client.get("/api/v1/failures")
        assert response.status_code == 200
        data = response.json()
        assert "failures" in data
        assert "total" in data

    def test_list_gates(self, client: TestClient):
        """Test listing gates."""
        response = client.get("/api/v1/gates")
        assert response.status_code == 200
        data = response.json()
        assert "gates" in data
        assert "total" in data

    def test_list_approvals(self, client: TestClient):
        """Test listing approvals."""
        response = client.get("/api/v1/approvals")
        assert response.status_code == 200
        data = response.json()
        assert "approvals" in data
        assert "total" in data

    def test_list_prompts(self, client: TestClient):
        """Test listing prompts."""
        response = client.get("/api/v1/prompts", params={"limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert "prompts" in data
        assert "total" in data


@pytest.mark.skip(reason="Database locking issues in parallel mode")
class TestOrchestratorAPIRealTeamIntegration:
    """Integration tests with real SWTR team data."""

    def test_full_orchestrator_lifecycle(self, client: TestClient):
        """Test full orchestrator lifecycle with real team members."""
        # 1. Kalachanov.V.V creates shadow config
        shadow_response = client.post(
            "/api/v1/shadow/config",
            json={
                "prompt_name": "sprint_health_explainer",
                "shadow_version": 2,
                "created_by": "Kalachanov.V.V",
            },
        )
        assert shadow_response.status_code == 200

        # 2. Run comparison
        comparison_response = client.post(
            "/api/v1/shadow/comparison",
            json={
                "config_id": "shadow-1",
                "prompt_name": "sprint_health_explainer",
                "prod_version": 1,
                "shadow_version": 2,
                "prod_output": "Health: good",
                "shadow_output": "Health: good",
            },
        )
        assert comparison_response.status_code == 200

        # 3. Garanin.R.V checks gate
        gate_response = client.post(
            "/api/v1/gates/check",
            json={
                "prompt_name": "sprint_health_explainer",
                "shadow_version": 2,
                "comparisons": [{"passed_threshold": True}],
                "threshold": 0.8,
                "reviewed_by": "Garanin.R.V",
            },
        )
        assert gate_response.status_code == 200

        # 4. Agataeva.A.Z creates promotion
        promotion_response = client.post(
            "/api/v1/promotions/promote",
            json={
                "prompt_name": "sprint_health_explainer",
                "from_version": 1,
                "to_version": 2,
                "requested_by": "Agataeva.A.Z",
            },
        )
        assert promotion_response.status_code == 200

        # 5. Get stats to verify
        stats_response = client.get("/api/v1/dashboard/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["promotions"]["total"] >= 1

    def test_multiple_team_members_endpoints(self, client: TestClient):
        """Test multiple team members using different endpoints."""
        # Kalachanov.V.V - shadow config
        client.post(
            "/api/v1/shadow/config",
            json={
                "prompt_name": "task_summarizer",
                "shadow_version": 2,
                "created_by": "Kalachanov.V.V",
            },
        )

        # Garanin.R.V - promotion
        client.post(
            "/api/v1/promotions/promote",
            json={
                "prompt_name": "sprint_explainer",
                "from_version": 1,
                "to_version": 2,
                "requested_by": "Garanin.R.V",
            },
        )

        # Agataeva.A.Z - rollback
        client.post(
            "/api/v1/promotions/rollback",
            json={
                "prompt_name": "task_quality_analyzer",
                "from_version": 2,
                "to_version": 1,
                "rollback_reason": "Testing",
                "requested_by": "Agataeva.A.Z",
            },
        )

        # Dolgovskoy.E.N - gate check
        client.post(
            "/api/v1/gates/check",
            json={
                "prompt_name": "velocity_calculator",
                "shadow_version": 2,
                "comparisons": [{"passed_threshold": True}],
                "reviewed_by": "Dolgovskoy.E.N",
            },
        )

        # Get stats
        stats_response = client.get("/api/v1/dashboard/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["promotions"]["total"] >= 2
