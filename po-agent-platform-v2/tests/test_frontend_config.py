"""Tests for Frontend build configuration."""

import json
from pathlib import Path

import pytest


FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
WORKSPACE_APP = FRONTEND_DIR / "src/recovery/WorkspaceApp.tsx"


class TestFrontendConfig:
    """Tests for frontend configuration files."""

    def test_package_json_exists(self):
        assert (FRONTEND_DIR / "package.json").exists()

    def test_package_json_valid(self):
        with open(FRONTEND_DIR / "package.json") as f:
            data = json.load(f)

        assert data["name"] == "po-agent-frontend"
        assert "dev" in data["scripts"]
        assert "build" in data["scripts"]

    def test_vite_config_exists(self):
        assert (FRONTEND_DIR / "vite.config.ts").exists()

    def test_vite_config_valid(self):
        content = (FRONTEND_DIR / "vite.config.ts").read_text()
        assert "react" in content.lower()
        assert "vite" in content.lower()
        assert "port" in content.lower() or "server" in content.lower()

    def test_tailwind_config_exists(self):
        assert (FRONTEND_DIR / "tailwind.config.js").exists()

    def test_tailwind_config_valid(self):
        content = (FRONTEND_DIR / "tailwind.config.js").read_text()
        assert "tailwindcss" in content.lower()
        assert "content" in content.lower()

    def test_tsconfig_exists(self):
        assert (FRONTEND_DIR / "tsconfig.json").exists()

    def test_tsconfig_node_exists(self):
        assert (FRONTEND_DIR / "tsconfig.node.json").exists()

    def test_postcss_config_exists(self):
        assert (FRONTEND_DIR / "postcss.config.js").exists()


class TestFrontendSourceStructure:
    def test_main_tsx_exists(self):
        assert (FRONTEND_DIR / "src/main.tsx").exists()

    def test_index_css_exists(self):
        assert (FRONTEND_DIR / "src/index.css").exists()

    def test_views_directory_exists(self):
        assert (FRONTEND_DIR / "src/views").is_dir()

    def test_api_directory_exists(self):
        assert (FRONTEND_DIR / "src/api").is_dir()

    def test_types_directory_exists(self):
        assert (FRONTEND_DIR / "src/types").is_dir()

    def test_components_directory_exists(self):
        assert (FRONTEND_DIR / "src/components").is_dir()

    def test_recovery_workspace_exists(self):
        assert WORKSPACE_APP.exists()


class TestFrontendViews:
    VIEW_FILES = [
        "AssistantView.tsx",
        "TasksView.tsx",
        "SprintView.tsx",
        "TeamView.tsx",
        "ReleasesView.tsx",
        "QualityView.tsx",
    ]

    def test_all_views_exist(self):
        for view in self.VIEW_FILES:
            assert (FRONTEND_DIR / f"src/views/{view}").exists(), f"Missing view: {view}"

    def test_views_have_react_imports(self):
        for view in self.VIEW_FILES:
            content = (FRONTEND_DIR / f"src/views/{view}").read_text()
            assert "react" in content.lower() or "useState" in content or "useEffect" in content

    def test_components_have_react_imports(self):
        component_files = [
            "KanbanBoard.tsx",
            "TeamDashboard.tsx",
            "SprintMetrics.tsx",
            "QualityIndicators.tsx",
            "CreateTaskForm.tsx",
        ]
        for comp in component_files:
            content = (FRONTEND_DIR / f"src/components/{comp}").read_text()
            assert "react" in content.lower() or "useState" in content or "useEffect" in content or "useMemo" in content

    def test_views_export_components(self):
        for view in self.VIEW_FILES:
            content = (FRONTEND_DIR / f"src/views/{view}").read_text()
            assert "export" in content
            assert "function" in content or "const" in content


class TestFrontendComponents:
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
        for comp in self.COMPONENT_FILES:
            assert (FRONTEND_DIR / f"src/components/{comp}").exists(), f"Missing component: {comp}"

    def test_components_export_functions(self):
        for comp in self.COMPONENT_FILES:
            content = (FRONTEND_DIR / f"src/components/{comp}").read_text()
            assert "export" in content
            assert "function" in content


class TestFrontendAPI:
    def test_api_client_exists(self):
        assert (FRONTEND_DIR / "src/api/client.ts").exists()

    def test_api_client_has_axios(self):
        content = (FRONTEND_DIR / "src/api/client.ts").read_text()
        assert "axios" in content or "import" in content

    def test_api_types_exists(self):
        assert (FRONTEND_DIR / "src/types/index.ts").exists()


class TestFrontendLayout:
    """Current recovery workspace shell contract."""

    def test_workspace_shell_exists(self):
        assert WORKSPACE_APP.exists()

    def test_workspace_shell_has_navigation(self):
        content = WORKSPACE_APP.read_text()
        assert "<nav>" in content
        assert "NavLink" in content
        assert "const nav =" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
