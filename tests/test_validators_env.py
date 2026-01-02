"""Tests for environment variable validation."""

from pathlib import Path

from agentpack.manifest import load_manifest
from agentpack.validators.env import validate_env_vars, _extract_env_refs


class TestEnvValidation:
    """Test environment variable validation."""

    def test_no_warnings_when_all_defined(
        self, fixtures_dir: Path, tmp_path: Path
    ) -> None:
        """No warnings when all variables are defined."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        devcontainer = tmp_path / ".devcontainer"
        devcontainer.mkdir()
        (devcontainer / ".env").write_text("EXAMPLE_API_KEY=secret\n")

        warnings = validate_env_vars(manifest, tmp_path)
        assert len(warnings) == 0

    def test_warning_for_missing_var(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """Warning when referenced variable is missing."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        devcontainer = tmp_path / ".devcontainer"
        devcontainer.mkdir()
        (devcontainer / ".env").write_text("")

        warnings = validate_env_vars(manifest, tmp_path)
        assert len(warnings) == 1
        assert "EXAMPLE_API_KEY" in warnings[0].message

    def test_no_env_file(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """Warning when .env file doesn't exist."""
        manifest = load_manifest(fixtures_dir / "full.yml")

        warnings = validate_env_vars(manifest, tmp_path)
        # Should warn about missing file and variable
        assert len(warnings) >= 1

    def test_extract_env_vars(self, fixtures_dir: Path) -> None:
        """Extract ${env:VAR} and ${VAR} patterns."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        # full.yml has ${env:EXAMPLE_API_KEY} in external-api server

        refs = _extract_env_refs(manifest)
        assert "EXAMPLE_API_KEY" in refs
