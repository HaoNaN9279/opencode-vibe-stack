"""Stack definition dataclasses.

Stacks are preset combinations of domains defined in ``stacks/*.json``.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StackMeta:
    """Stack definition parsed from ``stacks/*.json``.

    Parameters:
        name: Human-readable stack name (e.g. ``"Game Development"``).
        description: Optional description of the stack.
        domains: Ordered list of domain keys included in this stack
            (e.g. ``["game-dev/unity", "game-dev/unreal"]``).
    """

    name: str
    description: str = ""
    domains: list[str] = field(default_factory=list)
