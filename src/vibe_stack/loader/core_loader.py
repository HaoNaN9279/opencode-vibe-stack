"""Core configuration loader — scans ``core/`` directory for config files.

This module provides :func:`load_core`, the entry point for loading all
core (always-loaded) configuration from the ``core/`` directory hierarchy.
"""

from __future__ import annotations

from pathlib import Path

from vibe_stack.model.domain import CoreConfig


def _collect_md_files(directory: Path) -> list[Path]:
    """Return sorted ``.md`` files under *directory*.

    Returns an empty list if the directory does not exist.
    """
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.md"))


def _collect_json_files(directory: Path) -> list[Path]:
    """Return sorted ``.json`` files under *directory*.

    Returns an empty list if the directory does not exist.
    """
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.json"))


def _collect_subdirs(directory: Path) -> list[Path]:
    """Return sorted subdirectories under *directory*.

    Returns an empty list if the directory does not exist.
    """
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.iterdir() if p.is_dir())


def _collect_skill_dirs(skills_dir: Path) -> list[Path]:
    """Return sorted subdirectories that contain a ``SKILL.md`` file.

    Returns an empty list if *skills_dir* does not exist.
    """
    if not skills_dir.is_dir():
        return []
    return sorted(p for p in skills_dir.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())


def load_core(vibe_home: Path) -> CoreConfig:
    """Load core configuration from the ``core/`` directory.

    Scans each well-known subdirectory under *vibe_home* and returns a
    :class:`~vibe_stack.model.domain.CoreConfig` with the discovered files.

    The following subdirectories are recognised (all optional):

    =================  =================================  ====================
    Directory          Item type                           Extension
    =================  =================================  ====================
    ``rules/``         Rule files                          ``.md``
    ``agents/``        Agent definitions                   ``.md``
    ``commands/``      Custom commands                     ``.md``
    ``mcp/``           MCP config files (``.json``)        ``.json``
    ``mcp/``           MCP binary directories              (subdirs)
    ``skills/``        Skill directories                   (subdirs with
                                                           ``SKILL.md``)
    =================  =================================  ====================

    Missing or empty subdirectories are silently skipped and the
    corresponding field in the returned config is an empty list.

    Parameters:
        vibe_home: Base path of the ``core/`` directory (typically
            :data:`~vibe_stack.constants.VIBE_HOME`).

    Returns:
        A :class:`~vibe_stack.model.domain.CoreConfig` instance populated
        with the discovered files.
    """
    rules_dir = vibe_home / "rules"
    agents_dir = vibe_home / "agents"
    commands_dir = vibe_home / "commands"
    mcp_dir = vibe_home / "mcp"
    skills_dir = vibe_home / "skills"

    return CoreConfig(
        rules=_collect_md_files(rules_dir),
        agents=_collect_md_files(agents_dir),
        commands=_collect_md_files(commands_dir),
        mcp_files=_collect_json_files(mcp_dir),
        mcp_dirs=_collect_subdirs(mcp_dir),
        skills=_collect_skill_dirs(skills_dir),
    )
