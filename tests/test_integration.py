"""Integration tests for full agentpack workflow."""

from pathlib import Path
import subprocess
import sys


class TestFullWorkflow:
    """Test complete agentpack workflows."""

    def test_init_and_generate(self, tmp_path: Path) -> None:
        """Full workflow: init -> edit manifest -> generate."""
        # Skip template download in test, create files manually
        devcontainer = tmp_path / ".devcontainer"
        devcontainer.mkdir()
        (devcontainer / "devcontainer.json").write_text("{}")
        (devcontainer / "Dockerfile").write_text("FROM ubuntu")
        (devcontainer / "init-firewall.sh").write_text(
            """#!/bin/bash
ALLOWED_DOMAINS=(
)
"""
        )

        # Create manifest
        manifest = tmp_path / "agentpack.yml"
        manifest.write_text(
            """version: "1"

project:
  name: "integration-test"
  description: "Integration test project"

stack: python

stacks:
  python:
    detect:
      any: ["pyproject.toml"]
    deps: "uv sync"
    lint: "uv run ruff check ."
    test: "uv run pytest"

mcp:
  servers:
    api:
      transport: http
      url: "https://api.test.com/mcp"
    memory:
      transport: stdio
      command: ["npx", "@anthropic/mcp-memory"]
"""
        )

        # Create pyproject.toml for stack detection
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'")

        # Run generate
        result = subprocess.run(
            [sys.executable, "-m", "agent_container_pack", "generate", "--write"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, (
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

        # Verify outputs
        claude_md = (tmp_path / "CLAUDE.md").read_text()
        assert "integration-test" in claude_md
        assert "uv sync" in claude_md
        assert "uv run pytest" in claude_md

        settings = (tmp_path / ".claude" / "settings.json").read_text()
        # HTTP servers use type field in settings.json
        assert '"type": "http"' in settings
        assert "api.test.com" in settings

        codex_config = (tmp_path / "codex.config.toml").read_text()
        # Codex supports both stdio and HTTP servers
        assert "[mcp_servers.memory]" in codex_config
        assert "[mcp_servers.api]" in codex_config
        assert "api.test.com" in codex_config

        firewall = (devcontainer / "init-firewall.sh").read_text()
        assert "api.test.com" in firewall

    def test_generate_validates_skills(self, tmp_path: Path) -> None:
        """Generate warns about missing skills."""
        manifest = tmp_path / "agentpack.yml"
        manifest.write_text(
            """version: "1"

project:
  name: "test"
  description: "Test"

stacks:
  python:
    skills:
      required: ["missing-skill"]
"""
        )

        result = subprocess.run(
            [sys.executable, "-m", "agent_container_pack", "generate"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "missing-skill" in result.stderr
        assert "SKILL.md not found" in result.stderr
