"""Tests for manifest schema."""

import pytest
from pydantic import ValidationError

from agent_container_pack.manifest.schema import Manifest


class TestManifestValidation:
    """Test manifest validation."""

    def test_minimal_manifest(self) -> None:
        """Minimal valid manifest with required fields."""
        data = {
            "version": "1",
            "project": {
                "name": "test-project",
                "description": "Test project",
            },
        }
        manifest = Manifest.model_validate(data)
        assert manifest.version == "1"
        assert manifest.project.name == "test-project"

    def test_version_required(self) -> None:
        """Version field is required."""
        data = {
            "project": {
                "name": "test-project",
                "description": "Test project",
            },
        }
        with pytest.raises(ValidationError) as exc_info:
            Manifest.model_validate(data)
        assert "version" in str(exc_info.value)

    def test_project_required(self) -> None:
        """Project field is required."""
        data = {"version": "1"}
        with pytest.raises(ValidationError) as exc_info:
            Manifest.model_validate(data)
        assert "project" in str(exc_info.value)

    def test_full_manifest(self) -> None:
        """Full manifest with all fields."""
        data = {
            "version": "1",
            "project": {
                "name": "my-app",
                "description": "My application",
            },
            "docs": {
                "mode": "single-stack",
                "defaultStack": "auto",
                "maxLines": 250,
            },
            "stack": "python",
            "stacks": {
                "python": {
                    "detect": {"any": ["pyproject.toml", "requirements.txt"]},
                    "deps": "uv sync",
                    "lint": "uv run ruff check .",
                    "typecheck": "uv run ty check",
                    "test": "uv run pytest",
                    "run": "uv run python main.py",
                    "skills": {"required": ["python-dev"]},
                },
            },
            "mcp": {
                "servers": {
                    "memory": {
                        "transport": "stdio",
                        "command": ["npx", "@anthropic/mcp-memory"],
                        "env": {"MEMORY_PATH": "${workspaceFolder}/.memory"},
                    },
                    "external-api": {
                        "transport": "http",
                        "url": "https://api.example.com/mcp",
                        "env": {"API_KEY": "${env:EXAMPLE_API_KEY}"},
                    },
                },
            },
            "workflows": [
                {
                    "name": "開発フロー",
                    "steps": [
                        "uv run ruff format . && uv run ruff check .",
                        "uv run pytest",
                    ],
                },
            ],
            "pre_commit": ["prettier", "ruff", "ty"],
            "safety": {
                "preset": "default",
                "custom": ["本番DBに直接接続しない"],
            },
            "custom_content": "## Quick Start\n\n```bash\npython main.py\n```",
        }
        manifest = Manifest.model_validate(data)
        assert manifest.stack == "python"
        assert manifest.stacks["python"].deps == "uv sync"
        assert len(manifest.mcp.servers) == 2
        assert manifest.mcp.servers["memory"].transport == "stdio"
        assert manifest.mcp.servers["external-api"].transport == "http"

    def test_invalid_docs_mode(self) -> None:
        """Invalid docs mode should fail validation."""
        data = {
            "version": "1",
            "project": {"name": "test", "description": "test"},
            "docs": {"mode": "invalid"},
        }
        with pytest.raises(ValidationError) as exc_info:
            Manifest.model_validate(data)
        assert "mode" in str(exc_info.value)

    def test_mcp_server_requires_transport(self) -> None:
        """MCP server must have valid transport."""
        data = {
            "version": "1",
            "project": {"name": "test", "description": "test"},
            "mcp": {
                "servers": {
                    "invalid": {"command": ["echo", "test"]},
                },
            },
        }
        # stdio is default, so this should work
        manifest = Manifest.model_validate(data)
        assert manifest.mcp.servers["invalid"].transport == "stdio"

    def test_mcp_stdio_command_requires_at_least_one_element(self) -> None:
        """STDIO MCP server command must have at least one element."""
        data = {
            "version": "1",
            "project": {"name": "test", "description": "test"},
            "mcp": {
                "servers": {
                    "empty": {"transport": "stdio", "command": []},
                },
            },
        }
        with pytest.raises(ValidationError) as exc_info:
            Manifest.model_validate(data)
        assert "command" in str(exc_info.value).lower()
