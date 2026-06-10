"""Utility functions for vibe-stack.

Provides:
- Colored logging with automatic TTY detection
- Path resolution and vibe-stack home detection
- Platform detection
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional


# ── ANSI color codes ──────────────────────────────────────────────
_STYLES: dict[str, str] = {
    "bold": "\033[1m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "red": "\033[31m",
    "blue": "\033[34m",
    "reset": "\033[0m",
}


def _colorize(text: str, color: str) -> str:
    """Wrap *text* in ANSI escape codes when stdout is a TTY."""
    if sys.stdout.isatty():
        return f"{_STYLES[color]}{text}{_STYLES['reset']}"
    return text


# ── Logging ───────────────────────────────────────────────────────


def log_info(msg: str) -> None:
    """Print an informational message prefixed with ``[i]``."""
    prefix = _colorize("[i]", "blue")
    print(f"{prefix} {msg}")


def log_ok(msg: str) -> None:
    """Print a success message prefixed with ``[OK]``."""
    prefix = _colorize("[OK]", "green")
    print(f"{prefix} {msg}")


def log_warn(msg: str) -> None:
    """Print a warning message prefixed with ``[warn]``."""
    prefix = _colorize("[warn]", "yellow")
    print(f"{prefix} {msg}")


def log_error(msg: str) -> None:
    """Print an error message prefixed with ``[ERROR]``.

    This function does **not** call ``sys.exit()`` — callers are
    responsible for error handling.
    """
    prefix = _colorize("[ERROR]", "red")
    print(f"{prefix} {msg}")


# ── Path utilities ────────────────────────────────────────────────


def resolve_path(p: str) -> Path:
    """Resolve *p* to an absolute :class:`Path`, expanding ``~``."""
    return Path(p).expanduser().resolve()


def ensure_dir(p: Path) -> None:
    """Ensure directory *p* exists, creating parents as needed."""
    p.mkdir(parents=True, exist_ok=True)


# ── VIBE_STACK_HOME detection ────────────────────────────────────


def detect_vibe_stack_home(vibe_home_override: Optional[Path] = None) -> Path:
    """Detect the root directory of the vibe-stack repository.

    Resolution order (first wins):

    1. ``VIBE_STACK_HOME`` environment variable
    2. ``vibe_home_override`` argument (if provided)
    3. Walk upward from :func:`~pathlib.Path.cwd` looking for a directory
       that contains both ``core/rules/00-global.md`` and ``domains/``.
    4. Fallback to :func:`~pathlib.Path.cwd` if nothing matches.

    Returns
        An absolute :class:`~pathlib.Path` pointing to the repo root.
    """
    # 1. Environment variable
    env_val = os.environ.get("VIBE_STACK_HOME")
    if env_val:
        return Path(env_val).resolve()

    # 2. Explicit override
    if vibe_home_override is not None:
        return vibe_home_override.resolve()

    # 3. Walk upward from CWD
    cwd = Path.cwd().resolve()
    for parent in [cwd] + list(cwd.parents):
        if _is_vibe_stack_root(parent):
            return parent

    # 4. Fallback
    return cwd


def _is_vibe_stack_root(path: Path) -> bool:
    """Return ``True`` if *path* looks like a vibe-stack repository root."""
    return (
        (path / "core" / "rules" / "00-global.md").is_file()
        and (path / "domains").is_dir()
    )


# ── Platform detection ────────────────────────────────────────────


def is_windows() -> bool:
    """Return ``True`` when running on a Windows platform."""
    return sys.platform == "win32"
