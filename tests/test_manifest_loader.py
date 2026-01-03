"""Tests for manifest loader."""

from pathlib import Path

import pytest

from agent_container_pack.manifest import Manifest
from agent_container_pack.manifest.loader import load_manifest, ManifestNotFoundError


class TestLoadManifest:
    """Test manifest loading from YAML files."""

    def test_load_minimal(self, fixtures_dir: Path) -> None:
        """Load minimal manifest."""
        manifest = load_manifest(fixtures_dir / "minimal.yml")
        assert isinstance(manifest, Manifest)
        assert manifest.project.name == "minimal-project"

    def test_load_full(self, fixtures_dir: Path) -> None:
        """Load full manifest with all fields."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        assert manifest.project.name == "full-project"
        assert manifest.stack == "python"
        assert "memory" in manifest.mcp.servers
        assert manifest.mcp.servers["memory"].transport == "stdio"

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Raise error when file not found."""
        with pytest.raises(ManifestNotFoundError):
            load_manifest(tmp_path / "nonexistent.yml")

    def test_load_from_directory(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """Load agentpack.yml from directory."""
        import shutil

        shutil.copy(fixtures_dir / "minimal.yml", tmp_path / "agentpack.yml")
        manifest = load_manifest(tmp_path)
        assert manifest.project.name == "minimal-project"
