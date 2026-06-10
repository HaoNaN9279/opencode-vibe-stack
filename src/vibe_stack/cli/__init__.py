"""vibe-stack CLI — command routing via argparse.

Usage:
    vibe-stack list
    vibe-stack status
    vibe-stack activate <domains...>
    vibe-stack deactivate <domains...>
    vibe-stack use-stack <name>
    vibe-stack core-update
    vibe-stack help
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vibe_stack.utils import detect_vibe_stack_home


def main(argv: list[str] | None = None) -> None:
    """CLI entry point — parse arguments and delegate to subcommands."""
    vibe_home = detect_vibe_stack_home()
    project_root = Path.cwd().resolve()

    # ── Pre-validate command before argparse ─────────────────
    known_commands = {
        "list",
        "status",
        "activate",
        "deactivate",
        "use-stack",
        "core-update",
        "help",
    }
    raw_args = sys.argv[1:] if argv is None else argv

    if not raw_args or raw_args[0] not in known_commands:
        if raw_args:
            print(f"未知命令: {raw_args[0]}", file=sys.stderr)
            print(file=sys.stderr)
        _print_usage()
        sys.exit(1)

    # ── argparse setup ───────────────────────────────────────
    parser = argparse.ArgumentParser(
        prog="vibe-stack",
        description="管理 OpenCode / OMO 领域配置",
        add_help=False,
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # ── list ─────────────────────────────────────────────────
    subparsers.add_parser("list", help="列出可用领域")

    # ── status ───────────────────────────────────────────────
    subparsers.add_parser("status", help="显示当前项目激活的领域")

    # ── activate ─────────────────────────────────────────────
    p_activate = subparsers.add_parser("activate", help="激活一个或多个领域")
    p_activate.add_argument(
        "domains", nargs="+", metavar="DOMAIN", help="领域名称 (e.g. dcc/blender)"
    )

    # ── deactivate ───────────────────────────────────────────
    p_deactivate = subparsers.add_parser("deactivate", help="停用一个或多个领域")
    p_deactivate.add_argument(
        "domains", nargs="+", metavar="DOMAIN", help="领域名称 (e.g. dcc/blender)"
    )

    # ── use-stack ────────────────────────────────────────────
    p_use_stack = subparsers.add_parser(
        "use-stack", help="使用预设堆栈激活多个领域"
    )
    p_use_stack.add_argument("name", nargs="?", default="", metavar="NAME", help="堆栈名称 (e.g. game-dev)")

    # ── core-update ──────────────────────────────────────────
    subparsers.add_parser("core-update", help="更新 core/ 配置的符号链接")

    # ── help ─────────────────────────────────────────────────
    subparsers.add_parser("help", help="显示此帮助信息")

    args = parser.parse_args(raw_args)

    # ── Route to subcommand handlers (lazy imports) ──────────
    if args.command == "list":
        from vibe_stack.cli import cli_list_status

        cli_list_status.cmd_list(vibe_home=vibe_home, project_root=project_root)

    elif args.command == "status":
        from vibe_stack.cli import cli_list_status

        cli_list_status.cmd_status(vibe_home=vibe_home, project_root=project_root)

    elif args.command == "activate":
        from vibe_stack.cli import cli_activate

        cli_activate.cmd_activate(
            domains=args.domains,
            vibe_home=vibe_home,
            project_root=project_root,
        )

    elif args.command == "deactivate":
        from vibe_stack.cli import cli_deactivate

        cli_deactivate.cmd_deactivate(
            domains=args.domains,
            vibe_home=vibe_home,
            project_root=project_root,
        )

    elif args.command == "use-stack":
        from vibe_stack.cli import cli_use_stack

        cli_use_stack.cmd_use_stack(
            name=args.name,
            vibe_home=vibe_home,
            project_root=project_root,
        )

    elif args.command == "core-update":
        from vibe_stack.cli.cli_core_update import cmd_core_update

        cmd_core_update(
            vibe_home=vibe_home, project_root=project_root
        )

    elif args.command == "help":
        from vibe_stack.cli import cli_help

        cli_help.cmd_help(vibe_home=vibe_home, project_root=project_root)


def _print_usage() -> None:
    """Print formatted usage information."""
    print("USAGE")
    print("    vibe-stack COMMAND ...")
    print()
    print("COMMANDS")
    print("    list         列出可用领域")
    print("    status       显示当前项目激活的领域")
    print("    activate     激活一个或多个领域")
    print("    deactivate   停用一个或多个领域")
    print("    use-stack    使用预设堆栈激活多个领域")
    print("    core-update  更新 core/ 配置的符号链接")
    print("    help         显示此帮助信息")


if __name__ == "__main__":
    main()
