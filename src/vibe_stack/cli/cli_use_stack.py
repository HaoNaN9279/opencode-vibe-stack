"""Use-stack command — activate all domains from a stack preset."""

from __future__ import annotations

import json
from pathlib import Path

from vibe_stack.utils import log_error, log_info, log_ok


def cmd_use_stack(vibe_home: Path, project_root: Path, name: str) -> None:
    """Activate all domains defined in a stack preset.

    Reads ``<vibe_home>/stacks/<name>.json`` and calls ``cmd_activate``
    for each domain in the ``domains`` array.

    Parameters
    ----------
    vibe_home:
        Root of the vibe-stack repository.
    project_root:
        Root of the current project.
    name:
        Stack name (without ``.json`` extension). If empty or falsy,
        lists available stacks.
    """
    stacks_dir = vibe_home / "stacks"

    # ── No stack name given — list available stacks ─────────
    if not name:
        _list_available_stacks(stacks_dir)
        return

    # ── Read stack file ─────────────────────────────────────
    stack_file = stacks_dir / f"{name}.json"
    if not stack_file.is_file():
        log_error(f"堆栈未找到: {name}")
        log_info(f"  预期路径: {stack_file}")
        _list_available_stacks(stacks_dir)
        return

    # ── Parse JSON ──────────────────────────────────────────
    try:
        data = json.loads(stack_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        log_error(f"读取堆栈文件失败: {stack_file}")
        log_error(f"  {exc}")
        return

    domains = data.get("domains", [])
    if not domains:
        log_error(f"堆栈 '{name}' 中未找到 domain 定义")
        log_info(f"预期堆栈 JSON 包含 'domains' 数组，例如:")
        log_info(f'  {{ "domains": ["game-dev/unity", "game-dev/unreal"] }}')
        return

    log_info(f"正在加载堆栈: {name}")

    # ── Activate each domain ────────────────────────────────
    # Lazy import to avoid circular dependency with cli_activate
    from vibe_stack.cli import cli_activate  # fmt: skip

    for domain in domains:
        cli_activate.cmd_activate(
            domains=[domain],
            vibe_home=vibe_home,
            project_root=project_root,
        )

    log_ok(f"堆栈 '{name}' 已激活")


def _list_available_stacks(stacks_dir: Path) -> None:
    """Print available stack files to stdout."""
    print()
    print("可用堆栈:")

    if stacks_dir.is_dir():
        stack_files = sorted(stacks_dir.glob("*.json"))
    else:
        stack_files = []

    if stack_files:
        for stack_file in stack_files:
            name = stack_file.stem
            try:
                data = json.loads(stack_file.read_text(encoding="utf-8"))
                desc = data.get("description", "")
                if desc:
                    print(f"  {name:20s} — {desc}")
                else:
                    print(f"  {name}")
            except (json.JSONDecodeError, OSError):
                print(f"  {name}")
    else:
        print("  (空 — stacks/ 目录为空或不存在)")
        print()
        print("  创建堆栈: 添加 JSON 文件到:")
        print(f"    {stacks_dir / '<name>.json'}")
        print('    例如: { "domains": ["game-dev/unity", "game-dev/unreal"] }')
