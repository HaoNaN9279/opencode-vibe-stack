"""OpenCode JSON writer — the ONLY module that touches opencode.json.

Provides read/write/merge operations for the OpenCode configuration file
(opencode.json / opencode.jsonc). This is the single authority for all
opencode.json file I/O in the vibe-stack codebase.

Functions:
    read_opencode     — read and parse opencode.json/jsonc
    write_opencode    — write config dict as JSON to disk
    merge_vibe_entries— add/remove vibe-stack entries without touching user config
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from vibe_stack.errors import VibeStackError
from vibe_stack.writer.jsonc_utils import parse_jsonc


def read_opencode(path: Path) -> dict:
    """Read opencode.json/jsonc configuration file.

    Uses the jsonc_utils parser internally to handle JSONC comments
    (// line comments, /* */ block comments) and trailing commas.

    Args:
        path: Path to the opencode.json or opencode.jsonc file.

    Returns:
        Parsed configuration as a dict. Returns an empty dict for
        missing or empty files.

    Raises:
        VibeStackError: If the file contains corrupt JSON that cannot
            be parsed even after comment stripping.
    """
    try:
        return parse_jsonc(path)
    except json.JSONDecodeError as exc:
        raise VibeStackError(
            f"Failed to parse {path}: invalid JSON — {exc}"
        ) from exc


def write_opencode(path: Path, config: dict) -> None:
    """Write a configuration dict as formatted JSON to opencode.json.

    Creates parent directories if they don't exist. Overwrites any
    existing file. Output is plain JSON (indent=2) — no comments are
    generated. If the config dict contains a ``$schema`` key, it is
    preserved at the top of the output for readability.

    Args:
        path: Target file path (e.g. ``.opencode/opencode.json``).
        config: The configuration dict to write.

    Raises:
        OSError: If the file cannot be written (permission, disk full, etc.).
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Order $schema first for readability if present
    ordered: dict = {}
    if "$schema" in config:
        ordered["$schema"] = config["$schema"]
    ordered.update(config)

    content = json.dumps(ordered, indent=2, ensure_ascii=False)
    path.write_text(content + "\n", encoding="utf-8")


def merge_vibe_entries(
    current: dict,
    add: dict | None = None,
    remove: dict | None = None,
) -> dict:
    """Merge vibe-stack managed entries into an opencode.json config dict.

    Only touches entries that vibe-stack manages — user-owned instructions,
    skills.paths, and MCP server entries are always preserved untouched.

    The function operates in two phases, both optional:

    1. **Add phase** — add vibe-stack entries that don't already exist:
       * ``add["instructions"]`` — list of instruction globs to add
       * ``add["skills.paths"]``  — list of skill paths to add
       * ``add["mcpServers"]``    — dict of MCP servers to add (keys get a
         ``"vibe:"`` prefix; all existing ``vibe:`` entries are cleared first)

    2. **Remove phase** — remove specified vibe-stack entries:
       * ``remove["instructions"]`` — instruction entries to remove
       * ``remove["skills.paths"]``  — skill path entries to remove
       * ``remove["mcpServers"]``    — MCP server keys to remove (keys should
         match without ``"vibe:"`` prefix)

    Args:
        current: The current opencode.json config dict (never mutated).
        add: Entries to add. Dict with optional keys ``"instructions"``,
            ``"skills.paths"``, ``"mcpServers"``.
        remove: Entries to remove. Same structure as *add*.

    Returns:
        A **new** dict with the merged result. The *current* dict is never
        mutated. The returned dict is a deep copy.

    Examples:
        >>> current = {"instructions": ["user.md"], "skills": {"paths": ["s"]}}
        >>> merged = merge_vibe_entries(
        ...     current,
        ...     add={
        ...         "instructions": [".opencode/rules/ns/*.md"],
        ...         "skills.paths": [".opencode/skills/ns"],
        ...         "mcpServers": {"ns": {"command": ["ns"]}},
        ...     },
        ... )
        >>> ".opencode/rules/ns/*.md" in merged["instructions"]
        True
        >>> merged["mcp"]["vibe:ns"]
        {'command': ['ns']}
    """
    result = copy.deepcopy(current)

    # --- Add phase ---
    if add is not None:
        _apply_add_instructions(result, add.get("instructions", []))
        _apply_add_skills_paths(result, add.get("skills.paths", []))
        _apply_add_mcp_servers(result, add.get("mcpServers", {}))

    # --- Remove phase ---
    if remove is not None:
        _apply_remove_instructions(result, remove.get("instructions", []))
        _apply_remove_skills_paths(result, remove.get("skills.paths", []))
        _apply_remove_mcp_servers(result, remove.get("mcpServers", {}))

    return result


# ---------------------------------------------------------------------------
# Internal helpers — instruction management
# ---------------------------------------------------------------------------


def _ensure_instructions(result: dict) -> None:
    """Lazily create the ``instructions`` key if missing."""
    if "instructions" not in result:
        result["instructions"] = []


def _ensure_skills_paths(result: dict) -> None:
    """Lazily create the ``skills.paths`` key hierarchy if missing."""
    if "skills" not in result:
        result["skills"] = {}
    if "paths" not in result["skills"]:
        result["skills"]["paths"] = []


def _ensure_mcp(result: dict) -> None:
    """Lazily create the ``mcp`` key if missing."""
    if "mcp" not in result:
        result["mcp"] = {}


def _apply_add_instructions(result: dict, entries: list[str]) -> None:
    """Add instruction entries that don't already exist in the result."""
    if not entries:
        return
    _ensure_instructions(result)
    for entry in entries:
        if entry not in result["instructions"]:
            result["instructions"].append(entry)


def _apply_remove_instructions(result: dict, entries: list[str]) -> None:
    """Remove specified instruction entries from the result."""
    if not entries or "instructions" not in result:
        return
    for entry in entries:
        if entry in result["instructions"]:
            result["instructions"].remove(entry)


# ---------------------------------------------------------------------------
# Internal helpers — skills.paths management
# ---------------------------------------------------------------------------


def _apply_add_skills_paths(result: dict, entries: list[str]) -> None:
    """Add skills.paths entries that don't already exist in the result."""
    if not entries:
        return
    _ensure_skills_paths(result)
    for entry in entries:
        if entry not in result["skills"]["paths"]:
            result["skills"]["paths"].append(entry)


def _apply_remove_skills_paths(result: dict, entries: list[str]) -> None:
    """Remove specified skills.paths entries from the result."""
    if not entries or "skills" not in result or "paths" not in result["skills"]:
        return
    for entry in entries:
        if entry in result["skills"]["paths"]:
            result["skills"]["paths"].remove(entry)


# ---------------------------------------------------------------------------
# Internal helpers — MCP server management
# ---------------------------------------------------------------------------


def _apply_add_mcp_servers(result: dict, entries: dict) -> None:
    """Add MCP server entries with 'vibe:' prefix, clearing existing vibe: entries first.

    This implements the "activate" behavior: remove all existing vibe:-prefixed
    MCP entries, then add the new set. Non-vibe (user-owned) MCP entries are
    always preserved.
    """
    if not entries:
        return
    _ensure_mcp(result)

    # Strip ALL existing vibe: entries (activate = full replacement)
    result["mcp"] = {
        k: v for k, v in result["mcp"].items() if not k.startswith("vibe:")
    }
    # Add new entries with vibe: prefix
    for name, config in entries.items():
        result["mcp"][f"vibe:{name}"] = config


def _apply_remove_mcp_servers(result: dict, entries: dict) -> None:
    """Remove specified MCP server entries.

    Keys in *entries* may or may not have the ``"vibe:"`` prefix.
    The function normalizes them to ``"vibe:{name}"`` before removal.
    Non-vibe MCP keys are never touched.
    """
    if not entries or "mcp" not in result:
        return

    for name in entries:
        key = f"vibe:{name}" if not name.startswith("vibe:") else name
        result["mcp"].pop(key, None)
