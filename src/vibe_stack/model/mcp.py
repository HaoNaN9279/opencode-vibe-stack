"""MCP server configuration dataclasses.

Represents a single MCP server entry as declared in domain ``mcp/*.json``
files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MCPServerEntry:
    """A single MCP server configuration entry.

    Parameters:
        name: Unique server identifier (e.g. ``"data-forge"``).
        type: ``"local"`` for locally-run servers, ``"remote"`` for
            externally-hosted servers.
        command: The command (and args) to launch a local server.
            ``None`` for remote servers.
        enabled: Whether this server is enabled by default.
        extra: Arbitrary additional configuration for future extension.
    """

    name: str
    type: str = "local"
    command: list[str] | None = None
    enabled: bool = True
    extra: dict[str, Any] = field(default_factory=dict)
