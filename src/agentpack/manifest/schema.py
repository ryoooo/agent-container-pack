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
