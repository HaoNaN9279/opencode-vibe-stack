"""Installation module for vibe-stack.

Called by ``install.sh`` and ``install.ps1`` (which act as thin wrappers),
or directly via ``python -m vibe_stack.install [--vibe-home PATH]``.

Provides:

* :func:`check_prerequisites` — check for uv, Python, Git availability
* :func:`run_install` — complete 8-step installation flow
* ``main()`` — CLI entry point with argparse
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

from vibe_stack import config
from vibe_stack import mcp
from vibe_stack import registry
from vibe_stack import symlinks
from vibe_stack.constants import (
    OPENCODE_CONFIG_DIR,
    OPECODE_CONFIG_NAME,
    VIBE_STACK_DIR_TYPES,
    VIBE_STACK_MCP_REGISTRY_PATH,
)
from vibe_stack.utils import (
    detect_vibe_stack_home,
    ensure_dir,
    is_windows,
    log_error,
    log_info,
    log_ok,
    log_warn,
)

# ── Schema constant ─────────────────────────────────────────────────
_OPENCODE_SCHEMA = "https://opencode.ai/config.json"

# ── Default opencode.json helper ────────────────────────────────────


def _default_opencode_config() -> dict:
    """Return the minimal default ``opencode.json`` structure."""
    return {
        "$schema": _OPENCODE_SCHEMA,
        "instructions": ["~/.config/opencode/rules/*.md"],
    }


# ── Prerequisite checks ─────────────────────────────────────────────


def check_prerequisites() -> list[str]:
    """Check whether uv, Python, and Git are available on the system.

    Uses :func:`shutil.which` to locate executables on ``PATH``.

    Returns:
        List of missing tool names (empty list = all present).
    """
    missing: list[str] = []

    if shutil.which("uv") is None:
        missing.append("uv")

    # Python can be named python3 or python
    if shutil.which("python3") is None and shutil.which("python") is None:
        missing.append("Python")

    if shutil.which("git") is None:
        missing.append("Git")

    return missing


# ── Internal step helpers ───────────────────────────────────────────


def _verify_vibe_home(vibe_home: Path) -> None:
    """Raise :class:`SystemExit` if *vibe_home* is not a valid vibe-stack repo."""
    core_md = vibe_home / "core" / "rules" / "00-global.md"
    domains_dir = vibe_home / "domains"

    if not core_md.is_file() or not domains_dir.is_dir():
        log_error(
            f"Not a valid vibe-stack repository: {vibe_home}\n"
            f"  Expected: core/rules/00-global.md + domains/"
        )
        sys.exit(1)

    log_ok(f"Verified vibe-stack repo: {vibe_home}")


def _step_core_symlinks(vibe_home: Path) -> None:
    """Link ``core/{type}/`` contents → ``~/.config/opencode/{type}/`` for all 6 types."""
    log_info("==> Creating core symlinks...")

    for type_name in VIBE_STACK_DIR_TYPES:
        core_type_dir = vibe_home / "core" / type_name
        dest_dir = OPENCODE_CONFIG_DIR / type_name

        if core_type_dir.is_dir():
            symlinks.link_directory_contents(core_type_dir, dest_dir)
            log_ok(f"  Linked core/{type_name}/ -> {dest_dir}")
        else:
            log_warn(f"  core/{type_name}/ not found, skipping")


def _step_opencode_config() -> None:
    """Ensure ``~/.config/opencode/opencode.json`` exists with instructions
    and ``skills.paths`` registered."""
    log_info("==> Configuring opencode.json...")

    opencode_path = OPENCODE_CONFIG_DIR / OPECODE_CONFIG_NAME
    rules_glob = '"~/.config/opencode/rules/*.md"'

    # 1. Create opencode.json if missing, or ensure instructions array
    if not opencode_path.is_file():
        default = _default_opencode_config()
        config.write_jsonc(opencode_path, default)
        log_ok(f"  Created {opencode_path}")
    else:
        result = config.array_add(opencode_path, "instructions", rules_glob)
        if result == 0:
            log_ok("  Added instructions entry")
        elif result == 2:
            log_ok("  instructions already has rules glob")
        else:
            log_warn("  Could not add instructions entry — check opencode.json manually")

    # 2. Register skills.paths: ["skills"]
    skills_value = '"skills"'
    result = config.nested_array_add(opencode_path, "skills", "paths", skills_value)
    if result == 0:
        log_ok("  Registered core skills in skills.paths")
    elif result == 2:
        log_ok("  skills.paths already has 'skills'")
    else:
        # "skills" parent key may not exist — fall back to dict-level merge
        _ensure_skills_paths(opencode_path)


def _ensure_skills_paths(opencode_path: Path) -> None:
    """Fallback: read opencode.json as dict, add ``skills.paths``, write back."""
    try:
        cfg = config.read_jsonc(opencode_path)
    except Exception as e:
        log_warn(f"  Could not read {opencode_path}: {e}")
        return

    skills = cfg.setdefault("skills", {})
    if not isinstance(skills, dict):
        skills = {}
        cfg["skills"] = skills

    paths = skills.setdefault("paths", [])
    if not isinstance(paths, list):
        paths = []
        skills["paths"] = paths

    if "skills" not in paths:
        paths.append("skills")
        config.write_jsonc(opencode_path, cfg)
        log_ok("  Registered core skills in skills.paths (dict fallback)")
    else:
        log_ok("  skills.paths already has 'skills'")


def _step_registry_template(vibe_home: Path) -> None:
    """Generate ``~/.config/opencode/vibe-stack-mcp.jsonc`` template if missing."""
    log_info("==> Generating MCP registry template...")

    registry_path = VIBE_STACK_MCP_REGISTRY_PATH

    if registry_path.is_file():
        log_info(f"  (already exists, skipping): {registry_path}")
        return

    try:
        template = registry.generate_template(vibe_home)
        registry.write_registry(registry_path, template)
        log_ok(f"  Created registry template: {registry_path}")
        log_info(
            "  Edit vibe-stack-mcp.jsonc to configure MCP servers"
        )
    except Exception as e:
        log_error(f"  Failed to generate registry template: {e}")


def _step_activate_core_mcp(vibe_home: Path) -> None:
    """Resolve and write Core MCP entries to opencode.json."""
    log_info("==> Activating Core MCP servers...")
    mcp.activate_mcp_core(vibe_home)


def _step_install_cli(vibe_home: Path) -> None:
    """Install CLI wrapper to ``~/.local/bin/vibe-stack``.

    On Linux/macOS this creates a symlink from the repo's
    ``bin/vibe-stack/vibe-stack`` script.  On Windows the CLI wrapping
    is handled by the install.ps1 PowerShell script, so only a message
    is logged.
    """
    log_info("==> Installing CLI wrapper...")

    if is_windows():
        cli_dest_dir = Path.home() / ".local" / "bin"
        cli_cmd_path = cli_dest_dir / "vibe-stack.cmd"
        ensure_dir(cli_dest_dir)

        vibe_home_str = str(vibe_home.resolve()).replace("\\", "\\\\")
        cmd_content = f"""@echo off
setlocal

set "VIBE_STACK_HOME=%VIBE_STACK_HOME%"
if "%VIBE_STACK_HOME%"=="" set "VIBE_STACK_HOME={vibe_home_str}"

uv run --project "%VIBE_STACK_HOME%" python -m vibe_stack.cli %*

endlocal
"""
        cli_cmd_path.write_text(cmd_content, encoding="ascii")
        log_ok(f"  Installed: {cli_cmd_path}")
        return

    cli_src = vibe_home / "bin" / "vibe-stack" / "vibe-stack"
    cli_dest = Path.home() / ".local" / "bin" / "vibe-stack"

    if not cli_src.is_file():
        log_warn(f"  CLI script not found: {cli_src}")
        return

    ensure_dir(cli_dest.parent)

    # Remove existing link or file
    try:
        symlinks.remove_link(cli_dest)
    except Exception:
        pass

    symlinks.create_symlink(cli_src, cli_dest)
    log_ok(f"  Installed: {cli_dest} -> {cli_src}")


def _step_post_install() -> None:
    """Print user-friendly post-install instructions."""
    print()
    log_ok("Installation complete!")
    print()
    log_info("Next Steps:")
    print(f"  1. Edit {VIBE_STACK_MCP_REGISTRY_PATH} to set your MCP paths")
    print("  2. Run 'vibe-stack activate <domain>' in your project")
    print()


# ── Main entry point ────────────────────────────────────────────────


def run_install(vibe_home: Path) -> None:
    """Execute the complete vibe-stack installation flow.

    Steps (order matters):

    1. Verify *vibe_home* is a valid vibe-stack repository
    2. Create core → ``~/.config/opencode/`` symlinks for all 6 types
    3. Ensure ``opencode.json`` exists with ``instructions`` array
    4. Register ``skills.paths`` in opencode.json
    5. Generate MCP registry template (skip if exists)
    6. Resolve and write Core MCP entries via ``activate_mcp_core``
    7. Install CLI wrapper to ``~/.local/bin/vibe-stack``
    8. Print post-install instructions
    """
    # 1. Verify
    _verify_vibe_home(vibe_home)

    # 2. Core symlinks
    _step_core_symlinks(vibe_home)

    # 3-4. opencode.json: instructions + skills.paths
    _step_opencode_config()

    # 5. Registry template (before activate_mcp_core which reads it)
    _step_registry_template(vibe_home)

    # 6. Activate Core MCPs
    _step_activate_core_mcp(vibe_home)

    # 7. Install CLI wrapper
    _step_install_cli(vibe_home)

    # 8. Post-install
    _step_post_install()


def main() -> None:
    """CLI entry point for ``python -m vibe_stack.install``."""
    parser = argparse.ArgumentParser(
        prog="vibe-stack-install",
        description="Install vibe-stack: create symlinks, configure opencode.json, "
        "generate registry, activate core MCPs, and install CLI.",
    )
    parser.add_argument(
        "--vibe-home",
        type=Path,
        default=None,
        help="Path to the vibe-stack repository root "
        "(default: auto-detect from VIBE_STACK_HOME env var or CWD walk)",
    )

    args = parser.parse_args()

    # Detect vibe-stack home
    vibe_home = detect_vibe_stack_home(
        vibe_home_override=args.vibe_home if args.vibe_home else None
    )

    run_install(vibe_home)


if __name__ == "__main__":
    main()
