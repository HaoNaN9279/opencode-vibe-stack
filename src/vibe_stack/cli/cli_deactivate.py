"""vibe-stack deactivate command — remove domain configuration from a project.

Ports the ``deactivate.sh`` shell script logic into pure Python.

For each domain:
  1. Read link entries from the activation manifest.
  2. Remove every symlinked file listed in the manifest (fallback: scan dirs).
  3. Deactivate domain MCP entries from ``oh-my-openagent.jsonc``.
  4. Remove domain rules instruction from ``opencode.json`` if no rules remain.
  5. Remove skills path from ``opencode.json`` if no skills remain.
  6. Clean up ``oh-my-openagent.jsonc`` (remove if empty).
  7. Update the activation manifest.
  8. Clean up empty subdirectories under ``.opencode/``.
"""

from __future__ import annotations

from pathlib import Path

from vibe_stack import config
from vibe_stack import manifest
from vibe_stack import mcp
from vibe_stack import symlinks
from vibe_stack.constants import OPECODE_CONFIG_NAME, VIBE_STACK_DIR_TYPES
from vibe_stack.utils import log_error, log_info, log_ok, log_warn


def cmd_deactivate(
    vibe_home: Path,
    project_root: Path,
    domains: list[str],
) -> None:
    """停用一个或多个领域配置。

    Parameters
    ----------
    vibe_home:
        Vibe-stack 仓库根路径。
    project_root:
        用户项目的根目录（包含 ``.opencode/``）。
    domains:
        要停用的领域键名列表（格式: ``"category/name"``，如 ``"dcc/blender"``）。
    """
    opencode_path = project_root / ".opencode" / OPECODE_CONFIG_NAME

    for arg in domains:
        # ── 解析 domain key ────────────────────────────────────────
        parts = arg.split("/", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            log_error(f"无效的领域格式: '{arg}'，请使用 category/name 格式（如 dcc/blender）")
            continue

        category, domain_name = parts
        domain_key = f"{category}/{domain_name}"
        domain_root = vibe_home / "domains" / category / domain_name

        if not domain_root.is_dir():
            log_warn(f"领域目录不存在，跳过: {domain_root}")
            continue

        log_info(f"正在停用 {domain_key} ...")
        removed_any = False

        # ── 1a. 从清单中获取链接 ────────────────────────────────────
        links = manifest.get_links(project_root, domain_key)

        if links:
            # ── 1b. 删除所有已记录的符号链接文件 ────────────────────
            for dest_rel, src_rel in links.items():
                link_path = project_root / ".opencode" / dest_rel
                try:
                    symlinks.remove_link(link_path)
                    removed_any = True
                except OSError as e:
                    log_warn(f"无法删除链接 {dest_rel}: {e}")

        else:
            # ── 2. 回退：扫描符号链接目录 ───────────────────────────
            removed_any = _fallback_remove_links(project_root, domain_key, vibe_home)

        # ── 1c. 停用领域 MCP 配置 ──────────────────────────────────
        mcp.deactivate_mcp_domain(project_root, domain_key, domain_root)

        # ── 1d. 移除 opencode.json 中的领域规则指令 ──────────────
        _remove_rules_if_empty(project_root, opencode_path)

        # ── 1e. 如果 skills 目录为空则移除路径 ─────────────────────
        _remove_skills_if_empty(project_root, opencode_path)

        # ── 1f. 清理 OMO 配置 ──────────────────────────────────────
        mcp.deactivate_omo_config(project_root)

        # ── 1g. 从激活清单中移除该领域 ─────────────────────────────
        manifest.remove_domain(project_root, domain_key)

        # ── 3. 清理空的子目录 ──────────────────────────────────────
        _cleanup_empty_subdirs(project_root)

        if removed_any:
            log_ok(f"已停用 {domain_key}")
        else:
            log_warn(f"{domain_key} 未找到任何链接")


# ── 内部辅助函数 ───────────────────────────────────────────────────────


def _remove_rules_if_empty(project_root: Path, opencode_path: Path) -> None:
    """如果 ``.opencode/rules/`` 目录为空则移除 instructions 条目。"""
    rules_dir = project_root / ".opencode" / "rules"
    if not rules_dir.is_dir() or not _dir_has_entries(rules_dir):
        config.array_remove(
            opencode_path,
            "instructions",
            ".opencode/rules/*.md",
        )


def _remove_skills_if_empty(project_root: Path, opencode_path: Path) -> None:
    """如果 ``.opencode/skills/`` 目录为空则移除 skills.paths 条目。"""
    skills_dir = project_root / ".opencode" / "skills"
    if not skills_dir.is_dir() or not _dir_has_entries(skills_dir):
        config.nested_array_remove(
            opencode_path,
            "skills",
            "paths",
            '"skills"',
        )


def _fallback_remove_links(
    project_root: Path, domain_key: str, vibe_home: Path
) -> bool:
    """回退模式：扫描 ``.opencode/<type>/`` 目录，删除以领域前缀开头的链接。

    当激活清单中不包含该领域的链接条目时使用（旧版迁移场景）。

    对于非 tools 类型，通过前缀 ``{category}_{name}`` 匹配；
    对于 tools 类型，目录保持原名（无前缀），通过 target 路径归属判断。
    """
    import os

    removed = False
    prefix = domain_key.replace("/", "_")
    parts = domain_key.split("/", 1)
    dot_opencode = project_root / ".opencode"
    domain_root = vibe_home / "domains" / parts[0] / parts[1]

    for sub in VIBE_STACK_DIR_TYPES:
        sub_dir = dot_opencode / sub
        if not sub_dir.is_dir():
            continue

        for item in list(sub_dir.iterdir()):
            if not _is_link_or_junction(item):
                continue

            if sub == "mcp" and item.suffix == ".json":
                continue

            if sub == "tools":
                # Files: match by prefix; dirs: match by target path
                if item.name.startswith(prefix):
                    pass  # Matched by prefix
                elif item.is_dir():
                    # Directory without prefix — resolve target to check ownership
                    try:
                        target_str = os.readlink(str(item))
                    except (OSError, NotImplementedError, AttributeError):
                        continue
                    try:
                        Path(target_str).relative_to(domain_root / "tools")
                    except ValueError:
                        continue  # Not from this domain
                else:
                    continue  # Non-prefixed file, not ours
            else:
                # Other types: prefix matching
                if not item.name.startswith(prefix):
                    continue

            try:
                symlinks.remove_link(item)
                removed = True
            except OSError as e:
                log_warn(f"无法删除 {item}: {e}")

    return removed


def _cleanup_empty_subdirs(project_root: Path) -> None:
    """删除 ``.opencode/`` 下空的子目录。"""
    dot_opencode = project_root / ".opencode"
    if not dot_opencode.is_dir():
        return

    for sub in VIBE_STACK_DIR_TYPES:
        sub_dir = dot_opencode / sub
        if sub_dir.is_dir() and not _dir_has_entries(sub_dir):
            try:
                sub_dir.rmdir()
            except OSError:
                pass


def _dir_has_entries(path: Path) -> bool:
    """检查目录是否包含任何条目（包括符号链接和 junction）。"""
    try:
        for _ in path.iterdir():
            return True
    except OSError:
        pass
    return False


def _is_link_or_junction(path: Path) -> bool:
    """检查路径是否为符号链接或 junction（跨平台）。

    在 Windows 上，NTFS junction 不会被 ``is_symlink()`` 识别，
    因此通过 ``os.path.islink()`` 和 ``os.path.isjunction()``
    （Python 3.12+）综合判断。
    """
    import os

    if path.is_symlink():
        return True
    # Python 3.12+ has os.path.isjunction
    if hasattr(os.path, "isjunction") and os.path.isjunction(str(path)):
        return True
    return False
