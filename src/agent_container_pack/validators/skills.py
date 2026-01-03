"""Validate skills configuration."""

import re
from dataclasses import dataclass
from pathlib import Path

from agent_container_pack.manifest.schema import Manifest

FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
NAME_PATTERN = re.compile(r"^name:\s*(.+)$", re.MULTILINE)
DESCRIPTION_PATTERN = re.compile(r"^description:\s*(.+)$", re.MULTILINE)


@dataclass
class SkillsValidationError:
    """Error about skills configuration."""

    skill_id: str
    message: str


def _get_required_skills(manifest: Manifest) -> set[str]:
    """Get all required skill IDs from manifest.

    Args:
        manifest: Validated manifest.

    Returns:
        Set of required skill IDs.
    """
    skills: set[str] = set()

    for stack_config in manifest.stacks.values():
        if "required" in stack_config.skills:
            skills.update(stack_config.skills["required"])

    return skills


def _validate_skill(skill_id: str, skill_path: Path) -> list[SkillsValidationError]:
    """Validate a single skill.

    Args:
        skill_id: Skill identifier.
        skill_path: Path to skill directory.

    Returns:
        List of validation errors.
    """
    errors: list[SkillsValidationError] = []

    skill_file = skill_path / "SKILL.md"
    if not skill_file.exists():
        errors.append(
            SkillsValidationError(
                skill_id=skill_id,
                message=f"SKILL.md not found at {skill_file}",
            )
        )
        return errors

    content = skill_file.read_text()

    # Check frontmatter
    frontmatter_match = FRONTMATTER_PATTERN.match(content)
    if not frontmatter_match:
        errors.append(
            SkillsValidationError(
                skill_id=skill_id,
                message="SKILL.md is missing frontmatter (---...---)",
            )
        )
        return errors

    frontmatter = frontmatter_match.group(1)

    # Check name field
    name_match = NAME_PATTERN.search(frontmatter)
    if not name_match:
        errors.append(
            SkillsValidationError(
                skill_id=skill_id,
                message="SKILL.md frontmatter is missing 'name' field",
            )
        )

    # Check description field
    description_match = DESCRIPTION_PATTERN.search(frontmatter)
    if not description_match:
        errors.append(
            SkillsValidationError(
                skill_id=skill_id,
                message="SKILL.md frontmatter is missing 'description' field",
            )
        )

    return errors


def validate_skills(
    manifest: Manifest, project_dir: Path
) -> list[SkillsValidationError]:
    """Validate all required skills.

    Args:
        manifest: Validated manifest.
        project_dir: Project directory.

    Returns:
        List of validation errors.
    """
    errors: list[SkillsValidationError] = []

    skills_root = project_dir / manifest.skills.root
    required_skills = _get_required_skills(manifest)

    for skill_id in required_skills:
        skill_path = skills_root / skill_id
        errors.extend(_validate_skill(skill_id, skill_path))

    return errors
