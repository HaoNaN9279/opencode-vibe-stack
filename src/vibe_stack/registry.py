"""MCP 注册表读写与模板生成模块。

管理用户级 MCP 注册表文件（~/.config/opencode/vibe-stack-mcp.jsonc），
将 MCP 服务器名称映射到其可执行路径和运行参数。

注册表 schema::

    {
        "version": 1,
        "mcp_registry": {
            "server-name": {
                "command": "/path/to/executable",
                "args"?: [...],
                "cwd"?: "/working/dir",
                "env"?: {"KEY": "VALUE"}
            }
        }
    }
"""

from __future__ import annotations

import json
from pathlib import Path

from vibe_stack.config import read_jsonc, write_jsonc
from vibe_stack.constants import VIBE_STACK_MCP_REGISTRY_PATH
from vibe_stack.utils import log_info, log_warn

# 注册表 schema 版本
REGISTRY_VERSION = 1


# ── 核心读写 ──────────────────────────────────────────────────────

def read_registry(path: Path) -> dict:
    """读取 MCP 注册表 JSONC 文件。

    文件缺失或格式错误时返回含空 mcp_registry 的默认结构。

    Returns:
        ``{"version": REGISTRY_VERSION, "mcp_registry": {}}``
    """
    try:
        data = read_jsonc(path)
        if isinstance(data, dict):
            return data
    except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError):
        pass
    return {"version": REGISTRY_VERSION, "mcp_registry": {}}


def write_registry(path: Path, data: dict) -> None:
    """将注册表数据写入 JSON 文件。

    使用 ``json.dumps(data, indent=2)`` 格式化输出，
    自动创建父目录。
    """
    write_jsonc(path, data)


def read_registry_from_home(vibe_home: Path) -> dict:
    """从默认路径 ``~/.config/opencode/vibe-stack-mcp.jsonc`` 读取注册表。

    Args:
        vibe_home: vibe-stack 仓库根路径（保留参数以保持 API 一致性）
    """
    return read_registry(VIBE_STACK_MCP_REGISTRY_PATH)


# ── 条目查询 ──────────────────────────────────────────────────────

def get_entry(registry: dict, name: str) -> dict | None:
    """按名称查找注册表中的 MCP 服务器条目。

    Args:
        registry: 完整注册表 dict（含 ``mcp_registry`` 键）
        name: MCP 服务器名称

    Returns:
        条目 dict ``{"command", "args"?, "cwd"?, "env"?}``，不存在则返回 None
    """
    mcp_registry = registry.get("mcp_registry", {})
    if not isinstance(mcp_registry, dict):
        return None
    return mcp_registry.get(name)


# ── 模板生成 ──────────────────────────────────────────────────────

def generate_template(vibe_home: Path) -> dict:
    """扫描所有 MCP JSON 配置文件，生成注册表模板。

    扫描 ``core/mcp/*.json`` 和 ``domains/*/*/mcp/*.json``，
    提取每个 MCP 配置文件中的服务器名称，生成模板条目。
    模板中每个条目的 ``command`` 为空字符串，并附带 ``_hint`` 引导提示。

    Returns:
        模板注册表 dict::

            {
                "version": 1,
                "mcp_registry": {
                    "data-forge": {"command": "", "_hint": "填写 data-forge 可执行文件的路径"},
                    ...
                }
            }
    """
    entries: dict[str, dict] = {}

    # 扫描 core/mcp/*.json
    for mcp_file in sorted(vibe_home.glob("core/mcp/*.json")):
        _extract_template_entries(mcp_file, entries)

    # 扫描 domains/*/*/mcp/*.json
    for mcp_file in sorted(vibe_home.glob("domains/*/*/mcp/*.json")):
        _extract_template_entries(mcp_file, entries)

    log_info(f"模板生成完成：发现 {len(entries)} 个 MCP 服务器")
    return {"version": REGISTRY_VERSION, "mcp_registry": entries}


def _extract_template_entries(mcp_file: Path, entries: dict[str, dict]) -> None:
    """从单个 MCP JSON 配置文件中提取服务器名称，填充模板条目。"""
    try:
        data = read_jsonc(mcp_file)
    except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError) as e:
        log_warn(f"无法解析 MCP 配置文件 {mcp_file}: {e}")
        return

    mcp_block = data.get("mcp", {})
    if not isinstance(mcp_block, dict):
        return

    for server_name in mcp_block:
        if server_name not in entries:
            entries[server_name] = {
                "command": "",
                "_hint": f"填写 {server_name} 可执行文件的路径",
            }


# ── 验证 ──────────────────────────────────────────────────────────

def validate_registry(registry: dict) -> list[str]:
    """验证注册表，返回缺失 ``command`` 的服务器名称列表。

    检查 ``registry`` 是否包含 ``mcp_registry`` 键，
    以及每个条目是否具备有效的 ``command`` 值（非空且非 None）。

    Returns:
        缺失 command 的服务器名称列表
    """
    mcp_registry = registry.get("mcp_registry", {})
    if not isinstance(mcp_registry, dict):
        log_warn("注册表缺少有效的 mcp_registry 键")
        return []

    missing: list[str] = []
    for name, entry in mcp_registry.items():
        if not isinstance(entry, dict):
            missing.append(name)
            continue
        command = entry.get("command")
        if not command:  # None 或空字符串
            missing.append(name)

    return missing


# ── 合并 ──────────────────────────────────────────────────────────

def merge_into_registry(registry_path: Path, new_entries: dict) -> int:
    """将新条目合并到注册表中，不覆盖已有条目。

    适用于 core-update 场景：当域中新增 MCP 服务器时，
    将新条目加入用户注册表，但保留用户已有的 command 配置。

    Args:
        registry_path: 注册表文件路径
        new_entries: 待合并的新条目 dict ``{"server_name": {entry}}``

    Returns:
        新增的条目数量
    """
    registry = read_registry(registry_path)
    mcp_registry = registry.setdefault("mcp_registry", {})

    added = 0
    for name, entry in new_entries.items():
        if name not in mcp_registry:
            mcp_registry[name] = entry
            added += 1
            log_info(f"新增注册表条目: {name}")

    if added > 0:
        write_registry(registry_path, registry)
        log_info(f"注册表已更新，新增 {added} 个条目")
    else:
        log_info("注册表无新条目需要添加")

    return added
