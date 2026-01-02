"""Template download and extraction."""

import io
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

import httpx

GITHUB_PATTERN = re.compile(
    r"^github:(?P<owner>[^/]+)/(?P<repo>[^@#]+)(?:@(?P<branch>[^#]+))?(?:#(?P<subdir>.+))?$"
)


@dataclass
class TemplateSource:
    """Parsed template source."""

    owner: str
    repo: str
    branch: str | None = None
    subdir: str | None = None


def parse_template_source(source: str) -> TemplateSource:
    """Parse template source string.

    Args:
        source: Template source (e.g., "github:owner/repo@branch#subdir")

    Returns:
        Parsed template source.

    Raises:
        ValueError: If source format is invalid.
    """
    match = GITHUB_PATTERN.match(source)
    if not match:
        raise ValueError(f"Invalid template source: {source}")

    return TemplateSource(
        owner=match.group("owner"),
        repo=match.group("repo"),
        branch=match.group("branch"),
        subdir=match.group("subdir"),
    )


def download_template(source: TemplateSource, target_dir: Path) -> None:
    """Download template from GitHub.

    Args:
        source: Parsed template source.
        target_dir: Directory to extract template to.
    """
    branch = source.branch or "main"
    url = f"https://github.com/{source.owner}/{source.repo}/archive/refs/heads/{branch}.zip"

    response = httpx.get(url, follow_redirects=True)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        # Find the root directory in zip (usually repo-branch)
        root_prefix = None
        for name in zf.namelist():
            parts = name.split("/")
            if len(parts) > 1:
                root_prefix = parts[0]
                break

        if not root_prefix:
            raise ValueError("Empty or invalid zip archive")

        # Determine source directory in zip
        if source.subdir:
            zip_prefix = f"{root_prefix}/{source.subdir}/"
        else:
            zip_prefix = f"{root_prefix}/"

        # Extract only .devcontainer contents
        devcontainer_prefix = f"{zip_prefix}.devcontainer/"
        target_devcontainer = target_dir / ".devcontainer"
        target_devcontainer.mkdir(parents=True, exist_ok=True)

        for name in zf.namelist():
            if name.startswith(devcontainer_prefix) and not name.endswith("/"):
                # Get relative path within .devcontainer
                rel_path = name[len(devcontainer_prefix) :]
                if rel_path:
                    target_file = target_devcontainer / rel_path
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    target_file.write_bytes(zf.read(name))


def generate_skeleton(target_dir: Path, stack: str | None = None) -> None:
    """Generate agentpack.yml skeleton.

    Args:
        target_dir: Directory to create skeleton in.
        stack: Optional stack to include.
    """
    skeleton = """version: "1"

project:
  name: "my-project"
  description: "Project description"

docs:
  mode: single-stack
  defaultStack: auto
"""

    if stack:
        skeleton += f"""
stack: {stack}

stacks:
  {stack}:
    detect:
      any: []
    deps: ""
    lint: ""
    typecheck: ""
    test: ""
    run: ""
"""

    (target_dir / "agentpack.yml").write_text(skeleton)
