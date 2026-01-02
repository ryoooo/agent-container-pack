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

    def test_escapes_special_characters(self) -> None:
        """TOML strings with quotes/backslashes are properly escaped."""
        from agentpack.manifest.schema import Manifest

        manifest = Manifest.model_validate(
            {
                "version": "1",
                "project": {"name": "test", "description": "test"},
                "mcp": {
                    "servers": {
                        "special": {
                            "transport": "stdio",
                            "command": ["cmd", 'arg with "quotes"'],
                            "env": {"PATH": "C:\\Program Files\\app"},
                        },
                    },
                },
            }
        )
        result = generate_codex_config(manifest)
        # Quotes in args should be escaped
        assert r"\"quotes\"" in result
        # Backslashes should be escaped
        assert r"\\" in result

    def test_http_server_env_output(self) -> None:
        """HTTP servers output env variables."""
        from agentpack.manifest.schema import Manifest

        manifest = Manifest.model_validate(
            {
                "version": "1",
                "project": {"name": "test", "description": "test"},
                "mcp": {
                    "servers": {
                        "api": {
                            "transport": "http",
                            "url": "https://api.example.com/mcp",
                            "env": {"API_KEY": "${env:SECRET}"},
                        },
                    },
                },
            }
        )
        result = generate_codex_config(manifest)
        assert "API_KEY" in result
        assert "${env:SECRET}" in result or r"\${env:SECRET}" in result
