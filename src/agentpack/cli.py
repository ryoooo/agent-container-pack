"""Agentpack CLI."""

from pathlib import Path
import sys

import cyclopts

from agentpack.generators import generate_claude_md, generate_codex_config, generate_settings_json
from agentpack.manifest import load_manifest, ManifestNotFoundError, ManifestParseError
from agentpack.validators import validate_env_vars, validate_skills

app = cyclopts.App(
    name="agentpack",
    help="Generate CLAUDE.md/AGENTS.md from agentpack.yml",
)


@app.default
def main() -> None:
    """Show help by default."""
    print(app.help_format())


@app.command
def generate(
    *,
    write: bool = False,
    stack: str | None = None,
    directory: Path = Path("."),
) -> None:
    """Generate configuration files from agentpack.yml.

    Args:
        write: Write files to disk (default: dry-run).
        stack: Stack to use (default: auto-detect).
        directory: Project directory.
    """
    try:
        manifest = load_manifest(directory)
    except ManifestNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ManifestParseError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Generate outputs
    claude_md = generate_claude_md(manifest)
    agents_md = claude_md  # Same content
    settings_json = generate_settings_json(manifest)
    codex_config = generate_codex_config(manifest)

    # Validate
    env_warnings = validate_env_vars(manifest, directory)
    for warning in env_warnings:
        print(f"Warning: {warning.message}", file=sys.stderr)

    skills_errors = validate_skills(manifest, directory)
    for error in skills_errors:
        print(f"Warning: [{error.skill_id}] {error.message}", file=sys.stderr)

    if write:
        # Write files
        (directory / "CLAUDE.md").write_text(claude_md)
        (directory / "AGENTS.md").write_text(agents_md)

        claude_dir = directory / ".claude"
        claude_dir.mkdir(exist_ok=True)
        (claude_dir / "settings.json").write_text(settings_json)

        (directory / "codex.config.toml").write_text(codex_config)

        print("Generated:")
        print("  - CLAUDE.md")
        print("  - AGENTS.md")
        print("  - .claude/settings.json")
        print("  - codex.config.toml")
    else:
        # Dry run - show output
        print("=== CLAUDE.md ===")
        print(claude_md)
        print("=== .claude/settings.json ===")
        print(settings_json)
        print("=== codex.config.toml ===")
        print(codex_config)
        print("\nUse --write to create files.")


if __name__ == "__main__":
    app()
