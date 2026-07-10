"""MCP path resolver with env var fallback chain.

Resolves ``${...}`` placeholders in MCP server command configurations
against a priority chain: specific environment variable → general
``MCP_PATH`` env var → per-user paths config file → as-is fallback.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from vibe_stack.writer.jsonc_utils import parse_jsonc

# Regex to match ``${VAR_NAME}`` placeholders in command strings.
_PLACEHOLDER_RE = re.compile(r"\$\{([^}]+)\}")

# Path to the per-user MCP paths mapping file, relative to home.
_PATHS_CONFIG_REL = Path(".config") / "opencode" / "vibe-mcp-paths.json"


def resolve_mcp_config(
    mcp_json_path: Path,
    namespace: str,
    project_root: Path,
) -> dict[str, object]:
    """Resolve MCP JSON config, replacing ``${...}`` placeholders.

    Reads an MCP JSON (or JSONC) configuration file, processes each
    server entry, and resolves placeholder expressions in command
    elements using the following priority chain:

    1. Environment variable matching the placeholder name (e.g.,
       ``${MCP_PATH_FOO}`` resolves from env ``MCP_PATH_FOO``).
    2. Environment variable ``MCP_PATH`` (general fallback).
    3. Per-user path mapping file at
       ``~/.config/opencode/vibe-mcp-paths.json``, looked up by server
       name.
    4. If nothing resolves, the placeholder is left unchanged so the
       binary can be found on ``PATH``.

    Supports both ``"mcpServers"`` and legacy ``"mcp"`` top-level keys
    in the input JSON. When both are present, ``mcpServers`` is preferred.

    Parameters:
        mcp_json_path: Path to the MCP configuration file (``.json`` or
            ``.jsonc``).
        namespace: Domain namespace used to prefix output keys (e.g.,
            ``"dcc_blender"``).
        project_root: Project root directory (reserved for future use).

    Returns:
        A dictionary whose keys are ``vibe:{namespace}_{server_name}``
        and values are resolved server configuration dicts.
    """
    config = parse_jsonc(mcp_json_path)

    # Read servers from either "mcpServers" or legacy "mcp" key.
    servers_raw = config.get("mcpServers")
    if servers_raw is None:
        servers_raw = config.get("mcp", {})

    if not servers_raw or not isinstance(servers_raw, dict):
        return {}

    # Load the per-user paths config (may be empty if missing).
    paths_config = _load_paths_config()

    resolved: dict[str, object] = {}
    for server_name, server_cfg in servers_raw.items():  # type: ignore[union-attr]
        if not isinstance(server_cfg, dict):
            continue

        # Make a shallow copy so we don't mutate the parsed dict items.
        new_cfg: dict[str, object] = dict(server_cfg)  # type: ignore[arg-type]

        command = server_cfg.get("command")
        if isinstance(command, list):
            new_cfg["command"] = _resolve_command(
                command, server_name, paths_config
            )

        key = f"vibe:{namespace}_{server_name}"
        resolved[key] = new_cfg

    return resolved


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_paths_config() -> dict[str, str]:
    """Load the per-user MCP paths mapping.

    Returns:
        A dict mapping server names to executable paths, or an empty
        dict if the file does not exist.
    """
    paths_file = Path.home() / _PATHS_CONFIG_REL
    raw = parse_jsonc(paths_file)
    if not raw:
        return {}
    # Ensure values are strings.
    return {str(k): str(v) for k, v in raw.items()}


def _resolve_command(
    command: list[str],
    server_name: str,
    paths_config: dict[str, str],
) -> list[str]:
    """Resolve placeholders in every element of a command list.

    Parameters:
        command: The raw command list (may contain ``${...}`` entries).
        server_name: The server key from the MCP JSON (used for config
            file lookup).
        paths_config: Parsed contents of ``vibe-mcp-paths.json``.

    Returns:
        A new list with placeholders resolved.
    """
    return [_resolve_element(elem, server_name, paths_config) for elem in command]


def _resolve_element(
    elem: str,
    server_name: str,
    paths_config: dict[str, str],
) -> str:
    """Resolve ``${...}`` placeholders in a single command element.

    Resolution order:
    1. Exact env var match for the placeholder name.
    2. ``MCP_PATH`` env var (general fallback).
    3. Per-user ``vibe-mcp-paths.json`` mapping, using *server_name*.
    4. Leave the placeholder unchanged.

    Parameters:
        elem: A single command element (e.g., ``"${MCP_PATH_FOO}"``).
        server_name: Server key for config-file lookup.
        paths_config: Parsed paths mapping.

    Returns:
        The element with placeholders replaced (or left as-is).
    """

    def _replace(match: re.Match[str]) -> str:
        var_name = match.group(1)

        # 1. Exact env var match.
        env_val = os.environ.get(var_name)
        if env_val is not None:
            return env_val

        # 2. General MCP_PATH fallback.
        mcp_path = os.environ.get("MCP_PATH")
        if mcp_path is not None:
            return mcp_path

        # 3. Per-user paths config lookup (by server name).
        if server_name in paths_config:
            return paths_config[server_name]

        # 4. Nothing resolved — keep the placeholder as-is.
        return match.group(0)

    return _PLACEHOLDER_RE.sub(_replace, elem)
