"""Tests for firewall updater."""

from pathlib import Path

from agentpack.devcontainer.firewall import update_firewall, extract_domains
from agentpack.manifest import load_manifest


class TestFirewallUpdater:
    """Test init-firewall.sh updater."""

    def test_extract_domains_from_http_mcp(self, fixtures_dir: Path) -> None:
        """Extract domains from HTTP MCP servers."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        domains = extract_domains(manifest)
        assert "api.example.com" in domains

    def test_update_firewall_adds_domain(
        self, fixtures_dir: Path, tmp_path: Path
    ) -> None:
        """Add domain to init-firewall.sh."""
        manifest = load_manifest(fixtures_dir / "full.yml")

        devcontainer = tmp_path / ".devcontainer"
        devcontainer.mkdir()
        firewall_script = devcontainer / "init-firewall.sh"
        firewall_script.write_text(
            """#!/bin/bash
# Firewall initialization
ALLOWED_DOMAINS=(
    "existing.example.com"
)
"""
        )

        result = update_firewall(manifest, tmp_path)
        assert result.success

        content = firewall_script.read_text()
        assert "api.example.com" in content
        assert "existing.example.com" in content

    def test_no_firewall_script(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """Skip silently when no init-firewall.sh."""
        manifest = load_manifest(fixtures_dir / "full.yml")

        result = update_firewall(manifest, tmp_path)
        assert not result.success
        assert "not found" in result.message.lower()

    def test_no_http_servers(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """No changes when no HTTP MCP servers."""
        manifest = load_manifest(fixtures_dir / "minimal.yml")

        devcontainer = tmp_path / ".devcontainer"
        devcontainer.mkdir()
        (devcontainer / "init-firewall.sh").write_text("#!/bin/bash\n")

        result = update_firewall(manifest, tmp_path)
        assert result.success
        assert result.domains_added == 0
