# Agentpack v0.1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a CLI tool that generates CLAUDE.md/AGENTS.md and MCP configurations from agentpack.yml as Single Source of Truth.

**Architecture:** Manifest-driven generation using Pydantic for validation and cyclopts for CLI. Generators produce deterministic output from validated manifest data. TDD with snapshot tests for outputs.

**Tech Stack:** Python 3.13+, cyclopts (CLI), pydantic (validation), pyyaml (YAML parsing), httpx (HTTP), pytest + syrupy (testing)

---

## Prerequisites

Before starting implementation, ensure dependencies are installed:

```bash
uv add cyclopts pydantic pyyaml httpx
uv add --dev pytest syrupy pytest-asyncio
```

---

## Task 1: Project Skeleton Setup

**Files:**
- Create: `src/agentpack/__init__.py`
- Create: `src/agentpack/cli.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Modify: `pyproject.toml`

**Step 1: Update pyproject.toml for src layout**

Edit `pyproject.toml`:

```toml
[project]
name = "agentpack"
version = "0.1.0"
description = "CLI tool for generating CLAUDE.md/AGENTS.md from agentpack.yml"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "cyclopts",
    "pydantic",
    "pyyaml",
    "httpx",
]

[project.scripts]
agentpack = "agentpack.cli:app"

[dependency-groups]
dev = [
    "pre-commit",
    "pytest",
    "pytest-asyncio",
    "ruff",
    "syrupy",
    "ty",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

**Step 2: Create package init**

Create `src/agentpack/__init__.py`:

```python
"""Agentpack - Generate CLAUDE.md/AGENTS.md from agentpack.yml."""

__version__ = "0.1.0"
```

**Step 3: Create minimal CLI entry point**

Create `src/agentpack/cli.py`:

```python
"""Agentpack CLI."""

import cyclopts

app = cyclopts.App(
    name="agentpack",
    help="Generate CLAUDE.md/AGENTS.md from agentpack.yml",
)


@app.default
def main() -> None:
    """Show help by default."""
    print(app.help_format())


if __name__ == "__main__":
    app()
```

**Step 4: Create test infrastructure**

Create `tests/__init__.py`:

```python
"""Agentpack tests."""
```

Create `tests/conftest.py`:

```python
"""Pytest configuration and fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    return tmp_path
```

**Step 5: Create fixtures directory**

```bash
mkdir -p tests/fixtures
```

**Step 6: Sync dependencies and verify CLI works**

Run: `uv sync && uv run agentpack --help`
Expected: Help text displayed

**Step 7: Commit**

```bash
git add -A
git commit -m "feat: add project skeleton with cyclopts CLI

- Configure src layout in pyproject.toml
- Add cyclopts CLI entry point
- Set up pytest with fixtures"
```

---

## Task 2: Manifest Schema (Pydantic Models)

**Files:**
- Create: `src/agentpack/manifest/__init__.py`
- Create: `src/agentpack/manifest/schema.py`
- Create: `tests/test_manifest_schema.py`

**Step 1: Write failing test for minimal manifest**

Create `tests/test_manifest_schema.py`:

```python
"""Tests for manifest schema."""

import pytest
from pydantic import ValidationError

from agentpack.manifest.schema import Manifest


class TestManifestValidation:
    """Test manifest validation."""

    def test_minimal_manifest(self) -> None:
        """Minimal valid manifest with required fields."""
        data = {
            "version": "1",
            "project": {
                "name": "test-project",
                "description": "Test project",
            },
        }
        manifest = Manifest.model_validate(data)
        assert manifest.version == "1"
        assert manifest.project.name == "test-project"

    def test_version_required(self) -> None:
        """Version field is required."""
        data = {
            "project": {
                "name": "test-project",
                "description": "Test project",
            },
        }
        with pytest.raises(ValidationError) as exc_info:
            Manifest.model_validate(data)
        assert "version" in str(exc_info.value)

    def test_project_required(self) -> None:
        """Project field is required."""
        data = {"version": "1"}
        with pytest.raises(ValidationError) as exc_info:
            Manifest.model_validate(data)
        assert "project" in str(exc_info.value)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_manifest_schema.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Create manifest package**

Create `src/agentpack/manifest/__init__.py`:

```python
"""Manifest parsing and validation."""

from agentpack.manifest.schema import Manifest

__all__ = ["Manifest"]
```

**Step 4: Write minimal schema implementation**

Create `src/agentpack/manifest/schema.py`:

```python
"""Pydantic models for agentpack.yml manifest."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    """Project configuration."""

    name: str
    description: str


class DocsConfig(BaseModel):
    """Documentation generation configuration."""

    mode: Literal["single-stack", "multi-stack"] = "single-stack"
    defaultStack: str = "auto"
    maxLines: int = 250


class StackDetect(BaseModel):
    """Stack detection configuration."""

    any: list[str] = Field(default_factory=list)


class StackConfig(BaseModel):
    """Stack-specific configuration."""

    detect: StackDetect = Field(default_factory=StackDetect)
    deps: str | None = None
    lint: str | None = None
    typecheck: str | None = None
    test: str | None = None
    run: str | None = None
    skills: dict[str, list[str]] = Field(default_factory=dict)


class SkillsConfig(BaseModel):
    """Skills configuration."""

    root: str = ".claude/skills"


class MCPServerStdio(BaseModel):
    """STDIO MCP server configuration."""

    transport: Literal["stdio"] = "stdio"
    command: list[str]
    env: dict[str, str] = Field(default_factory=dict)
    cwd: str | None = None


class MCPServerHTTP(BaseModel):
    """HTTP MCP server configuration."""

    transport: Literal["http"]
    url: str
    env: dict[str, str] = Field(default_factory=dict)


MCPServer = MCPServerStdio | MCPServerHTTP


class MCPConfig(BaseModel):
    """MCP configuration."""

    servers: dict[str, MCPServer] = Field(default_factory=dict)


class WorkflowConfig(BaseModel):
    """Workflow configuration."""

    name: str
    steps: list[str]


class SafetyConfig(BaseModel):
    """Safety configuration."""

    preset: Literal["default", "none"] = "default"
    custom: list[str] = Field(default_factory=list)


class Manifest(BaseModel):
    """Root manifest model for agentpack.yml."""

    version: Literal["1"]
    project: ProjectConfig
    docs: DocsConfig = Field(default_factory=DocsConfig)
    stack: str | None = None
    stacks: dict[str, StackConfig] = Field(default_factory=dict)
    skills: SkillsConfig = Field(default_factory=SkillsConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    workflows: list[WorkflowConfig] = Field(default_factory=list)
    pre_commit: list[str] = Field(default_factory=list)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    custom_content: str | None = None
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_manifest_schema.py -v`
Expected: PASS (3 tests)

**Step 6: Add more comprehensive tests**

Add to `tests/test_manifest_schema.py`:

```python
    def test_full_manifest(self) -> None:
        """Full manifest with all fields."""
        data = {
            "version": "1",
            "project": {
                "name": "my-app",
                "description": "My application",
            },
            "docs": {
                "mode": "single-stack",
                "defaultStack": "auto",
                "maxLines": 250,
            },
            "stack": "python",
            "stacks": {
                "python": {
                    "detect": {"any": ["pyproject.toml", "requirements.txt"]},
                    "deps": "uv sync",
                    "lint": "uv run ruff check .",
                    "typecheck": "uv run ty check",
                    "test": "uv run pytest",
                    "run": "uv run python main.py",
                    "skills": {"required": ["python-dev"]},
                },
            },
            "mcp": {
                "servers": {
                    "memory": {
                        "transport": "stdio",
                        "command": ["npx", "@anthropic/mcp-memory"],
                        "env": {"MEMORY_PATH": "${workspaceFolder}/.memory"},
                    },
                    "external-api": {
                        "transport": "http",
                        "url": "https://api.example.com/mcp",
                        "env": {"API_KEY": "${env:EXAMPLE_API_KEY}"},
                    },
                },
            },
            "workflows": [
                {
                    "name": "開発フロー",
                    "steps": [
                        "uv run ruff format . && uv run ruff check .",
                        "uv run pytest",
                    ],
                },
            ],
            "pre_commit": ["prettier", "ruff", "ty"],
            "safety": {
                "preset": "default",
                "custom": ["本番DBに直接接続しない"],
            },
            "custom_content": "## Quick Start\n\n```bash\npython main.py\n```",
        }
        manifest = Manifest.model_validate(data)
        assert manifest.stack == "python"
        assert manifest.stacks["python"].deps == "uv sync"
        assert len(manifest.mcp.servers) == 2
        assert manifest.mcp.servers["memory"].transport == "stdio"
        assert manifest.mcp.servers["external-api"].transport == "http"

    def test_invalid_docs_mode(self) -> None:
        """Invalid docs mode should fail validation."""
        data = {
            "version": "1",
            "project": {"name": "test", "description": "test"},
            "docs": {"mode": "invalid"},
        }
        with pytest.raises(ValidationError) as exc_info:
            Manifest.model_validate(data)
        assert "mode" in str(exc_info.value)

    def test_mcp_server_requires_transport(self) -> None:
        """MCP server must have valid transport."""
        data = {
            "version": "1",
            "project": {"name": "test", "description": "test"},
            "mcp": {
                "servers": {
                    "invalid": {"command": ["echo", "test"]},
                },
            },
        }
        # stdio is default, so this should work
        manifest = Manifest.model_validate(data)
        assert manifest.mcp.servers["invalid"].transport == "stdio"
```

**Step 7: Run all tests**

Run: `uv run pytest tests/test_manifest_schema.py -v`
Expected: PASS (6 tests)

**Step 8: Commit**

```bash
git add -A
git commit -m "feat: add manifest schema with Pydantic models

- Define all manifest field models
- Support stdio and http MCP server types
- Validate required fields and enums"
```

---

## Task 3: Manifest Loader (YAML → Pydantic)

**Files:**
- Create: `src/agentpack/manifest/loader.py`
- Create: `tests/fixtures/minimal.yml`
- Create: `tests/fixtures/full.yml`
- Create: `tests/test_manifest_loader.py`
- Modify: `src/agentpack/manifest/__init__.py`

**Step 1: Create test fixtures**

Create `tests/fixtures/minimal.yml`:

```yaml
version: "1"

project:
  name: "minimal-project"
  description: "A minimal test project"
```

Create `tests/fixtures/full.yml`:

```yaml
version: "1"

project:
  name: "full-project"
  description: "A full featured test project"

docs:
  mode: single-stack
  defaultStack: auto
  maxLines: 250

stack: python

stacks:
  python:
    detect:
      any: ["pyproject.toml", "requirements.txt"]
    deps: "uv sync"
    lint: "uv run ruff check ."
    typecheck: "uv run ty check"
    test: "uv run pytest"
    run: "uv run python main.py"
    skills:
      required: ["python-dev"]

skills:
  root: ".claude/skills"

mcp:
  servers:
    memory:
      transport: stdio
      command: ["npx", "@anthropic/mcp-memory"]
      env:
        MEMORY_PATH: "${workspaceFolder}/.memory"
    external-api:
      transport: http
      url: "https://api.example.com/mcp"
      env:
        API_KEY: "${env:EXAMPLE_API_KEY}"

workflows:
  - name: "Development Flow"
    steps:
      - "uv run ruff format . && uv run ruff check ."
      - "uv run pytest"

pre_commit: ["prettier", "ruff", "ty"]

safety:
  preset: default
  custom:
    - "Do not connect to production DB directly"

custom_content: |
  ## Quick Start

  ```bash
  python main.py
  ```
```

**Step 2: Write failing test for loader**

Create `tests/test_manifest_loader.py`:

```python
"""Tests for manifest loader."""

from pathlib import Path

import pytest

from agentpack.manifest import Manifest
from agentpack.manifest.loader import load_manifest, ManifestNotFoundError


class TestLoadManifest:
    """Test manifest loading from YAML files."""

    def test_load_minimal(self, fixtures_dir: Path) -> None:
        """Load minimal manifest."""
        manifest = load_manifest(fixtures_dir / "minimal.yml")
        assert isinstance(manifest, Manifest)
        assert manifest.project.name == "minimal-project"

    def test_load_full(self, fixtures_dir: Path) -> None:
        """Load full manifest with all fields."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        assert manifest.project.name == "full-project"
        assert manifest.stack == "python"
        assert "memory" in manifest.mcp.servers
        assert manifest.mcp.servers["memory"].transport == "stdio"

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Raise error when file not found."""
        with pytest.raises(ManifestNotFoundError):
            load_manifest(tmp_path / "nonexistent.yml")

    def test_load_from_directory(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """Load agentpack.yml from directory."""
        import shutil

        shutil.copy(fixtures_dir / "minimal.yml", tmp_path / "agentpack.yml")
        manifest = load_manifest(tmp_path)
        assert manifest.project.name == "minimal-project"
```

**Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_manifest_loader.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 4: Implement loader**

Create `src/agentpack/manifest/loader.py`:

```python
"""Load and parse agentpack.yml manifest files."""

from pathlib import Path

import yaml

from agentpack.manifest.schema import Manifest


class ManifestError(Exception):
    """Base exception for manifest errors."""


class ManifestNotFoundError(ManifestError):
    """Manifest file not found."""


class ManifestParseError(ManifestError):
    """Failed to parse manifest file."""


def load_manifest(path: Path | str) -> Manifest:
    """Load manifest from YAML file or directory.

    Args:
        path: Path to agentpack.yml or directory containing it.

    Returns:
        Validated Manifest object.

    Raises:
        ManifestNotFoundError: If manifest file not found.
        ManifestParseError: If manifest is invalid.
    """
    path = Path(path)

    if path.is_dir():
        path = path / "agentpack.yml"

    if not path.exists():
        raise ManifestNotFoundError(f"Manifest not found: {path}")

    try:
        with path.open() as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ManifestParseError(f"Failed to parse YAML: {e}") from e

    try:
        return Manifest.model_validate(data)
    except Exception as e:
        raise ManifestParseError(f"Invalid manifest: {e}") from e
```

**Step 5: Update package exports**

Update `src/agentpack/manifest/__init__.py`:

```python
"""Manifest parsing and validation."""

from agentpack.manifest.loader import (
    ManifestError,
    ManifestNotFoundError,
    ManifestParseError,
    load_manifest,
)
from agentpack.manifest.schema import Manifest

__all__ = [
    "Manifest",
    "ManifestError",
    "ManifestNotFoundError",
    "ManifestParseError",
    "load_manifest",
]
```

**Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_manifest_loader.py -v`
Expected: PASS (4 tests)

**Step 7: Commit**

```bash
git add -A
git commit -m "feat: add manifest loader for YAML files

- Load from file path or directory
- Custom exceptions for not found and parse errors
- Create test fixtures for minimal and full manifests"
```

---

## Task 4: Markdown Generator (CLAUDE.md / AGENTS.md)

**Files:**
- Create: `src/agentpack/generators/__init__.py`
- Create: `src/agentpack/generators/markdown.py`
- Create: `tests/test_generators_markdown.py`
- Create: `tests/snapshots/` directory

**Step 1: Write failing snapshot test**

Create `tests/test_generators_markdown.py`:

```python
"""Tests for markdown generator."""

from pathlib import Path

from syrupy.assertion import SnapshotAssertion

from agentpack.generators.markdown import generate_claude_md
from agentpack.manifest import load_manifest


class TestMarkdownGenerator:
    """Test CLAUDE.md/AGENTS.md generation."""

    def test_generate_minimal(
        self,
        fixtures_dir: Path,
        snapshot: SnapshotAssertion,
    ) -> None:
        """Generate markdown from minimal manifest."""
        manifest = load_manifest(fixtures_dir / "minimal.yml")
        result = generate_claude_md(manifest)
        assert result == snapshot

    def test_generate_full(
        self,
        fixtures_dir: Path,
        snapshot: SnapshotAssertion,
    ) -> None:
        """Generate markdown from full manifest."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        result = generate_claude_md(manifest)
        assert result == snapshot
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_generators_markdown.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Create generators package**

Create `src/agentpack/generators/__init__.py`:

```python
"""Output generators for agentpack."""

from agentpack.generators.markdown import generate_claude_md

__all__ = ["generate_claude_md"]
```

**Step 4: Implement markdown generator**

Create `src/agentpack/generators/markdown.py`:

```python
"""Generate CLAUDE.md / AGENTS.md from manifest."""

from agentpack.manifest.schema import Manifest, SafetyConfig

SAFETY_PRESET_DEFAULT = [
    "secrets禁止（API_KEY等を直書きしない）",
    "破壊操作は段階的に: dry-run → diff → apply",
]


def _generate_safety_section(safety: SafetyConfig) -> str:
    """Generate safety section."""
    lines: list[str] = []

    if safety.preset == "default":
        for rule in SAFETY_PRESET_DEFAULT:
            lines.append(f"- {rule}")

    for rule in safety.custom:
        lines.append(f"- {rule}")

    if not lines:
        return ""

    return "## Safety\n\n" + "\n".join(lines) + "\n"


def generate_claude_md(manifest: Manifest) -> str:
    """Generate CLAUDE.md content from manifest.

    Args:
        manifest: Validated manifest object.

    Returns:
        Generated markdown content.
    """
    sections: list[str] = []

    # Header
    sections.append(f"# {manifest.project.name}\n")
    sections.append(f"{manifest.project.description}\n")

    # Commands section (if stack is specified)
    stack_config = None
    if manifest.stack and manifest.stack in manifest.stacks:
        stack_config = manifest.stacks[manifest.stack]
    elif manifest.stacks:
        # Use first available stack
        stack_config = next(iter(manifest.stacks.values()))

    if stack_config:
        commands: list[str] = []
        if stack_config.deps:
            commands.append(f"- **deps**: `{stack_config.deps}`")
        if stack_config.lint:
            commands.append(f"- **lint**: `{stack_config.lint}`")
        if stack_config.typecheck:
            commands.append(f"- **typecheck**: `{stack_config.typecheck}`")
        if stack_config.test:
            commands.append(f"- **test**: `{stack_config.test}`")
        if stack_config.run:
            commands.append(f"- **run**: `{stack_config.run}`")

        if commands:
            sections.append("## Commands\n")
            sections.append("\n".join(commands) + "\n")

    # Workflows section
    if manifest.workflows:
        sections.append("## Workflows\n")
        for workflow in manifest.workflows:
            sections.append(f"### {workflow.name}\n")
            for i, step in enumerate(workflow.steps, 1):
                sections.append(f"{i}. `{step}`")
            sections.append("")

    # Pre-commit section
    if manifest.pre_commit:
        sections.append("## Pre-commit\n")
        for tool in manifest.pre_commit:
            sections.append(f"- {tool}")
        sections.append("")

    # Safety section
    safety_section = _generate_safety_section(manifest.safety)
    if safety_section:
        sections.append(safety_section)

    # Custom content
    if manifest.custom_content:
        sections.append(manifest.custom_content.rstrip() + "\n")

    return "\n".join(sections)
```

**Step 5: Run test to update snapshots**

Run: `uv run pytest tests/test_generators_markdown.py -v --snapshot-update`
Expected: PASS (snapshots created)

**Step 6: Review generated snapshots**

Check contents of `tests/snapshots/` to verify output is correct.

**Step 7: Run test without update flag**

Run: `uv run pytest tests/test_generators_markdown.py -v`
Expected: PASS (2 tests)

**Step 8: Commit**

```bash
git add -A
git commit -m "feat: add markdown generator for CLAUDE.md/AGENTS.md

- Generate commands, workflows, pre-commit, safety sections
- Support safety presets and custom rules
- Add snapshot tests for minimal and full manifests"
```

---

## Task 5: Settings Generator (.claude/settings.json)

**Files:**
- Create: `src/agentpack/generators/settings.py`
- Create: `tests/test_generators_settings.py`
- Modify: `src/agentpack/generators/__init__.py`

**Step 1: Write failing snapshot test**

Create `tests/test_generators_settings.py`:

```python
"""Tests for settings.json generator."""

from pathlib import Path

from syrupy.assertion import SnapshotAssertion

from agentpack.generators.settings import generate_settings_json
from agentpack.manifest import load_manifest


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
        manifest = load_manifest(fixtures_dir / "full.yml")
        result = generate_settings_json(manifest)
        assert '"command": "npx"' in result
        assert '"args": ["@anthropic/mcp-memory"]' in result
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_generators_settings.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Implement settings generator**

Create `src/agentpack/generators/settings.py`:

```python
"""Generate .claude/settings.json from manifest."""

import json
from typing import Any

from agentpack.manifest.schema import Manifest, MCPServerStdio


def generate_settings_json(manifest: Manifest) -> str:
    """Generate .claude/settings.json content from manifest.

    Args:
        manifest: Validated manifest object.

    Returns:
        Generated JSON content.
    """
    mcp_servers: dict[str, Any] = {}

    for name, server in manifest.mcp.servers.items():
        if isinstance(server, MCPServerStdio):
            server_config: dict[str, Any] = {
                "command": server.command[0],
                "args": server.command[1:],
            }
            if server.env:
                server_config["env"] = server.env
            if server.cwd:
                server_config["cwd"] = server.cwd
        else:
            # HTTP server - skip for Claude settings (not supported)
            continue

        mcp_servers[name] = server_config

    settings: dict[str, Any] = {}
    if mcp_servers:
        settings["mcpServers"] = mcp_servers

    return json.dumps(settings, indent=2, ensure_ascii=False) + "\n"
```

**Step 4: Update package exports**

Update `src/agentpack/generators/__init__.py`:

```python
"""Output generators for agentpack."""

from agentpack.generators.markdown import generate_claude_md
from agentpack.generators.settings import generate_settings_json

__all__ = ["generate_claude_md", "generate_settings_json"]
```

**Step 5: Run test to update snapshots**

Run: `uv run pytest tests/test_generators_settings.py -v --snapshot-update`
Expected: PASS (snapshots created)

**Step 6: Run test without update flag**

Run: `uv run pytest tests/test_generators_settings.py -v`
Expected: PASS (3 tests)

**Step 7: Commit**

```bash
git add -A
git commit -m "feat: add settings.json generator for MCP servers

- Generate mcpServers with command/args format
- Support env and cwd options
- Skip HTTP servers (not supported by Claude settings)"
```

---

## Task 6: Codex Config Generator (codex.config.toml)

**Files:**
- Create: `src/agentpack/generators/codex_config.py`
- Create: `tests/test_generators_codex.py`
- Modify: `src/agentpack/generators/__init__.py`

**Step 1: Write failing snapshot test**

Create `tests/test_generators_codex.py`:

```python
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
        assert '[mcp_servers.memory]' in result
        assert 'command = "npx"' in result

    def test_http_format(self, fixtures_dir: Path) -> None:
        """HTTP servers have url field."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        result = generate_codex_config(manifest)
        assert '[mcp_servers.external-api]' in result
        assert 'url = "https://api.example.com/mcp"' in result
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_generators_codex.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Implement codex config generator**

Create `src/agentpack/generators/codex_config.py`:

```python
"""Generate codex.config.toml from manifest."""

from agentpack.manifest.schema import Manifest, MCPServerHTTP, MCPServerStdio


def _format_toml_value(value: str | list[str] | dict[str, str]) -> str:
    """Format a value for TOML output."""
    if isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, list):
        items = ", ".join(f'"{item}"' for item in value)
        return f"[{items}]"
    elif isinstance(value, dict):
        items = ", ".join(f'"{k}" = "{v}"' for k, v in value.items())
        return f"{{ {items} }}"
    return str(value)


def generate_codex_config(manifest: Manifest) -> str:
    """Generate codex.config.toml content from manifest.

    Args:
        manifest: Validated manifest object.

    Returns:
        Generated TOML content.
    """
    lines: list[str] = []

    for name, server in manifest.mcp.servers.items():
        lines.append(f"[mcp_servers.{name}]")

        if isinstance(server, MCPServerStdio):
            lines.append(f'command = "{server.command[0]}"')
            if len(server.command) > 1:
                lines.append(f"args = {_format_toml_value(server.command[1:])}")
            if server.env:
                lines.append(f"env = {_format_toml_value(server.env)}")
            if server.cwd:
                lines.append(f'cwd = "{server.cwd}"')
        elif isinstance(server, MCPServerHTTP):
            lines.append(f'url = "{server.url}"')

        lines.append("")

    return "\n".join(lines)
```

**Step 4: Update package exports**

Update `src/agentpack/generators/__init__.py`:

```python
"""Output generators for agentpack."""

from agentpack.generators.codex_config import generate_codex_config
from agentpack.generators.markdown import generate_claude_md
from agentpack.generators.settings import generate_settings_json

__all__ = ["generate_claude_md", "generate_codex_config", "generate_settings_json"]
```

**Step 5: Run test to update snapshots**

Run: `uv run pytest tests/test_generators_codex.py -v --snapshot-update`
Expected: PASS (snapshots created)

**Step 6: Run test without update flag**

Run: `uv run pytest tests/test_generators_codex.py -v`
Expected: PASS (4 tests)

**Step 7: Commit**

```bash
git add -A
git commit -m "feat: add codex.config.toml generator

- Support both STDIO and HTTP MCP servers
- Generate TOML format with proper value escaping"
```

---

## Task 7: Stack Detection

**Files:**
- Create: `src/agentpack/stack/__init__.py`
- Create: `src/agentpack/stack/detector.py`
- Create: `tests/test_stack_detector.py`

**Step 1: Write failing test**

Create `tests/test_stack_detector.py`:

```python
"""Tests for stack detection."""

from pathlib import Path

import pytest

from agentpack.manifest import load_manifest
from agentpack.stack.detector import detect_stack, AmbiguousStackError, NoStackDetectedError


class TestStackDetection:
    """Test stack detection from project files."""

    def test_detect_python_pyproject(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """Detect Python stack from pyproject.toml."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        (tmp_path / "pyproject.toml").touch()

        result = detect_stack(manifest, tmp_path)
        assert result == "python"

    def test_detect_python_requirements(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """Detect Python stack from requirements.txt."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        (tmp_path / "requirements.txt").touch()

        result = detect_stack(manifest, tmp_path)
        assert result == "python"

    def test_no_stack_detected(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """Error when no stack files found."""
        manifest = load_manifest(fixtures_dir / "full.yml")

        with pytest.raises(NoStackDetectedError):
            detect_stack(manifest, tmp_path)

    def test_explicit_stack_overrides_detection(
        self, fixtures_dir: Path, tmp_path: Path
    ) -> None:
        """Explicit stack in manifest overrides detection."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        # manifest.stack is "python", so detection is skipped
        result = detect_stack(manifest, tmp_path, use_manifest_stack=True)
        assert result == "python"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_stack_detector.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Create stack package**

Create `src/agentpack/stack/__init__.py`:

```python
"""Stack detection and configuration."""

from agentpack.stack.detector import (
    AmbiguousStackError,
    NoStackDetectedError,
    StackError,
    detect_stack,
)

__all__ = [
    "AmbiguousStackError",
    "NoStackDetectedError",
    "StackError",
    "detect_stack",
]
```

**Step 4: Implement detector**

Create `src/agentpack/stack/detector.py`:

```python
"""Detect stack from project files."""

from pathlib import Path

from agentpack.manifest.schema import Manifest


class StackError(Exception):
    """Base exception for stack errors."""


class NoStackDetectedError(StackError):
    """No stack could be detected."""


class AmbiguousStackError(StackError):
    """Multiple stacks detected, ambiguous selection."""


def detect_stack(
    manifest: Manifest,
    project_dir: Path,
    *,
    use_manifest_stack: bool = False,
) -> str:
    """Detect stack from project files.

    Args:
        manifest: Validated manifest with stack definitions.
        project_dir: Project directory to scan.
        use_manifest_stack: If True and manifest.stack is set, use it directly.

    Returns:
        Detected stack ID.

    Raises:
        NoStackDetectedError: If no stack files found.
        AmbiguousStackError: If multiple stacks detected in single-stack mode.
    """
    # Use explicit stack if specified
    if use_manifest_stack and manifest.stack:
        return manifest.stack

    detected: list[str] = []

    for stack_id, stack_config in manifest.stacks.items():
        for pattern in stack_config.detect.any:
            if (project_dir / pattern).exists():
                detected.append(stack_id)
                break

    if not detected:
        raise NoStackDetectedError(
            f"No stack detected in {project_dir}. "
            f"Expected one of: {list(manifest.stacks.keys())}"
        )

    if len(detected) > 1 and manifest.docs.mode == "single-stack":
        raise AmbiguousStackError(
            f"Multiple stacks detected: {detected}. "
            f"Use --stack to specify one, or set docs.mode to multi-stack."
        )

    return detected[0]
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_stack_detector.py -v`
Expected: PASS (4 tests)

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: add stack detection from project files

- Detect stack based on detect.any patterns
- Support explicit stack override
- Raise errors for ambiguous or no detection"
```

---

## Task 8: Environment Variable Validator

**Files:**
- Create: `src/agentpack/validators/__init__.py`
- Create: `src/agentpack/validators/env.py`
- Create: `tests/test_validators_env.py`

**Step 1: Write failing test**

Create `tests/test_validators_env.py`:

```python
"""Tests for environment variable validation."""

from pathlib import Path

import pytest

from agentpack.manifest import load_manifest
from agentpack.validators.env import validate_env_vars, EnvValidationWarning


class TestEnvValidation:
    """Test environment variable validation."""

    def test_no_warnings_when_all_defined(
        self, fixtures_dir: Path, tmp_path: Path
    ) -> None:
        """No warnings when all variables are defined."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        devcontainer = tmp_path / ".devcontainer"
        devcontainer.mkdir()
        (devcontainer / ".env").write_text("EXAMPLE_API_KEY=secret\n")

        warnings = validate_env_vars(manifest, tmp_path)
        assert len(warnings) == 0

    def test_warning_for_missing_var(
        self, fixtures_dir: Path, tmp_path: Path
    ) -> None:
        """Warning when referenced variable is missing."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        devcontainer = tmp_path / ".devcontainer"
        devcontainer.mkdir()
        (devcontainer / ".env").write_text("")

        warnings = validate_env_vars(manifest, tmp_path)
        assert len(warnings) == 1
        assert "EXAMPLE_API_KEY" in warnings[0].message

    def test_no_env_file(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """Warning when .env file doesn't exist."""
        manifest = load_manifest(fixtures_dir / "full.yml")

        warnings = validate_env_vars(manifest, tmp_path)
        # Should warn about missing file and variable
        assert len(warnings) >= 1

    def test_extract_env_vars(self, fixtures_dir: Path) -> None:
        """Extract ${env:VAR} and ${VAR} patterns."""
        manifest = load_manifest(fixtures_dir / "full.yml")
        # full.yml has ${env:EXAMPLE_API_KEY} in external-api server
        from agentpack.validators.env import _extract_env_refs

        refs = _extract_env_refs(manifest)
        assert "EXAMPLE_API_KEY" in refs
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_validators_env.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Create validators package**

Create `src/agentpack/validators/__init__.py`:

```python
"""Validators for agentpack."""

from agentpack.validators.env import EnvValidationWarning, validate_env_vars

__all__ = ["EnvValidationWarning", "validate_env_vars"]
```

**Step 4: Implement env validator**

Create `src/agentpack/validators/env.py`:

```python
"""Validate environment variable references."""

import re
from dataclasses import dataclass
from pathlib import Path

from agentpack.manifest.schema import Manifest

# Match ${VAR} or ${env:VAR}
ENV_REF_PATTERN = re.compile(r"\$\{(?:env:)?([A-Z_][A-Z0-9_]*)\}")


@dataclass
class EnvValidationWarning:
    """Warning about environment variable issues."""

    message: str


def _extract_env_refs(manifest: Manifest) -> set[str]:
    """Extract all environment variable references from manifest.

    Args:
        manifest: Validated manifest.

    Returns:
        Set of referenced variable names.
    """
    refs: set[str] = set()

    for server in manifest.mcp.servers.values():
        for value in server.env.values():
            matches = ENV_REF_PATTERN.findall(value)
            refs.update(matches)

    return refs


def _parse_env_file(path: Path) -> set[str]:
    """Parse .env file and return defined variable names.

    Args:
        path: Path to .env file.

    Returns:
        Set of defined variable names.
    """
    if not path.exists():
        return set()

    defined: set[str] = set()
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key = line.split("=", 1)[0].strip()
            if key:
                defined.add(key)

    return defined


def validate_env_vars(manifest: Manifest, project_dir: Path) -> list[EnvValidationWarning]:
    """Validate environment variable references.

    Args:
        manifest: Validated manifest.
        project_dir: Project directory.

    Returns:
        List of warnings for missing variables.
    """
    warnings: list[EnvValidationWarning] = []

    refs = _extract_env_refs(manifest)
    if not refs:
        return warnings

    env_file = project_dir / ".devcontainer" / ".env"
    defined = _parse_env_file(env_file)

    for ref in sorted(refs):
        if ref not in defined:
            warnings.append(
                EnvValidationWarning(
                    f"Environment variable {ref} is referenced but not defined in "
                    f".devcontainer/.env"
                )
            )

    return warnings
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_validators_env.py -v`
Expected: PASS (4 tests)

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: add environment variable validator

- Extract \${VAR} and \${env:VAR} references
- Parse .devcontainer/.env for defined vars
- Warn about undefined references"
```

---

## Task 9: Skills Validator

**Files:**
- Create: `src/agentpack/validators/skills.py`
- Create: `tests/test_validators_skills.py`
- Modify: `src/agentpack/validators/__init__.py`

**Step 1: Write failing test**

Create `tests/test_validators_skills.py`:

```python
"""Tests for skills validation."""

from pathlib import Path

import pytest

from agentpack.manifest import load_manifest
from agentpack.validators.skills import validate_skills, SkillsValidationError


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
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_validators_skills.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Implement skills validator**

Create `src/agentpack/validators/skills.py`:

```python
"""Validate skills configuration."""

import re
from dataclasses import dataclass
from pathlib import Path

from agentpack.manifest.schema import Manifest

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


def validate_skills(manifest: Manifest, project_dir: Path) -> list[SkillsValidationError]:
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
```

**Step 4: Update package exports**

Update `src/agentpack/validators/__init__.py`:

```python
"""Validators for agentpack."""

from agentpack.validators.env import EnvValidationWarning, validate_env_vars
from agentpack.validators.skills import SkillsValidationError, validate_skills

__all__ = [
    "EnvValidationWarning",
    "SkillsValidationError",
    "validate_env_vars",
    "validate_skills",
]
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_validators_skills.py -v`
Expected: PASS (4 tests)

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: add skills validator

- Check SKILL.md exists for required skills
- Validate frontmatter presence
- Validate name and description fields"
```

---

## Task 10: CLI Generate Command

**Files:**
- Modify: `src/agentpack/cli.py`
- Create: `tests/test_cli_generate.py`

**Step 1: Write failing test**

Create `tests/test_cli_generate.py`:

```python
"""Tests for generate command."""

from pathlib import Path
import subprocess
import sys


class TestGenerateCommand:
    """Test agentpack generate command."""

    def test_generate_dry_run(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """Generate command shows output without --write."""
        import shutil

        shutil.copy(fixtures_dir / "minimal.yml", tmp_path / "agentpack.yml")

        result = subprocess.run(
            [sys.executable, "-m", "agentpack", "generate"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "CLAUDE.md" in result.stdout
        assert "minimal-project" in result.stdout
        # Files should not be created
        assert not (tmp_path / "CLAUDE.md").exists()

    def test_generate_write(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """Generate command creates files with --write."""
        import shutil

        shutil.copy(fixtures_dir / "full.yml", tmp_path / "agentpack.yml")

        result = subprocess.run(
            [sys.executable, "-m", "agentpack", "generate", "--write"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / "AGENTS.md").exists()
        assert (tmp_path / ".claude" / "settings.json").exists()
        assert (tmp_path / "codex.config.toml").exists()

    def test_generate_manifest_not_found(self, tmp_path: Path) -> None:
        """Error when agentpack.yml not found."""
        result = subprocess.run(
            [sys.executable, "-m", "agentpack", "generate"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli_generate.py -v`
Expected: FAIL (no generate command)

**Step 3: Implement generate command**

Update `src/agentpack/cli.py`:

```python
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
```

**Step 4: Create __main__.py for python -m invocation**

Create `src/agentpack/__main__.py`:

```python
"""Allow running as python -m agentpack."""

from agentpack.cli import app

if __name__ == "__main__":
    app()
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_cli_generate.py -v`
Expected: PASS (3 tests)

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: add generate command

- Support dry-run (default) and --write mode
- Generate CLAUDE.md, AGENTS.md, settings.json, codex.config.toml
- Run env and skills validators with warnings"
```

---

## Task 11: Firewall Updater

**Files:**
- Create: `src/agentpack/devcontainer/__init__.py`
- Create: `src/agentpack/devcontainer/firewall.py`
- Create: `tests/test_devcontainer_firewall.py`

**Step 1: Write failing test**

Create `tests/test_devcontainer_firewall.py`:

```python
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

    def test_update_firewall_adds_domain(self, fixtures_dir: Path, tmp_path: Path) -> None:
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
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_devcontainer_firewall.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Create devcontainer package**

Create `src/agentpack/devcontainer/__init__.py`:

```python
"""Devcontainer configuration utilities."""

from agentpack.devcontainer.firewall import update_firewall

__all__ = ["update_firewall"]
```

**Step 4: Implement firewall updater**

Create `src/agentpack/devcontainer/firewall.py`:

```python
"""Update init-firewall.sh with MCP server domains."""

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from agentpack.manifest.schema import Manifest, MCPServerHTTP


@dataclass
class FirewallUpdateResult:
    """Result of firewall update operation."""

    success: bool
    message: str
    domains_added: int = 0


def extract_domains(manifest: Manifest) -> set[str]:
    """Extract domains from HTTP MCP servers.

    Args:
        manifest: Validated manifest.

    Returns:
        Set of domain names.
    """
    domains: set[str] = set()

    for server in manifest.mcp.servers.values():
        if isinstance(server, MCPServerHTTP):
            parsed = urlparse(server.url)
            if parsed.hostname:
                domains.add(parsed.hostname)

    return domains


def update_firewall(manifest: Manifest, project_dir: Path) -> FirewallUpdateResult:
    """Update init-firewall.sh with MCP server domains.

    Args:
        manifest: Validated manifest.
        project_dir: Project directory.

    Returns:
        Result of update operation.
    """
    domains = extract_domains(manifest)
    if not domains:
        return FirewallUpdateResult(
            success=True,
            message="No HTTP MCP servers to add",
            domains_added=0,
        )

    firewall_script = project_dir / ".devcontainer" / "init-firewall.sh"
    if not firewall_script.exists():
        return FirewallUpdateResult(
            success=False,
            message=f"Firewall script not found: {firewall_script}",
        )

    content = firewall_script.read_text()

    # Find ALLOWED_DOMAINS array
    pattern = r"(ALLOWED_DOMAINS=\(\s*\n)(.*?)(\n\s*\))"
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        return FirewallUpdateResult(
            success=False,
            message="Could not find ALLOWED_DOMAINS array in firewall script",
        )

    # Get existing domains
    existing_block = match.group(2)
    existing_domains = set(re.findall(r'"([^"]+)"', existing_block))

    # Add new domains
    new_domains = domains - existing_domains
    if not new_domains:
        return FirewallUpdateResult(
            success=True,
            message="All domains already present",
            domains_added=0,
        )

    # Build new array content
    all_domains = sorted(existing_domains | new_domains)
    new_block = "\n".join(f'    "{domain}"' for domain in all_domains)

    new_content = content[: match.start(2)] + new_block + content[match.end(2) :]
    firewall_script.write_text(new_content)

    return FirewallUpdateResult(
        success=True,
        message=f"Added domains: {sorted(new_domains)}",
        domains_added=len(new_domains),
    )
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_devcontainer_firewall.py -v`
Expected: PASS (4 tests)

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: add firewall updater for HTTP MCP domains

- Extract domains from HTTP MCP server URLs
- Update ALLOWED_DOMAINS array in init-firewall.sh
- Skip gracefully when script not found"
```

---

## Task 12: Init Command (Template Download)

**Files:**
- Create: `src/agentpack/init/__init__.py`
- Create: `src/agentpack/init/template.py`
- Create: `tests/test_init_template.py`
- Modify: `src/agentpack/cli.py`

**Step 1: Write failing test**

Create `tests/test_init_template.py`:

```python
"""Tests for template download."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from agentpack.init.template import parse_template_source, TemplateSource, download_template


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
        with pytest.raises(ValueError, match="Invalid template source"):
            parse_template_source("invalid")


class TestDownloadTemplate:
    """Test template download."""

    def test_download_creates_files(self, tmp_path: Path) -> None:
        """Download template creates expected files."""
        # Mock httpx response
        with patch("agentpack.init.template.httpx") as mock_httpx:
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
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_init_template.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Create init package**

Create `src/agentpack/init/__init__.py`:

```python
"""Template initialization."""

from agentpack.init.template import download_template, parse_template_source, TemplateSource

__all__ = ["download_template", "parse_template_source", "TemplateSource"]
```

**Step 4: Implement template module**

Create `src/agentpack/init/template.py`:

```python
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
    skeleton = '''version: "1"

project:
  name: "my-project"
  description: "Project description"

docs:
  mode: single-stack
  defaultStack: auto
'''

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
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_init_template.py -v`
Expected: PASS (6 tests)

**Step 6: Add init command to CLI**

Add to `src/agentpack/cli.py`:

```python
from agentpack.init import download_template, generate_skeleton, parse_template_source


@app.command
def init(
    directory: Path = Path("."),
    *,
    template: str = "github:agentpack/template-default",
    stack: str | None = None,
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
            print("Error: agentpack.yml already exists. Use --force to overwrite.", file=sys.stderr)
            sys.exit(1)
        if (directory / ".devcontainer").exists():
            print("Error: .devcontainer already exists. Use --force to overwrite.", file=sys.stderr)
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
```

**Step 7: Update imports in cli.py**

Add to imports at top of `src/agentpack/cli.py`:

```python
import httpx

from agentpack.init import download_template, generate_skeleton, parse_template_source
```

**Step 8: Run all tests**

Run: `uv run pytest -v`
Expected: All tests pass

**Step 9: Commit**

```bash
git add -A
git commit -m "feat: add init command for template download

- Parse github:owner/repo@branch#subdir format
- Download and extract .devcontainer from template
- Generate agentpack.yml skeleton"
```

---

## Task 13: Integrate Firewall Update into Generate

**Files:**
- Modify: `src/agentpack/cli.py`
- Modify: `tests/test_cli_generate.py`

**Step 1: Add test for firewall update**

Add to `tests/test_cli_generate.py`:

```python
    def test_generate_updates_firewall(self, fixtures_dir: Path, tmp_path: Path) -> None:
        """Generate updates firewall with HTTP MCP domains."""
        import shutil

        shutil.copy(fixtures_dir / "full.yml", tmp_path / "agentpack.yml")

        devcontainer = tmp_path / ".devcontainer"
        devcontainer.mkdir()
        (devcontainer / "init-firewall.sh").write_text(
            """#!/bin/bash
ALLOWED_DOMAINS=(
    "existing.com"
)
"""
        )

        result = subprocess.run(
            [sys.executable, "-m", "agentpack", "generate", "--write"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        content = (devcontainer / "init-firewall.sh").read_text()
        assert "api.example.com" in content
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli_generate.py::TestGenerateCommand::test_generate_updates_firewall -v`
Expected: FAIL (firewall not updated)

**Step 3: Update generate command**

Update `src/agentpack/cli.py` generate function to include firewall update:

```python
from agentpack.devcontainer import update_firewall

# Add after file writing in generate command:
    if write:
        # ... existing file writes ...

        # Update firewall
        firewall_result = update_firewall(manifest, directory)
        if firewall_result.success and firewall_result.domains_added > 0:
            print(f"  - Updated init-firewall.sh ({firewall_result.domains_added} domains added)")
        elif not firewall_result.success and "not found" not in firewall_result.message.lower():
            print(f"Warning: {firewall_result.message}", file=sys.stderr)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cli_generate.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: integrate firewall update into generate command

- Update init-firewall.sh with HTTP MCP domains
- Show warning on failure (non-blocking)"
```

---

## Task 14: Full Integration Test

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

Create `tests/test_integration.py`:

```python
"""Integration tests for full agentpack workflow."""

from pathlib import Path
import subprocess
import sys


class TestFullWorkflow:
    """Test complete agentpack workflows."""

    def test_init_and_generate(self, tmp_path: Path) -> None:
        """Full workflow: init -> edit manifest -> generate."""
        # Skip template download in test, create files manually
        devcontainer = tmp_path / ".devcontainer"
        devcontainer.mkdir()
        (devcontainer / "devcontainer.json").write_text("{}")
        (devcontainer / "Dockerfile").write_text("FROM ubuntu")
        (devcontainer / "init-firewall.sh").write_text(
            """#!/bin/bash
ALLOWED_DOMAINS=(
)
"""
        )

        # Create manifest
        manifest = tmp_path / "agentpack.yml"
        manifest.write_text(
            """version: "1"

project:
  name: "integration-test"
  description: "Integration test project"

stack: python

stacks:
  python:
    detect:
      any: ["pyproject.toml"]
    deps: "uv sync"
    lint: "uv run ruff check ."
    test: "uv run pytest"

mcp:
  servers:
    api:
      transport: http
      url: "https://api.test.com/mcp"
"""
        )

        # Create pyproject.toml for stack detection
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'")

        # Run generate
        result = subprocess.run(
            [sys.executable, "-m", "agentpack", "generate", "--write"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

        # Verify outputs
        claude_md = (tmp_path / "CLAUDE.md").read_text()
        assert "integration-test" in claude_md
        assert "uv sync" in claude_md
        assert "uv run pytest" in claude_md

        settings = (tmp_path / ".claude" / "settings.json").read_text()
        # HTTP servers are not in settings.json
        assert "{" in settings

        codex_config = (tmp_path / "codex.config.toml").read_text()
        assert "[mcp_servers.api]" in codex_config
        assert "api.test.com" in codex_config

        firewall = (devcontainer / "init-firewall.sh").read_text()
        assert "api.test.com" in firewall

    def test_generate_validates_skills(self, tmp_path: Path) -> None:
        """Generate warns about missing skills."""
        manifest = tmp_path / "agentpack.yml"
        manifest.write_text(
            """version: "1"

project:
  name: "test"
  description: "Test"

stacks:
  python:
    skills:
      required: ["missing-skill"]
"""
        )

        result = subprocess.run(
            [sys.executable, "-m", "agentpack", "generate"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "missing-skill" in result.stderr
        assert "SKILL.md not found" in result.stderr
```

**Step 2: Run integration tests**

Run: `uv run pytest tests/test_integration.py -v`
Expected: PASS (2 tests)

**Step 3: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests pass

**Step 4: Commit**

```bash
git add -A
git commit -m "test: add full integration tests

- Test init -> generate workflow
- Verify all output files generated correctly
- Test skills validation warnings"
```

---

## Task 15: Final Cleanup and Documentation

**Files:**
- Modify: `pyproject.toml` (description update)
- Run: format and lint checks

**Step 1: Run code quality checks**

```bash
uv run ruff format .
uv run ruff check . --fix
uv run ty check
```

**Step 2: Run full test suite**

```bash
uv run pytest -v
```

Expected: All tests pass, no lint errors

**Step 3: Final commit**

```bash
git add -A
git commit -m "chore: code quality cleanup

- Format with ruff
- Fix lint issues
- All tests passing"
```

---

## Summary

Total tasks: 15
Estimated commits: 15

Key deliverables:
1. CLI with `init` and `generate` commands
2. Manifest schema with Pydantic validation
3. Generators for CLAUDE.md, AGENTS.md, settings.json, codex.config.toml
4. Stack detection from project files
5. Environment variable and skills validation
6. Firewall updater for HTTP MCP domains
7. Template download from GitHub
8. Comprehensive test suite with snapshots

Run tests at any point with:
```bash
uv run pytest -v
```
