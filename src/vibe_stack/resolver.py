"""MCP 配置解析器模块。

将用户注册表条目与领域声明的 MCP 配置合并，输出 opencode 兼容的 MCP 格式。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from vibe_stack import config
from vibe_stack import RegistryError
from vibe_stack.constants import MCP_CORE_PREFIX, MCP_DOMAIN_PREFIX, VIBE_STACK_MCP_REGISTRY_PATH
from vibe_stack.registry import get_entry
from vibe_stack.utils import log_info, log_warn


def resolve_mcp(name: str, registry: dict, declaration: dict) -> dict:
    """将注册表条目与声明合并，解析为 opencode MCP 格式。

    Args:
        name: MCP 服务器名称
        registry: 完整注册表 dict（含 ``mcp_registry`` 键）::

            {"mcp_registry": {"server-name": {"command": "...", "args"?: [...], "cwd"?: "...", "env"?: {...}}}}}

        declaration: 按服务器名称索引的声明 dict::

            {"server-name": {"args"?: [...], "enabled"?: bool, "timeout"?: int, "env"?: {...}}}

    Returns:
        opencode 格式的 MCP 配置::

            {"type": "local", "command": [...], "enabled": true,
             "timeout": N (if set), "cwd": "..." (if set), "env": {...} (if set)}

    Raises:
        RegistryError: 注册表中缺少该服务器，或 command 为空
    """
    # 1. 查找注册表条目
    entry = get_entry(registry, name)
    if entry is None:
        raise RegistryError(
            f"MCP 服务器 '{name}' 未在注册表中找到，"
            f"请在 {VIBE_STACK_MCP_REGISTRY_PATH} 中添加该条目"
        )

    # 2. 验证 command
    command = entry.get("command")
    if not command:
        raise RegistryError(
            f"MCP 服务器 '{name}' 的 command 未配置，"
            f"请编辑 {VIBE_STACK_MCP_REGISTRY_PATH} 填写可执行文件路径"
        )

    # 3. 获取该服务器的声明
    decl = declaration.get(name, {})

    # 4. 构建 command 列表
    if isinstance(command, str):
        cmd_list: list[str] = [command]
    else:
        cmd_list = list(command)

    # 注册表 args 在前
    reg_args = entry.get("args", [])
    if reg_args:
        cmd_list.extend(reg_args)

    # 声明 args 追加在后
    decl_args = decl.get("args", [])
    if decl_args:
        cmd_list.extend(decl_args)

    # 5. 合并环境变量（注册表为 base，声明覆盖）
    env: dict[str, str] = {}
    reg_env = entry.get("env")
    if reg_env:
        env.update(reg_env)
    decl_env = decl.get("env")
    if decl_env:
        env.update(decl_env)

    # 6. 构建结果
    result: dict[str, Any] = {
        "type": "local",
        "command": cmd_list,
        "enabled": decl.get("enabled", True),
    }

    timeout = decl.get("timeout")
    if timeout is not None:
        result["timeout"] = timeout

    cwd = entry.get("cwd")
    if cwd:
        result["cwd"] = cwd

    if env:
        result["env"] = env

    return result


def resolve_core_mcp(vibe_home: Path, registry: dict) -> dict:
    """解析所有 core MCP 服务器。

    扫描 ``core/mcp/*.json``，将每个服务器解析为 opencode 格式，
    并以 ``vibe:core-`` 前缀命名。

    Args:
        vibe_home: vibe-stack 仓库根路径
        registry: 完整注册表 dict

    Returns:
        ``{"vibe:core-codegraph": {...}, ...}``
    """
    result: dict[str, dict] = {}
    mcp_dir = vibe_home / "core" / "mcp"

    if not mcp_dir.is_dir():
        log_warn("core/mcp/ 目录不存在，跳过 core MCP 解析")
        return result

    for mcp_file in sorted(mcp_dir.glob("*.json")):
        try:
            data = config.read_jsonc(mcp_file)
        except Exception as e:
            log_warn(f"无法读取 MCP 配置文件 {mcp_file}: {e}")
            continue

        mcp_block = data.get("mcp", {})
        if not isinstance(mcp_block, dict) or not mcp_block:
            continue

        for server_name in mcp_block:
            key = f"{MCP_CORE_PREFIX}{server_name}"
            try:
                resolved = resolve_mcp(server_name, registry, mcp_block)
                result[key] = resolved
                log_info(f"已解析 core MCP: {key}")
            except RegistryError as e:
                log_warn(f"跳过 core MCP '{server_name}': {e}")

    return result


def resolve_domain_mcp(vibe_home: Path, domain_key: str, registry: dict) -> dict:
    """解析指定领域的所有 MCP 服务器。

    扫描 ``domains/{category}/{name}/mcp/*.json``，
    将每个服务器解析为 opencode 格式，并以 ``vibe:`` 前缀命名。

    Args:
        vibe_home: vibe-stack 仓库根路径
        domain_key: 领域标识（格式 ``"category/name"``，如 ``"ai/data-forge"``）
        registry: 完整注册表 dict

    Returns:
        ``{"vibe:server-name": {...}, ...}``
        若领域无 mcp/ 目录则返回空 dict
    """
    result: dict[str, dict] = {}
    mcp_dir = vibe_home / "domains" / domain_key / "mcp"

    if not mcp_dir.is_dir():
        return result

    for mcp_file in sorted(mcp_dir.glob("*.json")):
        try:
            data = config.read_jsonc(mcp_file)
        except Exception as e:
            log_warn(f"无法读取 MCP 配置文件 {mcp_file}: {e}")
            continue

        mcp_block = data.get("mcp", {})
        if not isinstance(mcp_block, dict) or not mcp_block:
            continue

        for server_name in mcp_block:
            key = f"{MCP_DOMAIN_PREFIX}{server_name}"
            try:
                resolved = resolve_mcp(server_name, registry, mcp_block)
                result[key] = resolved
                log_info(f"已解析 domain MCP: {key}")
            except RegistryError as e:
                log_warn(f"跳过 domain MCP '{server_name}': {e}")

    return result
