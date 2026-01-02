"""Tests for markdown generator."""

from pathlib import Path

from syrupy.assertion import SnapshotAssertion

from agentpack.generators.markdown import generate_claude_md
from agentpack.manifest import load_manifest


class TestMarkdownGenerator:
    """Test CLAUDE.md/AGENTS.md generation."""

    def test_generate_minimal(
        self,
        fixtures_dir: Path,
        snapshot: SnapshotAssertion,
    ) -> None:
        """Generate markdown from minimal manifest."""
        manifest = load_manifest(fixtures_dir / "minimal.yml")
        result = generate_claude_md(manifest)
        assert result == snapshot

    def test_generate_full(
        self,
        fixtures_dir: Path,
        snapshot: SnapshotAssertion,
    ) -> None:
        """Generate markdown from full manifest."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        result = generate_claude_md(manifest)
        assert result == snapshot
