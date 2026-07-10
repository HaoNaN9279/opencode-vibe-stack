"""CLI entry point for the vibe-stack command.

Exposes :func:`main` as the programmatic entry point wired in
``pyproject.toml`` via ``vibe-stack = "vibe_stack.cli:main"``.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from vibe_stack.utils.path_util import detect_vibe_home


def _resolve_vibe_home() -> Path:
    """Determine the vibe-stack repository root.

    Precedence:
    1. ``VIBE_STACK_HOME`` environment variable.
    2. Filesystem walk-up via :func:`detect_vibe_home`.

    Returns:
        Absolute path to the vibe-stack repository root.

    Raises:
        RuntimeError: Propagated from :func:`detect_vibe_home` when the
            repository cannot be located.
    """
    env_val = os.environ.get("VIBE_STACK_HOME")
    if env_val:
        return Path(env_val).resolve()
    return detect_vibe_home()


def main(argv: list[str] | None = None) -> None:
    """CLI entry point — parse args and route to subcommands.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]``).
            Useful for testing — callers can inject an explicit argument
            list without touching ``sys.argv``.
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog="vibe-stack")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="vibe-stack 0.2.0",
    )

    sub = parser.add_subparsers(dest="command")

    # list
    sp_list = sub.add_parser("list", help="List available domains")
    sp_list.add_argument("--json", action="store_true", help="Output as JSON")

    # status
    sp_status = sub.add_parser("status", help="Show active domains")
    sp_status.add_argument("--json", action="store_true", help="Output as JSON")

    # info
    sp_info = sub.add_parser("info", help="Show domain details")
    sp_info.add_argument("domain", help="Domain key (e.g. dcc/blender)")
    sp_info.add_argument("--json", action="store_true", help="Output as JSON")

    # activate
    sp_activate = sub.add_parser("activate", help="Activate domains")
    sp_activate.add_argument(
        "domains", nargs="+", help="Domains to activate",
    )

    # deactivate
    sp_deactivate = sub.add_parser("deactivate", help="Deactivate domains")
    sp_deactivate.add_argument(
        "domains", nargs="+", help="Domains to deactivate",
    )

    # use-stack
    sp_use = sub.add_parser("use-stack", help="Use a stack preset")
    sp_use.add_argument(
        "name", nargs="?", default="", help="Stack name (omit to list available)",
    )

    # sync
    sub.add_parser("sync", help="Sync core and active domains")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_usage()
        return

    # Resolve paths once, after parsing so --version/--help work without
    # needing a real vibe-stack repo on disk.
    vibe_home = _resolve_vibe_home()
    project_root = Path.cwd().resolve()

    # ------------------------------------------------------------------
    # Route to command (lazy-imported to keep startup fast)
    # ------------------------------------------------------------------
    if args.command == "list":
        from vibe_stack.cli.commands.list_status import cmd_list

        cmd_list(vibe_home, json_output=args.json)

    elif args.command == "status":
        from vibe_stack.cli.commands.list_status import cmd_status

        cmd_status(vibe_home, project_root, json_output=args.json)

    elif args.command == "info":
        from vibe_stack.cli.commands.info import cmd_info

        cmd_info(vibe_home, args.domain, json_output=args.json)

    elif args.command == "activate":
        from vibe_stack.cli.commands.activate import cmd_activate

        cmd_activate(vibe_home, project_root, args.domains)

    elif args.command == "deactivate":
        from vibe_stack.cli.commands.deactivate import cmd_deactivate

        cmd_deactivate(vibe_home, project_root, args.domains)

    elif args.command == "use-stack":
        from vibe_stack.cli.commands.use_stack import cmd_use_stack

        cmd_use_stack(vibe_home, project_root, args.name)

    elif args.command == "sync":
        from vibe_stack.cli.commands.sync import cmd_sync

        cmd_sync(vibe_home, project_root)
