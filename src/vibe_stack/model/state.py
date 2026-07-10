"""Activation state dataclasses.

Represents the runtime activation state persisted to
``.vibe-stack-state.json`` in user projects.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DomainState:
    """Activation state for a single domain.

    Parameters:
        domain_key: Slash-delimited domain identifier (e.g.
            ``"dcc/blender"``).
        namespace: Underscore-delimited namespace (e.g.
            ``"dcc_blender"``).
        activated_at: ISO 8601 timestamp of activation.
        files: Relative paths of symlinked files under ``.opencode/``.
        directories: Relative paths of symlinked directories under
            ``.opencode/``.
        opencode_entries: Map of OpenCode config section to value lists
            (e.g. ``{"instructions": ["..."], "skills.paths": ["..."]}``).
    """

    domain_key: str
    namespace: str
    activated_at: str
    files: list[str] = field(default_factory=list)
    directories: list[str] = field(default_factory=list)
    opencode_entries: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class ActivationState:
    """Full activation state persisted to ``.vibe-stack-state.json``.

    Parameters:
        version: Schema version (currently ``2``).
        domains: Mapping of domain_key → :class:`DomainState`.
    """

    version: int = 2
    domains: dict[str, DomainState] = field(default_factory=dict)
