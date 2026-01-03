"""Agentpack CLI."""

from pathlib import Path
import sys

import cyclopts
import httpx

from agentpack.devcontainer import update_firewall
from agentpack.generators import (
    generate_claude_md,
    generate_codex_config,
    generate_settings_json,
)
from agentpack.init import download_template, generate_skeleton, parse_template_source
from agentpack.manifest import load_manifest, ManifestNotFoundError, ManifestParseError
from agentpack.validators import validate_env_vars, validate_skills

app = cyclopts.App(
    name="agentpack",
    help="Generate CLAUDE.md/AGENTS.md from agentpack.yml",
)


@app.default
def main() -> None:
    """Show help by default."""
    app(["--help"])


@app.command
def generate(
    *,
    write: bool = False,
    directory: Path = Path("."),
) -> None:
    """Generate configuration files from agentpack.yml.

    Args:
        write: Write files to disk (default: dry-run).
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

        # Update firewall
        firewall_result = update_firewall(manifest, directory)
        if firewall_result.success and firewall_result.domains_added > 0:
            print(
                f"  - Updated init-firewall.sh ({firewall_result.domains_added} domains added)"
            )
        elif (
            not firewall_result.success
            and "not found" not in firewall_result.message.lower()
        ):
            print(f"Warning: {firewall_result.message}", file=sys.stderr)

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


@app.command
def init(
    directory: Path = Path("."),
    *,
    template: str = "github:ryoooo/agentpack-template-default",
    stack: str = "python",
    force: bool = False,
) -> None:
    """Initialize a new agentpack project.

    Args:
        directory: Target directory.
        template: Template source.
        stack: Stack to use.
        force: Overwrite existing files.
    """
    directory = directory.resolve()

    # Check for existing files
    if not force:
        if (directory / "agentpack.yml").exists():
            print(
                "Error: agentpack.yml already exists. Use --force to overwrite.",
                file=sys.stderr,
            )
            sys.exit(1)
        if (directory / ".devcontainer").exists():
            print(
                "Error: .devcontainer already exists. Use --force to overwrite.",
                file=sys.stderr,
            )
            sys.exit(1)

    directory.mkdir(parents=True, exist_ok=True)

    try:
        source = parse_template_source(template)
        print(f"Downloading template from {template}...")
        download_template(source, directory)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        print(f"Error downloading template: {e}", file=sys.stderr)
        sys.exit(1)

    generate_skeleton(directory, stack)

    print(f"Initialized agentpack project in {directory}")
    print("  - .devcontainer/")
    print("  - agentpack.yml")


if __name__ == "__main__":
    app()
