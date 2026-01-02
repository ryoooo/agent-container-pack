"""Tests for stack detection."""

from pathlib import Path

import pytest

from agentpack.manifest import load_manifest
from agentpack.manifest.schema import Manifest
from agentpack.stack.detector import AmbiguousStackError, detect_stack, NoStackDetectedError


class TestStackDetection:
    """Test stack detection from project files."""

    def test_detect_python_pyproject(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """Detect Python stack from pyproject.toml."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        (tmp_path / "pyproject.toml").touch()

        result = detect_stack(manifest, tmp_path)
        assert result == "python"

    def test_detect_python_requirements(
        self, fixtures_dir: Path, tmp_path: Path
    ) -> None:
        """Detect Python stack from requirements.txt."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        (tmp_path / "requirements.txt").touch()

        result = detect_stack(manifest, tmp_path)
        assert result == "python"

    def test_no_stack_detected(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """Error when no stack files found."""
        manifest = load_manifest(fixtures_dir / "full.yml")

        with pytest.raises(NoStackDetectedError):
            detect_stack(manifest, tmp_path)

    def test_explicit_stack_overrides_detection(
        self, fixtures_dir: Path, tmp_path: Path
    ) -> None:
        """Explicit stack in manifest overrides detection."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        # manifest.stack is "python", so detection is skipped
        result = detect_stack(manifest, tmp_path, use_manifest_stack=True)
        assert result == "python"

    def test_ambiguous_stacks_raises_error(self, tmp_path: Path) -> None:
        """Error when multiple stacks detected in single-stack mode."""
        manifest = Manifest.model_validate(
            {
                "version": "1",
                "project": {"name": "test", "description": "test"},
                "docs": {"mode": "single-stack"},
                "stacks": {
                    "python": {"detect": {"any": ["pyproject.toml"]}},
                    "node": {"detect": {"any": ["package.json"]}},
                },
            }
        )
        (tmp_path / "pyproject.toml").touch()
        (tmp_path / "package.json").touch()

        with pytest.raises(AmbiguousStackError):
            detect_stack(manifest, tmp_path)
