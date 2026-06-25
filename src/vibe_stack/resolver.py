"""MCP 配置解析器模块（自包含版本）。

直接从 JSON 声明文件中读取 MCP 配置，不再依赖外部注册表。
支持 ``${MCP_LINK_DIR}`` 占位符解析为绝对路径。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from vibe_stack import config
from vibe_stack.constants import (
    MCP_CORE_PREFIX,
    MCP_DOMAIN_PREFIX,
    MCP_LINK_DIR_PLACEHOLDER,
    OPENCODE_CONFIG_DIR,
)
from vibe_stack.utils import log_info, log_warn


# ── Internal helpers ──────────────────────────────────────────────


def _resolve_placeholder(value: str, link_dir: str) -> str:
    """Replace ``${MCP_LINK_DIR}`` in *value* with *link_dir*."""
    return value.replace(MCP_LINK_DIR_PLACEHOLDER, link_dir)


def _resolve_dict_values(
    entry: dict[str, Any],
    link_dir: str | None,
) -> dict[str, Any]:
    """Resolve ``${MCP_LINK_DIR}`` in command / cwd / env of *entry*.

    Only performs replacement when *link_dir* is not ``None``.
    """
    resolved = dict(entry)

    if link_dir is None:
        return resolved

    # Resolve command (list[str])
    command = resolved.get("command")
    if isinstance(command, list):
        resolved["command"] = [
            _resolve_placeholder(s, link_dir) if isinstance(s, str) else s
            for s in command
        ]

    # Resolve cwd (str)
    cwd = resolved.get("cwd")
    if isinstance(cwd, str):
        resolved["cwd"] = _resolve_placeholder(cwd, link_dir)

    # Resolve env values (dict[str, str])
    env = resolved.get("env")
    if isinstance(env, dict):
        resolved["env"] = {
            k: _resolve_placeholder(v, link_dir) if isinstance(v, str) else v
            for k, v in env.items()
        }

    return resolved


# ── Self-contained MCP resolver ───────────────────────────────────


def resolve_mcp_self_contained(
    mcp_file: Path,
    link_dir: str | None,
) -> dict[str, dict[str, Any]]:
    """从 JSON 声明文件解析 MCP 服务器配置，不依赖外部注册表。

    替换 ``${MCP_LINK_DIR}`` 占位符为实际路径，支持本地和远程两种 MCP 类型。

    Args:
        mcp_file: MCP JSON 声明文件路径
        link_dir: ``${MCP_LINK_DIR}`` 的替换值（绝对路径字符串），
            为 ``None`` 时不执行替换

    Returns:
        未加前缀的 server_name → config 映射字典

    JSON 格式支持:
        - ``mcpServers`` 键（优先）或 ``mcp`` 键（回退兼容）
        - ``type: "remote"`` → 透传声明，默认 ``enabled: true``
        - ``type: "local"`` 或缺失 → 解析占位符，默认 ``type: "local"`` 和 ``enabled: true``
    """
    result: dict[str, dict[str, Any]] = {}

    try:
        data = config.read_jsonc(mcp_file)
    except Exception as e:
        log_warn(f"无法读取 MCP 配置文件 {mcp_file}: {e}")
        return result

    # 优先 mcpServers，回退到 mcp
    mcp_block = data.get("mcpServers")
    if not isinstance(mcp_block, dict) or not mcp_block:
        mcp_block = data.get("mcp", {})
    if not isinstance(mcp_block, dict) or not mcp_block:
        return result

    for server_name, declaration in mcp_block.items():
        if not isinstance(declaration, dict):
            continue

        mcp_type = declaration.get("type", "local")

        if mcp_type == "remote":
            # 远程 MCP：透传原始声明
            resolved: dict[str, Any] = dict(declaration)
            resolved.setdefault("enabled", True)
        else:
            # 本地 MCP（含 type 缺失默认情况）：解析占位符
            resolved = _resolve_dict_values(declaration, link_dir)
            resolved["type"] = "local"
            resolved.setdefault("enabled", True)

        result[server_name] = resolved
        log_info(f"已解析 MCP: {server_name} ({mcp_type})")

    return result


# ── Core MCP resolution ──────────────────────────────────────────


def resolve_core_mcp(vibe_home: Path) -> dict[str, dict[str, Any]]:
    """解析所有 core MCP 服务器，不再依赖外部注册表。

    扫描 ``core/mcp/*.json``，若存在同名伴随文件夹则将其路径作为
    ``${MCP_LINK_DIR}`` 的替换值。结果以 ``vibe:core-`` 前缀命名。

    Args:
        vibe_home: vibe-stack 仓库根路径

    Returns:
        ``{"vibe:core-codegraph": {...}, ...}``
    """
    result: dict[str, dict[str, Any]] = {}
    mcp_dir = vibe_home / "core" / "mcp"

    if not mcp_dir.is_dir():
        log_warn("core/mcp/ 目录不存在，跳过 core MCP 解析")
        return result

    for mcp_file in sorted(mcp_dir.glob("*.json")):
        mcp_name = mcp_file.stem

        # 检测伴随文件夹（core/mcp/{name}/）
        companion_dir = mcp_file.with_suffix("")
        if companion_dir.is_dir():
            link_dir: str | None = str(
                OPENCODE_CONFIG_DIR / "mcp" / mcp_name
            )
        else:
            link_dir = None

        resolved = resolve_mcp_self_contained(mcp_file, link_dir)

        for server_name, server_config in resolved.items():
            key = f"{MCP_CORE_PREFIX}{server_name}"
            result[key] = server_config

    return result


# ── Domain MCP resolution ────────────────────────────────────────


def resolve_domain_mcp(
    vibe_home: Path,
    domain_key: str,
    project_root: Path,
) -> dict[str, dict[str, Any]]:
    """解析指定领域的所有 MCP 服务器，不再依赖外部注册表。

    扫描 ``domains/{domain_key}/mcp/*.json``，若存在同名伴随文件夹则将其
    路径作为 ``${MCP_LINK_DIR}`` 的替换值。结果以 ``vibe:`` 前缀命名。

    Args:
        vibe_home: vibe-stack 仓库根路径
        domain_key: 领域标识（格式 ``"category/name"``，如 ``"ai/data-forge"``）
        project_root: 用户项目根目录（用于构建 link_dir 绝对路径）

    Returns:
        ``{"vibe:server-name": {...}, ...}``
        若领域无 mcp/ 目录则返回空 dict
    """
    result: dict[str, dict[str, Any]] = {}
    mcp_dir = vibe_home / "domains" / domain_key / "mcp"

    if not mcp_dir.is_dir():
        return result

    # 解析 domain key 为 category / name
    parts = domain_key.split("/", 1)
    category = parts[0]
    domain_name = parts[1] if len(parts) > 1 else parts[0]

    for mcp_file in sorted(mcp_dir.glob("*.json")):
        mcp_name = mcp_file.stem

        # 检测伴随文件夹（domains/{domain_key}/mcp/{name}/）
        companion_dir = mcp_file.with_suffix("")
        if companion_dir.is_dir():
            link_dir: str | None = str(
                project_root
                / ".opencode"
                / "mcp"
                / f"{category}_{domain_name}_{mcp_name}"
            )
        else:
            link_dir = None

        resolved = resolve_mcp_self_contained(mcp_file, link_dir)

        for server_name, server_config in resolved.items():
            key = f"{MCP_DOMAIN_PREFIX}{server_name}"
            result[key] = server_config

    return result


# ── Legacy (deprecated) ──────────────────────────────────────────
# @deprecated — 旧版注册表依赖解析器，自包含版本已取代。
#             保留用于参考，RegistryError 和 get_entry 导入已移除。
#
# def resolve_mcp(name: str, registry: dict, declaration: dict) -> dict:
#     """将注册表条目与声明合并，解析为 opencode MCP 格式。
#
#     Args:
#         name: MCP 服务器名称
#         registry: 完整注册表 dict（含 ``mcp_registry`` 键）
#         declaration: 按服务器名称索引的声明 dict
#
#     Returns:
#         opencode 格式的 MCP 配置
#
#     Raises:
#         RegistryError: 注册表中缺少该服务器，或 command 为空
#     """
#     entry = get_entry(registry, name)
#     if entry is None:
#         raise RegistryError(
#             f"MCP 服务器 '{name}' 未在注册表中找到，"
#             f"请在 {VIBE_STACK_MCP_REGISTRY_PATH} 中添加该条目"
#         )
#
#     command = entry.get("command")
#     if not command:
#         raise RegistryError(
#             f"MCP 服务器 '{name}' 的 command 未配置，"
#             f"请编辑 {VIBE_STACK_MCP_REGISTRY_PATH} 填写可执行文件路径"
#         )
#
#     decl = declaration.get(name, {})
#
#     if isinstance(command, str):
#         cmd_list: list[str] = [command]
#     else:
#         cmd_list = list(command)
#
#     reg_args = entry.get("args", [])
#     if reg_args:
#         cmd_list.extend(reg_args)
#
#     decl_args = decl.get("args", [])
#     if decl_args:
#         cmd_list.extend(decl_args)
#
#     env: dict[str, str] = {}
#     reg_env = entry.get("env")
#     if reg_env:
#         env.update(reg_env)
#     decl_env = decl.get("env")
#     if decl_env:
#         env.update(decl_env)
#
#     result: dict[str, Any] = {
#         "type": "local",
#         "command": cmd_list,
#         "enabled": decl.get("enabled", True),
#     }
#
#     timeout = decl.get("timeout")
#     if timeout is not None:
#         result["timeout"] = timeout
#
#     cwd = entry.get("cwd")
#     if cwd:
#         result["cwd"] = cwd
#
#     if env:
#         result["env"] = env
#
#     return result
#
#
# @deprecated — 旧版注册表依赖函数，自包含版本已取代。
#
# def resolve_core_mcp(vibe_home: Path, registry: dict) -> dict:
#     ...
#
#
# @deprecated — 旧版注册表依赖函数，自包含版本已取代。
#
# def resolve_domain_mcp(vibe_home: Path, domain_key: str, registry: dict) -> dict:
#     ...
