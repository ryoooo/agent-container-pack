"""Tests for template download."""

from pathlib import Path
from unittest.mock import patch, MagicMock

from agent_container_pack.init.template import parse_template_source, download_template


class TestTemplateSource:
    """Test template source parsing."""

    def test_parse_github_basic(self) -> None:
        """Parse basic GitHub source."""
        source = parse_template_source("github:owner/repo")
        assert source.owner == "owner"
        assert source.repo == "repo"
        assert source.branch is None
        assert source.subdir is None

    def test_parse_github_with_branch(self) -> None:
        """Parse GitHub source with branch."""
        source = parse_template_source("github:owner/repo@main")
        assert source.owner == "owner"
        assert source.repo == "repo"
        assert source.branch == "main"

    def test_parse_github_with_subdir(self) -> None:
        """Parse GitHub source with subdirectory."""
        source = parse_template_source("github:owner/repo#templates/python")
        assert source.owner == "owner"
        assert source.repo == "repo"
        assert source.subdir == "templates/python"

    def test_parse_github_full(self) -> None:
        """Parse full GitHub source."""
        source = parse_template_source("github:owner/repo@v1.0#templates")
        assert source.owner == "owner"
        assert source.repo == "repo"
        assert source.branch == "v1.0"
        assert source.subdir == "templates"

    def test_invalid_format(self) -> None:
        """Error on invalid format."""
        import pytest

        with pytest.raises(ValueError, match="Invalid template source"):
            parse_template_source("invalid")


class TestDownloadTemplate:
    """Test template download."""

    def test_download_creates_files(self, tmp_path: Path) -> None:
        """Download template creates expected files."""
        # Mock httpx response
        with patch("agent_container_pack.init.template.httpx") as mock_httpx:
            import zipfile
            import io

            # Create mock zip file with .devcontainer
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                zf.writestr("repo-main/.devcontainer/devcontainer.json", "{}")
                zf.writestr("repo-main/.devcontainer/Dockerfile", "FROM ubuntu")

            mock_response = MagicMock()
            mock_response.content = zip_buffer.getvalue()
            mock_response.raise_for_status = MagicMock()
            mock_httpx.get.return_value = mock_response

            source = parse_template_source("github:owner/repo")
            download_template(source, tmp_path)

            assert (tmp_path / ".devcontainer" / "devcontainer.json").exists()
            assert (tmp_path / ".devcontainer" / "Dockerfile").exists()


class TestGenerateSkeleton:
    """Test skeleton generation."""

    def test_generate_skeleton_basic(self, tmp_path: Path) -> None:
        """Generate basic skeleton without stack."""
        from agent_container_pack.init.template import generate_skeleton

        generate_skeleton(tmp_path)

        assert (tmp_path / "agentpack.yml").exists()
        content = (tmp_path / "agentpack.yml").read_text()
        assert 'version: "1"' in content
        assert "my-project" in content

    def test_generate_skeleton_with_stack(self, tmp_path: Path) -> None:
        """Generate skeleton with specific stack."""
        from agent_container_pack.init.template import generate_skeleton

        generate_skeleton(tmp_path, stack="python")

        content = (tmp_path / "agentpack.yml").read_text()
        assert "stack: python" in content
        assert "stacks:" in content
        assert "python:" in content
