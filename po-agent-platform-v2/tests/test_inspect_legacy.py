"""Tests for inspect_legacy.py - Legacy discovery tool."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module (it will be at po-agent-platform-v2/scripts/inspect_legacy.py)
import sys

# Add the scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestLegacyComponent:
    """Tests for LegacyComponent class."""

    def test_legacy_component_init(self):
        """Test LegacyComponent initialization."""
        from inspect_legacy import LegacyComponent

        component = LegacyComponent(
            name="Test Component",
            path="/path/to/component",
            type_="test",
            responsibility="Test responsibility",
            reuse="YES",
            target_module="target.module",
            risks=["Risk 1"],
            notes="Test notes",
        )

        assert component.name == "Test Component"
        assert component.path == "/path/to/component"
        assert component.type_ == "test"
        assert component.responsibility == "Test responsibility"
        assert component.reuse == "YES"
        assert component.target_module == "target.module"
        assert component.risks == ["Risk 1"]
        assert component.notes == "Test notes"

    def test_legacy_component_to_dict(self):
        """Test LegacyComponent.to_dict() method."""
        from inspect_legacy import LegacyComponent

        component = LegacyComponent(
            name="Test Component",
            path="/path/to/component",
            type_="test",
            responsibility="Test responsibility",
            reuse="YES",
            target_module="target.module",
            risks=["Risk 1"],
            notes="Test notes",
        )

        result = component.to_dict()

        assert result == {
            "name": "Test Component",
            "path": "/path/to/component",
            "type": "test",
            "responsibility": "Test responsibility",
            "reuse": "YES",
            "target_module": "target.module",
            "risks": ["Risk 1"],
            "notes": "Test notes",
        }

    def test_legacy_component_default_risks(self):
        """Test LegacyComponent defaults to empty risks list."""
        from inspect_legacy import LegacyComponent

        component = LegacyComponent(
            name="Test Component",
            path="/path/to/component",
            type_="test",
            responsibility="Test responsibility",
            reuse="YES",
            target_module="target.module",
        )

        assert component.risks == []


class TestLegacyInspector:
    """Tests for LegacyInspector class."""

    @pytest.fixture
    def temp_legacy_dir(self, tmp_path):
        """Create a temporary legacy directory structure."""
        # Create some dummy files
        (tmp_path / "swtr_client.py").write_text("# SWTR Client")
        (tmp_path / "s21_mcp_proxy.py").write_text("# MCP Proxy")
        (tmp_path / "jira_mcp_server.py").write_text("# Jira MCP")
        (tmp_path / "mcp-swtr").mkdir()
        (tmp_path / "mcp-swtr" / "mcp_server.py").write_text("# SWTR MCP")
        (tmp_path / "s21-task-agent").mkdir()
        (tmp_path / "task-api").mkdir()
        (tmp_path / "task-api" / "config").mkdir()
        (tmp_path / "task-api" / "config" / "metrics.yaml").write_text("{}")
        (tmp_path / "task-api" / "config" / "thresholds.yaml").write_text("{}")
        (tmp_path / "task-api" / "config" / "workflow_statuses.yaml").write_text("{}")
        (tmp_path / "task-api" / "config" / "status_mapping.yaml").write_text("{}")
        (tmp_path / "task-api" / "config" / "team_members.yaml").write_text("{}")
        (tmp_path / "task-api" / "main.py").write_text("# Main")

        return tmp_path

    @pytest.fixture
    def inspector(self, temp_legacy_dir):
        """Create a LegacyInspector instance."""
        from inspect_legacy import LegacyInspector

        return LegacyInspector(temp_legacy_dir)

    def test_inspector_init(self, temp_legacy_dir):
        """Test LegacyInspector initialization."""
        from inspect_legacy import LegacyInspector

        inspector = LegacyInspector(temp_legacy_dir)
        assert inspector.legacy_base == temp_legacy_dir
        assert inspector.components == []

    def test_inspect_finds_components(self, temp_legacy_dir):
        """Test that inspect() finds all expected components."""
        from inspect_legacy import LegacyInspector

        inspector = LegacyInspector(temp_legacy_dir)
        components = inspector.inspect()

        # We should find multiple components
        assert len(components) > 0

        # Check that we found some expected types
        component_types = {c.type_ for c in components}
        assert "transport" in component_types
        assert "mcp" in component_types
        assert "config" in component_types

    def test_inspector_to_json(self, temp_legacy_dir):
        """Test LegacyInspector.to_json() method."""
        from inspect_legacy import LegacyInspector

        inspector = LegacyInspector(temp_legacy_dir)
        inspector.inspect()

        result = inspector.to_json()

        assert "inspection_date" in result
        assert "legacy_base" in result
        assert "components" in result
        assert "summary" in result

        assert result["legacy_base"] == str(temp_legacy_dir)
        assert len(result["components"]) > 0
        assert "total" in result["summary"]
        assert "by_type" in result["summary"]
        assert "reuse_by_category" in result["summary"]

    def test_count_by_type(self, temp_legacy_dir):
        """Test _count_by_type() method."""
        from inspect_legacy import LegacyInspector

        inspector = LegacyInspector(temp_legacy_dir)
        inspector.inspect()

        counts = inspector._count_by_type()

        # Check that types are counted
        assert isinstance(counts, dict)
        for key, value in counts.items():
            assert isinstance(key, str)
            assert isinstance(value, int)
            assert value > 0

    def test_count_by_reuse(self, temp_legacy_dir):
        """Test _count_by_reuse() method."""
        from inspect_legacy import LegacyInspector

        inspector = LegacyInspector(temp_legacy_dir)
        inspector.inspect()

        counts = inspector._count_by_reuse()

        # Check that reuse categories are counted
        assert isinstance(counts, dict)
        for key, value in counts.items():
            assert isinstance(key, str)
            assert isinstance(value, int)
            assert value > 0


class TestGenerateReuseMap:
    """Tests for generate_reuse_map function."""

    def test_generate_reuse_map_basic(self):
        """Test basic generate_reuse_map functionality."""
        from inspect_legacy import LegacyComponent, generate_reuse_map

        components = [
            LegacyComponent(
                name="Component 1",
                path="/path1",
                type_="test",
                responsibility="Responsibility 1",
                reuse="YES",
                target_module="target1",
            ),
            LegacyComponent(
                name="Component 2",
                path="/path2",
                type_="test",
                responsibility="Responsibility 2",
                reuse="PARTIAL",
                target_module="target2",
                risks=["Risk"],
                notes="Notes",
            ),
        ]

        result = generate_reuse_map(components)

        # Check that result contains expected content
        assert "# Legacy Reuse Map" in result
        assert "Component 1" in result
        assert "Component 2" in result
        assert "✅" in result  # YES symbol
        assert "⚠️" in result  # PARTIAL symbol
        assert "/path1" in result
        assert "/path2" in result

    def test_generate_reuse_map_no_risks(self):
        """Test generate_reuse_map without risks."""
        from inspect_legacy import LegacyComponent, generate_reuse_map

        components = [
            LegacyComponent(
                name="Component",
                path="/path",
                type_="test",
                responsibility="Responsibility",
                reuse="YES",
                target_module="target",
            ),
        ]

        result = generate_reuse_map(components)

        assert "**Risks:**" not in result  # Should not include risks section

    def test_generate_reuse_map_with_risks(self):
        """Test generate_reuse_map with risks."""
        from inspect_legacy import LegacyComponent, generate_reuse_map

        components = [
            LegacyComponent(
                name="Component",
                path="/path",
                type_="test",
                responsibility="Responsibility",
                reuse="YES",
                target_module="target",
                risks=["Risk 1", "Risk 2"],
            ),
        ]

        result = generate_reuse_map(components)

        assert "**Risks:**" in result
        assert "- Risk 1" in result
        assert "- Risk 2" in result

    def test_generate_reuse_map_with_notes(self):
        """Test generate_reuse_map with notes."""
        from inspect_legacy import LegacyComponent, generate_reuse_map

        components = [
            LegacyComponent(
                name="Component",
                path="/path",
                type_="test",
                responsibility="Responsibility",
                reuse="YES",
                target_module="target",
                notes="Important notes",
            ),
        ]

        result = generate_reuse_map(components)

        assert "**Notes:** Important notes" in result
