"""Domain configuration dataclasses.

Defines :class:`DomainMeta` (domain.json metadata), :class:`DomainConfig`
(complete domain configuration with resolved file paths), and
:class:`CoreConfig` (core configuration file lists).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DomainMeta:
    """Domain metadata parsed from ``domain.json``.

    Parameters:
        name: Short domain identifier (e.g. ``"blender"``).
        description: Human-readable description of the domain.
        version: Semantic version string (e.g. ``"1.0.0"``).
        tags: Classification tags (e.g. ``["dcc", "3d"]``).
        dependencies: Domain keys this domain depends on
            (e.g. ``["ai/data-forge"]``).
    """

    name: str
    description: str
    version: str
    tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)


@dataclass
class DomainConfig:
    """Complete domain configuration with resolved file paths.

    Parameters:
        meta: Metadata from ``domain.json``.
        domain_key: Slash-delimited domain identifier
            (e.g. ``"dcc/blender"``).
        namespace: Underscore-delimited namespace derived from the key
            (e.g. ``"dcc_blender"``).  Defaults to the key with slashes
            replaced by underscores.
        domain_root: Filesystem root of this domain (e.g.
            ``Path("domains/dcc/blender")``).
        rules: Rule files belonging to this domain.
        agents: Agent definition files.
        commands: Custom command definition files.
        mcp_files: MCP JSON config files.
        mcp_dirs: MCP executable directories.
        skills: Skill directories.
    """

    meta: DomainMeta
    domain_key: str
    namespace: str = ""
    domain_root: Path = field(default_factory=Path)
    rules: list[Path] = field(default_factory=list)
    agents: list[Path] = field(default_factory=list)
    commands: list[Path] = field(default_factory=list)
    mcp_files: list[Path] = field(default_factory=list)
    mcp_dirs: list[Path] = field(default_factory=list)
    skills: list[Path] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Auto-compute *namespace* from *domain_key* if not provided."""
        if not self.namespace:
            self.namespace = self.domain_key.replace("/", "_")


@dataclass
class CoreConfig:
    """Core configuration file lists from ``core/``.

    Parameters:
        rules: Global rule files that are always loaded.
        agents: Global agent definitions.
        commands: Global custom commands.
        mcp_files: MCP JSON config files from core.
        mcp_dirs: MCP executable directories from core.
        skills: Global skill directories.
    """

    rules: list[Path] = field(default_factory=list)
    agents: list[Path] = field(default_factory=list)
    commands: list[Path] = field(default_factory=list)
    mcp_files: list[Path] = field(default_factory=list)
    mcp_dirs: list[Path] = field(default_factory=list)
    skills: list[Path] = field(default_factory=list)
