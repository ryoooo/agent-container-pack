"""Tests for settings.json generator."""

from pathlib import Path

from syrupy.assertion import SnapshotAssertion

from agent_container_pack.generators.settings import generate_settings_json
from agent_container_pack.manifest import load_manifest


class TestSettingsGenerator:
    """Test .claude/settings.json generation."""

    def test_generate_minimal(
        self,
        fixtures_dir: Path,
        snapshot: SnapshotAssertion,
    ) -> None:
        """Generate settings from manifest with no MCP servers."""
        manifest = load_manifest(fixtures_dir / "minimal.yml")
        result = generate_settings_json(manifest)
        assert result == snapshot

    def test_generate_with_mcp(
        self,
        fixtures_dir: Path,
        snapshot: SnapshotAssertion,
    ) -> None:
        """Generate settings with MCP servers."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        result = generate_settings_json(manifest)
        assert result == snapshot

    def test_stdio_server_format(self, fixtures_dir: Path) -> None:
        """STDIO servers use command/args format."""
        import json

        manifest = load_manifest(fixtures_dir / "full.yml")
        result = generate_settings_json(manifest)
        data = json.loads(result)
        assert data["mcpServers"]["memory"]["command"] == "npx"
        assert data["mcpServers"]["memory"]["args"] == ["@anthropic/mcp-memory"]

    def test_http_server_format(self, fixtures_dir: Path) -> None:
        """HTTP servers use type/url format per Claude Code spec."""
        import json

        manifest = load_manifest(fixtures_dir / "full.yml")
        result = generate_settings_json(manifest)
        data = json.loads(result)
        # HTTP server should be included with type field
        assert "external-api" in data["mcpServers"]
        assert data["mcpServers"]["external-api"]["type"] == "http"
        assert data["mcpServers"]["external-api"]["url"] == "https://api.example.com/mcp"
