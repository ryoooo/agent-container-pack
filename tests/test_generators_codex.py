"""Tests for codex.config.toml generator."""

from pathlib import Path

from syrupy.assertion import SnapshotAssertion

from agentpack.generators.codex_config import generate_codex_config
from agentpack.manifest import load_manifest


class TestCodexConfigGenerator:
    """Test codex.config.toml generation."""

    def test_generate_minimal(
        self,
        fixtures_dir: Path,
        snapshot: SnapshotAssertion,
    ) -> None:
        """Generate config from manifest with no MCP servers."""
        manifest = load_manifest(fixtures_dir / "minimal.yml")
        result = generate_codex_config(manifest)
        assert result == snapshot

    def test_generate_with_mcp(
        self,
        fixtures_dir: Path,
        snapshot: SnapshotAssertion,
    ) -> None:
        """Generate config with both STDIO and HTTP MCP servers."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        result = generate_codex_config(manifest)
        assert result == snapshot

    def test_stdio_format(self, fixtures_dir: Path) -> None:
        """STDIO servers have command and args."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        result = generate_codex_config(manifest)
        assert "[mcp_servers.memory]" in result
        assert 'command = "npx"' in result

    def test_http_format(self, fixtures_dir: Path) -> None:
        """HTTP servers have url field."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        result = generate_codex_config(manifest)
        assert "[mcp_servers.external-api]" in result
        assert 'url = "https://api.example.com/mcp"' in result
