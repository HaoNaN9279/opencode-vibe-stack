"""激活清单文件 .vibe-stack-active.json 的读写操作。"""

import json
from pathlib import Path

from vibe_stack.constants import ACTIVE_MANIFEST_NAME

_MANIFEST_VERSION = 1


def _manifest_path(project_root: Path) -> Path:
    """返回 .vibe-stack-active.json 的完整路径。"""
    return project_root / ".opencode" / ACTIVE_MANIFEST_NAME


def read_manifest(project_root: Path) -> dict:
    """读取激活清单，文件不存在或格式错误时返回默认结构。"""
    path = _manifest_path(project_root)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "version" in data:
            return data
        return {"version": _MANIFEST_VERSION, "domains": {}}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"version": _MANIFEST_VERSION, "domains": {}}


def write_manifest(project_root: Path, data: dict) -> None:
    """写入激活清单。"""
    path = _manifest_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def has_domain(project_root: Path, domain_key: str) -> bool:
    """检查指定 domain 是否在激活清单中。"""
    data = read_manifest(project_root)
    return domain_key in data.get("domains", {})


def add_domain(project_root: Path, domain_key: str, links: dict) -> None:
    """向激活清单中添加 domain 及其链接映射。"""
    data = read_manifest(project_root)
    domains = data.setdefault("domains", {})
    domains[domain_key] = {"links": links}
    write_manifest(project_root, data)


def remove_domain(project_root: Path, domain_key: str) -> bool:
    """从激活清单中移除指定 domain。

    如果移除后 domains 为空则删除清单文件。
    返回 True 表示 domain 被成功移除，False 表示不存在。
    """
    data = read_manifest(project_root)
    domains = data.get("domains", {})
    if domain_key not in domains:
        return False

    del domains[domain_key]
    # 按约定设为空 dict，以便检查是否应删除文件
    data["domains"] = domains

    if not domains:
        path = _manifest_path(project_root)
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
    else:
        write_manifest(project_root, data)

    return True


def get_links(project_root: Path, domain_key: str) -> dict:
    """返回指定 domain 的链接映射，不存在时返回空 dict。"""
    data = read_manifest(project_root)
    domain = data.get("domains", {}).get(domain_key, {})
    return domain.get("links", {})


def list_active_domains(project_root: Path) -> list[str]:
    """返回所有已激活 domain 的键名列表。"""
    data = read_manifest(project_root)
    return list(data.get("domains", {}).keys())
