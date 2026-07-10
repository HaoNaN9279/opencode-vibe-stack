"""Sync engine — orchestration layer for all sync/copy/merge/write operations.

Provides five public functions:
    activate_domain   — activate a domain in the current project
    deactivate_domain — deactivate a domain from the current project
    sync_core         — sync core config to user's OpenCode config directory
    sync_all_active   — re-sync all active domains
    sync              — full sync: core + all active domains
"""

from __future__ import annotations

import copy
import os
from datetime import datetime, timezone
from pathlib import Path

from vibe_stack.errors import (
    DomainAlreadyActiveError,
    DomainNotActiveError,
)
from vibe_stack.loader.core_loader import load_core
from vibe_stack.loader.domain_loader import load_domain
from vibe_stack.model.state import DomainState
from vibe_stack.sync.copier import remove_domain_files, sync_core_files, sync_domain_files
from vibe_stack.sync.mcp_resolver import resolve_mcp_config
from vibe_stack.sync.state_manager import (
    add_domain,
    list_active_domains,
    read_state,
    remove_domain,
    write_state,
)
from vibe_stack.writer.jsonc_utils import parse_jsonc
from vibe_stack.writer.opencode_writer import merge_vibe_entries, read_opencode, write_opencode

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

_CORE_DIR = "core"


def _dot_opencode(project_root: Path) -> Path:
    """Return the project's ``.opencode`` directory path."""
    return project_root / ".opencode"


def _opencode_json_path(base: Path) -> Path:
    """Return path to opencode.json under *base*."""
    return base / "opencode.json"


# ---------------------------------------------------------------------------
# Domain activation helpers
# ---------------------------------------------------------------------------


def _build_domain_state(
    dc,  # DomainConfig (lazy import avoids circular)
    resolved_mcp: dict[str, object],
) -> DomainState:
    """Build a DomainState from a DomainConfig and resolved MCP entries.

    Tracks every file and directory that sync_domain_files copies, plus
    the opencode.json entries that were added.
    """
    ns = dc.namespace
    files: list[str] = []
    directories: list[str] = []

    # Individual files
    for attr_name, dir_type in [
        ("rules", "rules"),
        ("agents", "agents"),
        ("commands", "commands"),
        ("mcp_files", "mcp"),
    ]:
        for source in getattr(dc, attr_name, []):
            files.append(f"{dir_type}/{ns}/{source.name}")

    # Directory trees (skills, mcp_dirs)
    for attr_name, dir_type in [
        ("skills", "skills"),
        ("mcp_dirs", "mcp"),
    ]:
        for source in getattr(dc, attr_name, []):
            directories.append(f"{dir_type}/{ns}/{source.name}")

    # Track opencode.json entries
    opencode_entries: dict[str, list[str]] = {
        "instructions": [f".opencode/rules/{ns}/*.md"],
        "skills.paths": [f".opencode/skills/{ns}"],
    }
    # MCP keys: strip "vibe:" prefix for storage — merge_vibe_entries
    # will re-add it during both add and remove phases.
    mcp_raw_keys: list[str] = []
    for key in resolved_mcp:
        if key.startswith("vibe:"):
            mcp_raw_keys.append(key[len("vibe:"):])
        else:
            mcp_raw_keys.append(key)
    if mcp_raw_keys:
        opencode_entries["mcpServers"] = mcp_raw_keys

    return DomainState(
        domain_key=dc.domain_key,
        namespace=ns,
        activated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        files=sorted(files),
        directories=sorted(directories),
        opencode_entries=opencode_entries,
    )


def _resolve_domain_mcp(dc, project_root: Path) -> dict[str, object]:
    """Resolve all MCP config files for a domain.

    Returns a merged dict whose keys are ``vibe:{namespace}_{server}``.
    """
    merged: dict[str, object] = {}
    for mcp_file in dc.mcp_files:
        resolved = resolve_mcp_config(mcp_file, dc.namespace, project_root)
        merged.update(resolved)
    return merged


def _strip_vibe_prefix(entries: dict[str, object]) -> dict[str, object]:
    """Strip ``vibe:`` prefix from all keys so merge_vibe_entries can re-add it."""
    return {
        (key[len("vibe:"):] if key.startswith("vibe:") else key): value
        for key, value in entries.items()
    }


# ---------------------------------------------------------------------------
# Domain deactivation helpers
# ---------------------------------------------------------------------------


def _build_remove_dict(ds: DomainState) -> dict:
    """Build a ``remove`` dict for merge_vibe_entries from a DomainState."""
    remove: dict = {}
    oe = ds.opencode_entries

    if "instructions" in oe:
        remove["instructions"] = oe["instructions"]
    if "skills.paths" in oe:
        remove["skills.paths"] = oe["skills.paths"]
    if "mcpServers" in oe:
        # merge_vibe_entries remove phase expects a dict (values are ignored)
        remove["mcpServers"] = {k: {} for k in oe["mcpServers"]}

    return remove


def _sync_tools_rule(vibe_home: Path, user_config_dir: Path) -> None:
    """Generate the vibe-stack-tools.md rule file.

    Scans ``tools/`` for tool directories (those containing a
    ``pyproject.toml``), extracts metadata, and writes a machine-readable
    rule file to ``{user_config_dir}/rules/vibe-stack-tools.md``.

    The generated file contains absolute paths so AI agents can locate
    and execute tools regardless of the current working directory.
    """
    tools_dir = vibe_home / "tools"
    if not tools_dir.is_dir():
        return

    vibe_root_str = str(vibe_home.resolve())

    lines: list[str] = [
        "# Vibe Stack Tools",
        "",
        "> 此文件由 `vibe-stack sync` 自动生成，请勿手动编辑。",
        "",
        f"Vibe Stack 根目录: `{vibe_root_str}`",
        "",
        "## 工具启动方式",
        "",
        "每个工具通过 `uv run --project <路径> <命令>` 启动。",
        "首次使用前需在工具目录执行 `uv sync` 安装依赖。",
        "",
        "## 可用工具",
        "",
    ]

    for tool_dir in sorted(tools_dir.iterdir()):
        if not tool_dir.is_dir():
            continue

        pyproject = tool_dir / "pyproject.toml"
        if not pyproject.is_file():
            continue

        tool_name = tool_dir.name
        tool_path = str(tool_dir.resolve())

        # Extract entry points from pyproject.toml.
        scripts = _read_tool_scripts(pyproject)

        lines.append(f"### {tool_name}")
        lines.append(f"- **路径**: `{tool_path}`")
        if scripts:
            lines.append(f"- **命令**: `{', '.join(scripts)}`")
            lines.append(f"- **用法**: `uv run --project {tool_path} {' '.join(scripts[:1])}`")
        else:
            # Fallback: use tool name as module entry.
            lines.append(f"- **用法**: `uv run --project {tool_path} python -m {tool_name}`")
        lines.append("")

    rule_path = user_config_dir / "rules" / "vibe-stack-tools.md"
    rule_path.parent.mkdir(parents=True, exist_ok=True)
    rule_path.write_text("\n".join(lines), encoding="utf-8")


def _read_tool_scripts(pyproject_path: Path) -> list[str]:
    """Extract entry-point script names from a pyproject.toml."""
    try:
        raw: dict = parse_jsonc(pyproject_path)  # type: ignore[assignment]
    except Exception:
        return []

    project = raw.get("project")
    if not isinstance(project, dict):
        return []
    scripts = project.get("scripts", {})
    if isinstance(scripts, dict):
        return sorted(scripts.keys())
    return []


# ============================================================================
# Public API
# ============================================================================


def activate_domain(
    vibe_home: Path,
    project_root: Path,
    domain_key: str,
) -> None:
    """Activate a domain in the project.

    Copies domain files into ``.opencode/{namespace}/``, merges
    instructions, skills.paths, and MCP server entries into
    ``opencode.json``, and records the activation in the state file.

    Parameters:
        vibe_home: Root of the vibe-stack repository (contains
            ``domains/`` and ``core/``).
        project_root: Root of the project being configured.
        domain_key: Slash-delimited domain identifier
            (e.g. ``"dcc/blender"``).

    Raises:
        DomainNotFoundError: If *domain_key* does not correspond to a
            domain on disk.
        DomainAlreadyActiveError: If *domain_key* is already active in
            this project.
    """
    # 1. Load domain config (raises DomainNotFoundError if missing).
    dc = load_domain(vibe_home, domain_key)

    # 2. Check if already active.
    state = read_state(project_root)
    if domain_key in state.domains:
        raise DomainAlreadyActiveError(
            f"domain '{domain_key}' is already active"
        )

    # 3. Copy domain files into .opencode/.
    dot = _dot_opencode(project_root)
    sync_domain_files(dc, dot)

    # 4. Read current opencode.json.
    oc_path = _opencode_json_path(dot)
    current = read_opencode(oc_path)

    # 5. Resolve MCP configs.
    resolved_mcp = _resolve_domain_mcp(dc, project_root)

    # 6. Build add dict and merge.
    ns = dc.namespace
    add: dict[str, object] = {
        "instructions": [f".opencode/rules/{ns}/*.md"],
        "skills.paths": [f".opencode/skills/{ns}"],
    }
    if resolved_mcp:
        add["mcpServers"] = _strip_vibe_prefix(resolved_mcp)

    merged = merge_vibe_entries(current, add=add)

    # 7. Write opencode.json.
    write_opencode(oc_path, merged)

    # 8. Build DomainState and persist.
    ds = _build_domain_state(dc, resolved_mcp)
    add_domain(state, ds)
    write_state(project_root, state)


def deactivate_domain(
    vibe_home: Path,
    project_root: Path,
    domain_key: str,
) -> None:
    """Deactivate a domain from the project.

    Removes all tracked files and directories, strips the domain's
    entries from ``opencode.json``, and removes the domain from the
    activation state file.

    Parameters:
        vibe_home: Root of the vibe-stack repository.
        project_root: Root of the project.
        domain_key: Domain identifier to deactivate.

    Raises:
        DomainNotActiveError: If *domain_key* is not currently active.
    """
    # 1. Read state and validate.
    state = read_state(project_root)
    if domain_key not in state.domains:
        raise DomainNotActiveError(
            f"domain '{domain_key}' is not active"
        )

    ds = state.domains[domain_key]

    # 2. Remove all tracked files and directories.
    dot = _dot_opencode(project_root)
    remove_domain_files(ds, dot)

    # 3. Remove entries from opencode.json.
    oc_path = _opencode_json_path(dot)
    current = read_opencode(oc_path)
    remove_dict = _build_remove_dict(ds)
    merged = merge_vibe_entries(current, remove=remove_dict)
    write_opencode(oc_path, merged)

    # 4. Remove domain from state file.
    remove_domain(state, domain_key)
    write_state(project_root, state)


def sync_core(
    vibe_home: Path,
    user_config_dir: Path | None = None,
) -> None:
    """Sync core config to the user's OpenCode configuration directory.

    Copies core files from ``vibe_home/core/`` into the user config
    directory (defaults to ``~/.config/opencode``) and ensures
    ``opencode.json`` contains the necessary entries for core rules,
    skills, and MCP servers.

    Parameters:
        vibe_home: Root of the vibe-stack repository.
        user_config_dir: Target user config directory.  Defaults to
            ``~/.config/opencode``.
    """
    if user_config_dir is None:
        user_config_dir = Path.home() / ".config" / "opencode"

    core_dir = vibe_home / _CORE_DIR

    # 1. Load core config.
    core = load_core(core_dir)

    # 2. Copy core files to user config directory.
    sync_core_files(core, user_config_dir)

    # 3. Read current opencode.json.
    oc_path = _opencode_json_path(user_config_dir)
    current = read_opencode(oc_path)

    # 4. Resolve core MCP configs and transform keys to vibe:core- prefix.
    resolved_mcp: dict[str, object] = {}
    for mcp_file in core.mcp_files:
        raw = resolve_mcp_config(mcp_file, "core", vibe_home)
        for key, value in raw.items():
            # Transform vibe:core_X → vibe:core-X
            new_key = key.replace("vibe:core_", "vibe:core-", 1)
            resolved_mcp[new_key] = value

    # 5. Build add dict.
    add: dict[str, object] = {
        "instructions": ["~/.config/opencode/rules/*.md"],
    }
    # Ensure skills.paths includes "skills" for core skills directory.
    current_skills_paths: list[str] = current.get("skills", {}).get("paths", [])
    if "skills" not in current_skills_paths:
        add["skills.paths"] = ["skills"]

    if resolved_mcp:
        add["mcpServers"] = _strip_vibe_prefix(resolved_mcp)

    merged = merge_vibe_entries(current, add=add)

    # 6. Write opencode.json.
    write_opencode(oc_path, merged)

    # 7. Generate tools index rule file.
    _sync_tools_rule(vibe_home, user_config_dir)


def sync_all_active(
    vibe_home: Path,
    project_root: Path,
) -> None:
    """Re-sync all active domains in the project.

    Reads the state file, re-loads each active domain's configuration,
    re-copies its files, and re-merges its entries into ``opencode.json``.

    Parameters:
        vibe_home: Root of the vibe-stack repository.
        project_root: Root of the project.
    """
    # 1. Read state.
    state = read_state(project_root)
    if not state.domains:
        return

    dot = _dot_opencode(project_root)
    oc_path = _opencode_json_path(dot)
    current = read_opencode(oc_path)

    # 2. Re-sync files for every active domain and collect entries.
    instr_list: list[str] = []
    skills_list: list[str] = []
    all_mcp: dict[str, object] = {}
    updated_domains: dict[str, DomainState] = {}

    for domain_key, ds in state.domains.items():
        # Re-load domain config (may have changed on disk).
        dc = load_domain(vibe_home, domain_key)

        # Re-copy files.
        sync_domain_files(dc, dot)

        # Resolve MCP.
        resolved_mcp = _resolve_domain_mcp(dc, project_root)

        # Track entries for batch merge.
        ns = dc.namespace
        instr_entry = f".opencode/rules/{ns}/*.md"
        if instr_entry not in instr_list:
            instr_list.append(instr_entry)

        skills_entry = f".opencode/skills/{ns}"
        if skills_entry not in skills_list:
            skills_list.append(skills_entry)

        all_mcp.update(resolved_mcp)

        # Rebuild DomainState with updated tracking info.
        updated_ds = _build_domain_state(dc, resolved_mcp)
        updated_domains[domain_key] = updated_ds

    add: dict[str, object] = {
        "instructions": instr_list,
        "skills.paths": skills_list,
    }

    # 3. Merge all entries into opencode.json at once.
    if all_mcp:
        add["mcpServers"] = _strip_vibe_prefix(all_mcp)

    merged = merge_vibe_entries(current, add=add)
    write_opencode(oc_path, merged)

    # 4. Update state with potentially refreshed DomainState entries.
    for key, ds in updated_domains.items():
        add_domain(state, ds)
    write_state(project_root, state)


def sync(
    vibe_home: Path,
    project_root: Path,
) -> None:
    """Full sync: core config + all active domains at once.

    Equivalent to calling :func:`sync_core` followed by
    :func:`sync_all_active`.

    Parameters:
        vibe_home: Root of the vibe-stack repository.
        project_root: Root of the project.
    """
    sync_core(vibe_home)
    sync_all_active(vibe_home, project_root)
