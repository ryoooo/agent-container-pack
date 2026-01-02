"""Tests for generate command."""

from pathlib import Path
import subprocess
import sys


class TestGenerateCommand:
    """Test agentpack generate command."""

    def test_generate_dry_run(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """Generate command shows output without --write."""
        import shutil

        shutil.copy(fixtures_dir / "minimal.yml", tmp_path / "agentpack.yml")

        result = subprocess.run(
            [sys.executable, "-m", "agentpack", "generate"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "CLAUDE.md" in result.stdout
        assert "minimal-project" in result.stdout
        # Files should not be created
        assert not (tmp_path / "CLAUDE.md").exists()

    def test_generate_write(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """Generate command creates files with --write."""
        import shutil

        shutil.copy(fixtures_dir / "full.yml", tmp_path / "agentpack.yml")

        result = subprocess.run(
            [sys.executable, "-m", "agentpack", "generate", "--write"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / "AGENTS.md").exists()
        assert (tmp_path / ".claude" / "settings.json").exists()
        assert (tmp_path / "codex.config.toml").exists()

    def test_generate_manifest_not_found(self, tmp_path: Path) -> None:
        """Error when agentpack.yml not found."""
        result = subprocess.run(
            [sys.executable, "-m", "agentpack", "generate"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()

    def test_generate_updates_firewall(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """Generate updates firewall with HTTP MCP domains."""
        import shutil

        shutil.copy(fixtures_dir / "full.yml", tmp_path / "agentpack.yml")

        devcontainer = tmp_path / ".devcontainer"
        devcontainer.mkdir()
        (devcontainer / "init-firewall.sh").write_text(
            """#!/bin/bash
ALLOWED_DOMAINS=(
    "existing.com"
)
"""
        )

        result = subprocess.run(
            [sys.executable, "-m", "agentpack", "generate", "--write"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        content = (devcontainer / "init-firewall.sh").read_text()
        assert "api.example.com" in content
