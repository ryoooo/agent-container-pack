"""Tests for codex.config.toml generator."""

from pathlib import Path

from syrupy.assertion import SnapshotAssertion

from agent_container_pack.generators.codex_config import generate_codex_config
from agent_container_pack.manifest import load_manifest


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

    def test_http_server_format(self, fixtures_dir: Path) -> None:
        """HTTP servers use url field per Codex spec."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        result = generate_codex_config(manifest)
        assert "[mcp_servers.external-api]" in result
        assert 'url = "https://api.example.com/mcp"' in result

    def test_escapes_special_characters(self) -> None:
        """TOML strings with quotes/backslashes are properly escaped."""
        from agent_container_pack.manifest.schema import Manifest

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

    def test_escapes_newlines_prevents_injection(self) -> None:
        """Newlines in env values are escaped to prevent TOML injection."""
        from agent_container_pack.manifest.schema import Manifest

        manifest = Manifest.model_validate(
            {
                "version": "1",
                "project": {"name": "test", "description": "test"},
                "mcp": {
                    "servers": {
                        "test": {
                            "transport": "stdio",
                            "command": ["cmd"],
                            "env": {"KEY": 'value"}\n[evil]\nmalicious = "true'},
                        },
                    },
                },
            }
        )
        result = generate_codex_config(manifest)
        # Should only have one section (no injection)
        assert result.count("[mcp_servers.") == 1
        # Newlines should be escaped as \n
        assert r"\n" in result
        # The output should be valid - all on expected number of lines
        lines = result.strip().split("\n")
        assert len(lines) == 3  # section, command, env

    def test_http_server_no_env_in_output(self) -> None:
        """HTTP servers don't output env (use http_headers instead per Codex spec)."""
        from agent_container_pack.manifest.schema import Manifest

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
        # HTTP server should be in output with url
        assert "[mcp_servers.api]" in result
        assert 'url = "https://api.example.com/mcp"' in result
        # env is not a valid Codex HTTP field - should not be output
        assert "API_KEY" not in result
