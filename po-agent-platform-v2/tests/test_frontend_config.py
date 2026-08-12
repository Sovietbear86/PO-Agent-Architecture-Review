"""Tests for Frontend build configuration."""

import os
import json
import pytest
from pathlib import Path


FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


class TestFrontendConfig:
    """Tests for frontend configuration files."""

    def test_package_json_exists(self):
        """Test that package.json exists."""
        assert (FRONTEND_DIR / "package.json").exists()

    def test_package_json_valid(self):
        """Test that package.json is valid JSON."""
        with open(FRONTEND_DIR / "package.json") as f:
            data = json.load(f)

        assert "name" in data
        assert data["name"] == "po-agent-frontend"
        assert "scripts" in data
        assert "dev" in data["scripts"]
        assert "build" in data["scripts"]

    def test_vite_config_exists(self):
        """Test that vite.config.ts exists."""
        assert (FRONTEND_DIR / "vite.config.ts").exists()

    def test_vite_config_valid(self):
        """Test that vite.config.ts has valid content."""
        with open(FRONTEND_DIR / "vite.config.ts") as f:
            content = f.read()

        assert "react" in content.lower()
        assert "vite" in content.lower()
        assert "port" in content.lower() or "server" in content.lower()

    def test_tailwind_config_exists(self):
        """Test that tailwind.config.js exists."""
        assert (FRONTEND_DIR / "tailwind.config.js").exists()

    def test_tailwind_config_valid(self):
        """Test that tailwind.config.js has valid content."""
        with open(FRONTEND_DIR / "tailwind.config.js") as f:
            content = f.read()

        assert "tailwindcss" in content.lower()
        assert "content" in content.lower()

    def test_tsconfig_exists(self):
        """Test that tsconfig.json exists."""
        assert (FRONTEND_DIR / "tsconfig.json").exists()

    def test_tsconfig_node_exists(self):
        """Test that tsconfig.node.json exists."""
        assert (FRONTEND_DIR / "tsconfig.node.json").exists()

    def test_postcss_config_exists(self):
        """Test that postcss.config.js exists."""
        assert (FRONTEND_DIR / "postcss.config.js").exists()


class TestFrontendSourceStructure:
    """Tests for frontend source structure."""

    def test_main_tsx_exists(self):
        """Test that main.tsx exists."""
        assert (FRONTEND_DIR / "src/main.tsx").exists()

    def test_index_css_exists(self):
        """Test that index.css exists."""
        assert (FRONTEND_DIR / "src/index.css").exists()

    def test_views_directory_exists(self):
        """Test that views directory exists."""
        assert (FRONTEND_DIR / "src/views").is_dir()

    def test_api_directory_exists(self):
        """Test that api directory exists."""
        assert (FRONTEND_DIR / "src/api").is_dir()

    def test_types_directory_exists(self):
        """Test that types directory exists."""
        assert (FRONTEND_DIR / "src/types").is_dir()

    def test_components_directory_exists(self):
        """Test that components directory exists."""
        assert (FRONTEND_DIR / "src/components").is_dir()


class TestFrontendViews:
    """Tests for frontend view files."""

    VIEW_FILES = [
        "AssistantView.tsx",
        "TasksView.tsx",
        "SprintView.tsx",
        "TeamView.tsx",
        "ReleasesView.tsx",
        "QualityView.tsx",
    ]

    def test_all_views_exist(self):
        """Test that all view files exist."""
        for view in self.VIEW_FILES:
            assert (FRONTEND_DIR / f"src/views/{view}").exists(), f"Missing view: {view}"

    def test_views_have_react_imports(self):
        """Test that views have required imports."""
        for view in self.VIEW_FILES:
            with open(FRONTEND_DIR / f"src/views/{view}") as f:
                content = f.read()

            assert "react" in content.lower() or "useState" in content or "useEffect" in content

    def test_components_have_react_imports(self):
        """Test that components have required imports."""
        component_files = [
            "KanbanBoard.tsx",
            "TeamDashboard.tsx",
            "SprintMetrics.tsx",
            "QualityIndicators.tsx",
            "CreateTaskForm.tsx",
        ]
        for comp in component_files:
            with open(FRONTEND_DIR / f"src/components/{comp}") as f:
                content = f.read()
            assert "react" in content.lower() or "useState" in content or "useEffect" in content or "useMemo" in content

    def test_views_export_components(self):
        """Test that views export components."""
        for view in self.VIEW_FILES:
            with open(FRONTEND_DIR / f"src/views/{view}") as f:
                content = f.read()

            assert "export" in content
            assert "function" in content or "const" in content


class TestFrontendComponents:
    """Tests for frontend components."""

    COMPONENT_FILES = [
        "KanbanBoard.tsx",
        "TeamDashboard.tsx",
        "SprintMetrics.tsx",
        "QualityIndicators.tsx",
        "CreateTaskForm.tsx",
        "AIDashboard.tsx",
        "ImprovementCandidates.tsx",
        "PromptRegistry.tsx",
        "VersionHistory.tsx",
        "AgentHistory.tsx",
    ]

    def test_all_components_exist(self):
        """Test that all component files exist."""
        for comp in self.COMPONENT_FILES:
            assert (FRONTEND_DIR / f"src/components/{comp}").exists(), f"Missing component: {comp}"

    def test_components_export_functions(self):
        """Test that components export functions."""
        for comp in self.COMPONENT_FILES:
            with open(FRONTEND_DIR / f"src/components/{comp}") as f:
                content = f.read()
            assert "export" in content
            assert "function" in content


class TestFrontendAPI:
    """Tests for frontend API client."""

    def test_api_client_exists(self):
        """Test that api/client.ts exists."""
        assert (FRONTEND_DIR / "src/api/client.ts").exists()

    def test_api_client_has_axios(self):
        """Test that api client imports axios."""
        with open(FRONTEND_DIR / "src/api/client.ts") as f:
            content = f.read()

        assert "axios" in content or "import" in content

    def test_api_types_exists(self):
        """Test that types/index.ts exists."""
        assert (FRONTEND_DIR / "src/types/index.ts").exists()


class TestFrontendLayout:
    """Tests for frontend layout components."""

    def test_layout_exists(self):
        """Test that Layout component exists."""
        assert (FRONTEND_DIR / "src/components/Layout.tsx").exists()

    def test_layout_has_navigation(self):
        """Test that layout has navigation."""
        with open(FRONTEND_DIR / "src/components/Layout.tsx") as f:
            content = f.read()

        assert "nav" in content.lower()
        assert "Link" in content or "router" in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
