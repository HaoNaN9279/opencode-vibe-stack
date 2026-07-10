"""Config merger for opencode.json entries.

Provides pure functions for adding/removing entries in the opencode.json
configuration sections: instructions, skills.paths, and mcpServers.

All functions return NEW copies — they never mutate their inputs.
"""

from __future__ import annotations

from typing import Literal

from vibe_stack.errors import ConfigMergeError

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_VALID_MODES: frozenset[str] = frozenset({"add", "remove"})


def _validate_mode(mode: str) -> None:
    """Raise ConfigMergeError if *mode* is not valid."""
    if mode not in _VALID_MODES:
        raise ConfigMergeError(
            f"invalid merge mode {mode!r} — expected one of {sorted(_VALID_MODES)!r}"
        )


# ---------------------------------------------------------------------------
# merge_instructions
# ---------------------------------------------------------------------------


def merge_instructions(
    current: list[str],
    namespace: str,
    mode: Literal["add", "remove"],
) -> list[str]:
    """Add or remove ``.opencode/rules/{namespace}/*.md`` from instructions.

    Parameters:
        current: Existing instructions list (never mutated).
        namespace: Domain namespace (e.g. ``dcc_blender``).
        mode: ``"add"`` appends the glob if not already present;
            ``"remove"`` removes it if present.

    Returns:
        A new list with the entry added or removed.

    Raises:
        ConfigMergeError: If *mode* is not ``"add"`` or ``"remove"``.
    """
    _validate_mode(mode)
    target = f".opencode/rules/{namespace}/*.md"

    if mode == "add":
        if target in current:
            return list(current)
        return [*current, target]

    # mode == "remove"
    return [entry for entry in current if entry != target]


# ---------------------------------------------------------------------------
# merge_skills_paths
# ---------------------------------------------------------------------------


def merge_skills_paths(
    current: list[str],
    namespace: str,
    mode: Literal["add", "remove"],
) -> list[str]:
    """Add or remove ``.opencode/skills/{namespace}`` from skills.paths.

    Parameters:
        current: Existing skills.paths list (never mutated).
        namespace: Domain namespace (e.g. ``dcc_blender``).
        mode: ``"add"`` appends the path if not already present;
            ``"remove"`` removes it if present.

    Returns:
        A new list with the entry added or removed.

    Raises:
        ConfigMergeError: If *mode* is not ``"add"`` or ``"remove"``.
    """
    _validate_mode(mode)
    target = f".opencode/skills/{namespace}"

    if mode == "add":
        if target in current:
            return list(current)
        return [*current, target]

    # mode == "remove"
    return [entry for entry in current if entry != target]


# ---------------------------------------------------------------------------
# merge_mcp_servers
# ---------------------------------------------------------------------------


def merge_mcp_servers(
    current: dict,
    entries: dict,
    mode: Literal["add", "remove"],
) -> dict:
    """Add or remove ``vibe:``-prefixed MCP server entries.

    Parameters:
        current: Existing ``mcpServers`` dict (never mutated).  Keys that do
            **not** start with ``"vibe:"`` are always preserved unchanged.
        entries: For ``"add"``: mapping of server names to configs — each key
            is automatically prefixed with ``"vibe:"``.  For ``"remove"``:
            mapping whose **keys** (already prefixed) identify the entries
            to remove; values are ignored.
        mode: ``"add"`` merges entries in (with ``"vibe:"`` prefix);
            ``"remove"`` drops matching keys.

    Returns:
        A new dict with the requested changes applied.

    Raises:
        ConfigMergeError: If *mode* is not ``"add"`` or ``"remove"``.
    """
    _validate_mode(mode)

    # Separate vibe-prefixed entries from user-owned entries.
    result: dict = {}
    for key, value in current.items():
        if key.startswith("vibe:"):
            # Only carry forward vibe entries in "add" mode
            if mode == "add":
                result[key] = value
            # In "remove" mode, we'll selectively keep based on entries
            else:
                if key not in entries:
                    result[key] = value
        else:
            result[key] = value

    if mode == "add":
        for name, config in entries.items():
            result[f"vibe:{name}"] = config

    return result
