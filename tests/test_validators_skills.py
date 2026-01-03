"""Tests for skills validation."""

from pathlib import Path

from agent_container_pack.manifest import load_manifest
from agent_container_pack.validators.skills import validate_skills


class TestSkillsValidation:
    """Test skills validation."""

    def test_valid_skill(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """Valid skill with correct frontmatter."""
        manifest = load_manifest(fixtures_dir / "full.yml")

        skills_dir = tmp_path / ".claude" / "skills" / "python-dev"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text(
            """---
name: python-dev
description: Python development best practices
---

## Purpose
...
"""
        )

        errors = validate_skills(manifest, tmp_path)
        assert len(errors) == 0

    def test_missing_skill_file(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """Error when SKILL.md is missing."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        skills_dir = tmp_path / ".claude" / "skills" / "python-dev"
        skills_dir.mkdir(parents=True)
        # No SKILL.md file

        errors = validate_skills(manifest, tmp_path)
        assert len(errors) == 1
        assert "SKILL.md not found" in errors[0].message

    def test_missing_frontmatter(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """Error when frontmatter is missing."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        skills_dir = tmp_path / ".claude" / "skills" / "python-dev"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("# Python Dev\n\nNo frontmatter here.")

        errors = validate_skills(manifest, tmp_path)
        assert len(errors) == 1
        assert "frontmatter" in errors[0].message.lower()

    def test_missing_name_field(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """Error when name field is missing."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        skills_dir = tmp_path / ".claude" / "skills" / "python-dev"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text(
            """---
description: Python development best practices
---

## Purpose
"""
        )

        errors = validate_skills(manifest, tmp_path)
        assert len(errors) == 1
        assert "name" in errors[0].message
