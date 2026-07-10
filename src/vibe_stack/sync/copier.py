"""File copier for domain and core config synchronization.

Provides three functions:
    sync_domain_files  — copy domain files into .opencode/{namespace}/
    remove_domain_files — remove tracked files and directories
    sync_core_files    — copy core files into user config directory
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, replace
from pathlib import Path

from vibe_stack.model.domain import CoreConfig, DomainConfig
from vibe_stack.model.state import DomainState
from vibe_stack.utils.path_util import compute_relative_target

# Directories and files to exclude from directory-tree copies.
# These patterns match items that are never useful at the target
# (git repos, build artifacts, virtual environments, etc.).
_COPY_IGNORE = shutil.ignore_patterns(
    ".git",
    "__pycache__",
    ".venv",
    "node_modules",
    ".pytest_cache",
    "*.pyc",
)


@dataclass(frozen=True)
class FileChanges:
    """Counts of file-system mutations performed during a sync.

    Parameters:
        created: Number of new files or directories created.
        updated: Number of existing files re-copied (source mtime newer).
        deleted: Number of stale target files/directories removed.
    """

    created: int = 0
    updated: int = 0
    deleted: int = 0


# -- Mapping tables ----------------------------------------------------------


_FILE_TYPE_ATTRS: list[tuple[str, str]] = [
    ("rules", "rules"),
    ("agents", "agents"),
    ("commands", "commands"),
    ("mcp_files", "mcp"),
]

_DIR_TYPE_ATTRS: list[tuple[str, str]] = [
    ("skills", "skills"),
    ("mcp_dirs", "mcp"),
]


# -- Domain sync -------------------------------------------------------------


def _stale_cleanup(
    dc: DomainConfig, dot_opencode: Path, changes: FileChanges
) -> FileChanges:
    """Remove target files/dirs that have no matching source in *dc*."""
    type_expected: dict[str, set[str]] = {
        "rules": {s.name for s in dc.rules},
        "agents": {s.name for s in dc.agents},
        "commands": {s.name for s in dc.commands},
        "mcp": {s.name for s in dc.mcp_files} | {s.name for s in dc.mcp_dirs},
        "skills": {s.name for s in dc.skills},
    }

    for dir_type, expected_names in type_expected.items():
        ns_dir = dot_opencode / dir_type / dc.namespace
        if not ns_dir.is_dir():
            continue
        for item in sorted(ns_dir.iterdir()):
            if item.name not in expected_names:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                changes = replace(changes, deleted=changes.deleted + 1)

    return changes


def sync_domain_files(dc: DomainConfig, dot_opencode: Path) -> FileChanges:
    """Sync domain files to ``.opencode/{namespace}/`` subdirectories.

    Copies individual files (rules, agents, commands, MCP .json) and
    directory trees (skills, MCP companion folders) into the project's
    ``.opencode`` directory organised by type and namespace.

    Parameters:
        dc: Fully-resolved domain configuration with source file paths.
        dot_opencode: Path to the project's ``.opencode`` directory.

    Returns:
        Mutation counts indicating how many files were created, updated,
        or deleted during the sync.
    """
    changes = FileChanges()

    # 1. Copy individual files (rules, agents, commands, mcp_files).
    for attr_name, dir_type in _FILE_TYPE_ATTRS:
        sources: list[Path] = getattr(dc, attr_name)
        for source in sources:
            target = compute_relative_target(
                source, dot_opencode, dc.namespace, dir_type
            )
            target.parent.mkdir(parents=True, exist_ok=True)

            if not target.exists():
                shutil.copy2(source, target)
                changes = replace(changes, created=changes.created + 1)
            elif source.stat().st_mtime > target.stat().st_mtime:
                shutil.copy2(source, target)
                changes = replace(changes, updated=changes.updated + 1)

    # 2. Copy directory trees (skills, mcp_dirs).
    for attr_name, dir_type in _DIR_TYPE_ATTRS:
        sources: list[Path] = getattr(dc, attr_name)
        for source in sources:
            target = compute_relative_target(
                source, dot_opencode, dc.namespace, dir_type
            )
            target.parent.mkdir(parents=True, exist_ok=True)

            if not target.exists():
                shutil.copytree(source, target, ignore=_COPY_IGNORE)
                changes = replace(changes, created=changes.created + 1)
            else:
                # Check if any source file is newer than its target
                # counterpart — if so, re-copy the whole tree.
                needs_update = False
                for src_file in source.rglob("*"):
                    if not src_file.is_file():
                        continue
                    rel = src_file.relative_to(source)
                    tgt_file = target / rel
                    if (
                        not tgt_file.exists()
                        or src_file.stat().st_mtime > tgt_file.stat().st_mtime
                    ):
                        needs_update = True
                        break
                if needs_update:
                    shutil.rmtree(target)
                    shutil.copytree(source, target, ignore=_COPY_IGNORE)
                    changes = replace(changes, updated=changes.updated + 1)

    # 3. Remove stale targets that no longer have a source.
    changes = _stale_cleanup(dc, dot_opencode, changes)

    return changes


# -- Domain removal ----------------------------------------------------------


def remove_domain_files(state: DomainState, dot_opencode: Path) -> None:
    """Remove all tracked files and directories for a domain.

    Parameters:
        state: Domain activation state containing the file and directory
            relative paths to remove.
        dot_opencode: Path to the project's ``.opencode`` directory.
    """
    for rel_path in state.files:
        target = dot_opencode / rel_path
        if target.exists():
            target.unlink()

    for rel_path in state.directories:
        target = dot_opencode / rel_path
        if target.is_dir():
            shutil.rmtree(target)


# -- Core sync ---------------------------------------------------------------


def sync_core_files(core: CoreConfig, user_config_dir: Path) -> None:
    """Copy core files to the user config directory.

    Copies individual files and directory trees from the vibe-stack
    ``core/`` into ``~/.config/opencode/`` (no namespace nesting).

    Parameters:
        core: Core configuration with source file paths.
        user_config_dir: Path to the user config directory
            (e.g. ``~/.config/opencode``).
    """
    # Individual files.
    for dir_type, sources in [
        ("rules", core.rules),
        ("agents", core.agents),
        ("commands", core.commands),
        ("mcp", core.mcp_files),
    ]:
        for source in sources:
            target = user_config_dir / dir_type / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    # Directory trees (mcp_dirs, skills).
    for dir_type, sources in [
        ("mcp", core.mcp_dirs),
        ("skills", core.skills),
    ]:
        for source in sources:
            target = user_config_dir / dir_type / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target, ignore=_COPY_IGNORE)
