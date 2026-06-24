"""Cross-platform symlink / junction creation utilities.

Provides four core functions that abstract away platform differences:

* :func:`create_symlink` — file symlink with Windows copy fallback
* :func:`create_dir_link` — directory link (symlink on Unix, junction on Windows)
* :func:`link_directory_contents` — per-item links from a source directory
* :func:`remove_link` — safe removal of symlinks / junctions

On Windows, directory links use NTFS junctions (``cmd /c mklink /J``) because
``os.symlink()`` for directories requires Administrator privileges.  File
symlinks that fail on Windows silently fall back to copying the file.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

from vibe_stack.utils import is_windows, log_warn


# ── Internal helpers ───────────────────────────────────────────────


def _rmdir_windows(path: Path) -> None:
    """Remove a Windows junction or empty directory via ``cmd /c rmdir``."""
    subprocess.run(
        ["cmd", "/c", "rmdir", str(path)],
        capture_output=True,
    )


def _mklink_junction(src: Path, dest: Path) -> bool:
    """Create an NTFS junction at *dest* pointing to *src* via ``mklink /J``.

    Returns ``True`` on success.
    """
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(dest), str(src)],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and dest.exists()


# ── Public API ─────────────────────────────────────────────────────


def create_symlink(src: Path, dest: Path) -> None:
    """Create a **file** symlink at *dest* pointing to *src*.

    On Windows, if ``os.symlink`` fails (e.g. no Developer Mode), the file
    is copied instead and a warning is emitted.
    """
    # Clean up existing dest
    remove_link(dest)

    try:
        os.symlink(src, dest)
    except OSError:
        if is_windows():
            log_warn(
                f"Symlink unavailable — copying file: {dest.name} "
                f"(enable Developer Mode to avoid copies)"
            )
            shutil.copy2(str(src), str(dest))
        else:
            raise


def create_dir_link(src: Path, dest: Path) -> None:
    """Create a **directory** link at *dest* pointing to *src*.

    *   Linux / macOS — uses :func:`os.symlink`.
    *   Windows — creates an NTFS junction via ``mklink /J`` (no admin
        rights required when Developer Mode is enabled).
    """
    # Clean up existing dest — handle junctions, symlinks, and real dirs
    remove_link(dest)

    if is_windows():
        if _mklink_junction(src, dest):
            return
        # Junction failed — fall through to os.symlink as last resort
        log_warn(
            f"Junction creation failed for {dest.name}, "
            f"falling back to os.symlink (may need admin)"
        )

    # Unix native symlink or Windows fallback
    os.symlink(src, dest, target_is_directory=True)


def link_directory_contents(
    src_dir: Path,
    dest_dir: Path,
    prefix: str = "",
    exclude_pattern: str | None = None,
) -> None:
    """Link every item inside *src_dir* into *dest_dir* as individual entries.

    *   If *dest_dir* is an existing symlink or junction, it is removed first.
    *   *dest_dir* is then (re)created as a real directory.
    *   Each item gets a per-item link inside *dest_dir*.
    *   When *prefix* is non-empty, each link name is
        ``{prefix}_{basename}``.
    *   When *exclude_pattern* is not ``None``, items whose name matches the
        shell glob pattern (via :func:`fnmatch.fnmatch`) are skipped.

    Directories become junctions (Windows) or symlinks (Unix); files
    become symlinks (with copy fallback on Windows).
    """
    # Remove old directory-level link if present (legacy upgrade path)
    remove_link(dest_dir)

    # Ensure dest_dir is a real directory
    if dest_dir.exists():
        # It's a real directory leftover — clear it so we start fresh
        if not dest_dir.is_symlink():
            shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    if not src_dir.is_dir():
        log_warn(f"Source directory not found, skipping: {src_dir}")
        return

    for item in sorted(src_dir.iterdir()):
        if exclude_pattern is not None and fnmatch(item.name, exclude_pattern):
            continue
        item_name = item.name
        link_name = f"{prefix}_{item_name}" if prefix else item_name
        link_path = dest_dir / link_name

        remove_link(link_path)

        if item.is_dir():
            create_dir_link(item, link_path)
        else:
            create_symlink(item, link_path)


def link_tools_directory(
    src_dir: Path, dest_dir: Path, prefix: str = ""
) -> None:
    """Link each item inside *src_dir* as individual links in *dest_dir*.

    Unlike :func:`link_directory_contents`, this function does **not** clear
    the destination directory — it only adds or overwrites individual item
    links.  This allows multiple domains to contribute tools to the same
    ``.opencode/tools/`` directory without clobbering each other.

    When *prefix* is non-empty, only **files** get the prefix (e.g.
    ``ai_data-forge_caption.ts``); **directories** are linked without prefix
    (e.g. ``data-forge/`` → ``data-forge/``) so that their internal structure
    remains self-contained.

    If *src_dir* does not exist or is empty, this function silently skips.
    """
    if not src_dir.is_dir():
        return

    # Check if directory has any entries
    try:
        has_entries = any(True for _ in src_dir.iterdir())
    except OSError:
        return

    if not has_entries:
        return

    # Remove old directory-level link if present (upgrade from legacy)
    remove_link(dest_dir)
    # Ensure dest_dir is a real directory (never a symlink/junction itself)
    dest_dir.mkdir(parents=True, exist_ok=True)

    for item in sorted(src_dir.iterdir()):
        item_name = item.name
        # Directories keep original name; files get the domain prefix
        if item.is_dir():
            link_name = item_name
        else:
            link_name = f"{prefix}_{item_name}" if prefix else item_name
        link_path = dest_dir / link_name
        remove_link(link_path)
        if item.is_dir():
            create_dir_link(item, link_path)
        else:
            create_symlink(item, link_path)


def remove_link(path: Path) -> None:
    """Safely remove a symlink, junction, or directory **without following
    the target**.

    Handles three cases:

    * Symlink / junction → ``os.unlink`` on Unix; ``cmd /c rmdir`` on Windows.
    * Real directory → removed with :func:`shutil.rmtree`.
    * Real file → removed with :func:`os.unlink`.
    * Does not exist → no-op.
    """
    if not os.path.lexists(str(path)):
        return

    if is_windows():
        # On Windows, os.unlink cannot remove junctions — use rmdir
        _rmdir_windows(path)
        # If rmdir didn't clean it up (e.g. it's a real file), try again
        if os.path.lexists(str(path)):
            try:
                path.unlink()
            except OSError:
                if path.is_dir():
                    shutil.rmtree(path)
    else:
        if path.is_symlink():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
