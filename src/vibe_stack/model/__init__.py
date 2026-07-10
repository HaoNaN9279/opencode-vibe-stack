"""Data model dataclasses for vibe-stack.

This package contains pure-data dataclasses that represent the
core domain model: domains, activation state, stacks, and MCP servers.
"""

from __future__ import annotations

from vibe_stack.model.domain import CoreConfig, DomainConfig, DomainMeta
from vibe_stack.model.mcp import MCPServerEntry
from vibe_stack.model.stack import StackMeta
from vibe_stack.model.state import ActivationState, DomainState

__all__ = [
    "ActivationState",
    "CoreConfig",
    "DomainConfig",
    "DomainMeta",
    "DomainState",
    "MCPServerEntry",
    "StackMeta",
]
