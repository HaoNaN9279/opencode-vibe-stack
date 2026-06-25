"""MCP activation/deactivation module for vibe-stack.

Ports the MCP merge logic from shell scripts (mcp.sh, mcp-config.sh)
to pure Python using the config and resolver modules.

Key concepts
------------
* **Core MCPs** — global MCP servers resolved from ``core/mcp/*.json``,
  written to ``~/.config/opencode/opencode.json`` with ``vibe:core-`` prefix.
* **Domain MCPs** — per-domain MCP servers resolved from
  ``domains/{key}/mcp/*.json``, written to
   ``.opencode/opencode.json`` with ``vibe:`` prefix.
* **Registry** — user-level mapping of MCP server names to executables
  (``~/.config/opencode/vibe-stack-mcp.jsonc``).
"""

from __future__ import annotations

from pathlib import Path

from vibe_stack import config
from vibe_stack import resolver
from vibe_stack.constants import (
    MCP_CORE_PREFIX,
    MCP_DOMAIN_PREFIX,
    OPENCODE_CONFIG_DIR,
    OMO_CONFIG_NAME,
    OPECODE_CONFIG_NAME,
)
from vibe_stack.utils import log_error, log_info, log_ok, log_warn


# ── Schema constants ───────────────────────────────────────────────

_OPENCODE_SCHEMA = "https://opencode.ai/config.json"
_OMO_SCHEMA = "https://oh-my-openagent.com/config.json"


# ── Error handler ──────────────────────────────────────────────────

def _backup_and_fail(path: Path, error: Exception) -> None:
    """当配置文件解析失败时，备份原文件并报错退出。
    
    绝不静默覆盖已有的用户配置。
    """
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_suffix(f"{path.suffix}.backup-{timestamp}")
    
    try:
        shutil.copy2(path, backup_path)
    except OSError:
        backup_path = None
    
    log_error(f"配置文件解析失败: {path}")
    log_error(f"  错误详情: {error}")
    if backup_path:
        log_error(f"  原文件已备份到: {backup_path}")
    log_error(f"  请手动修复 JSON 语法后重试。")
    raise SystemExit(1)


# ── Default config builders ────────────────────────────────────────

def _default_opencode_config() -> dict:
    """Create a minimal default ``opencode.json`` config dict."""
    return {
        "$schema": _OPENCODE_SCHEMA,
        "instructions": ["~/.config/opencode/rules/*.md"],
    }


def _default_omo_config() -> dict:
    """Create a minimal default ``oh-my-openagent.jsonc`` config dict."""
    return {
        "$schema": _OMO_SCHEMA,
        "agent_definitions": ["agents/"],
    }


def _default_project_opencode_config() -> dict:
    """Create a minimal default project-level ``opencode.json`` config dict.

    Unlike :func:`_default_opencode_config`, this does **not** include
    ``instructions`` — that is a user-level concern only.
    """
    return {"$schema": _OPENCODE_SCHEMA}


# ── Core MCP activation ───────────────────────────────────────────

def activate_mcp_core(vibe_home: Path) -> None:
    """Resolve and write **Core MCPs** to user-level ``opencode.json``.

    1. Resolve core MCP entries via :func:`resolver.resolve_core_mcp`.
    2. Read existing ``~/.config/opencode/opencode.json`` — create default
       if missing.
    3. Merge resolved entries with ``vibe:core-`` prefix via
       :func:`config.merge_mcp_block`.
    4. Write back with :func:`config.write_jsonc`.

    Parameters
    ----------
    vibe_home:
        vibe-stack repository root path.
    """
    # 1. Resolve core MCP entries (self-contained, no registry needed)
    try:
        resolved = resolver.resolve_core_mcp(vibe_home)
    except Exception as e:
        log_error(f"Core MCP 解析失败: {e}")
        return

    if not resolved:
        log_info("没有需要激活的 Core MCP 服务器")
        return

    # 3. Read existing opencode.json or create default
    opencode_path = OPENCODE_CONFIG_DIR / OPECODE_CONFIG_NAME
    if opencode_path.is_file():
        try:
            cfg = config.read_jsonc(opencode_path)
        except Exception as e:
            _backup_and_fail(opencode_path, e)
            return  # unreachable, but safe
    else:
        cfg = _default_opencode_config()

    # 4. Merge core MCP entries (prefix "vibe:core-" isolates from domain entries)
    config.merge_mcp_block(cfg, resolved, prefix=MCP_CORE_PREFIX)

    # 5. Write back
    config.write_jsonc(opencode_path, cfg)

    for name in resolved:
        log_ok(f"  + {name}")
    log_ok(f"Core MCP activated -> {opencode_path}")


# ── Domain MCP activation ─────────────────────────────────────────

def activate_mcp_domain(
    vibe_home: Path,
    project_root: Path,
    domain_key: str,
    domain_root: Path,
) -> None:
    """Resolve and write **domain MCPs** to project-level ``opencode.json``.

    1. Resolve domain MCP entries via :func:`resolver.resolve_domain_mcp`.
    2. If no MCPs found for this domain, return early.
    3. Read existing ``.opencode/opencode.json`` — create default
       if missing.
    4. Merge resolved entries with ``vibe:`` prefix via ``mcp.update()``
       (additive — only replaces matching keys, preserving entries from
       other domains).
    5. Write back.

    Parameters
    ----------
    vibe_home:
        vibe-stack repository root path.
    project_root:
        Root directory of the user's project (where ``.opencode/`` lives).
    domain_key:
        Domain identifier in ``category/name`` format (e.g. ``"ai/data-forge"``).
    domain_root:
        Absolute path to the domain directory inside the vibe-stack repo
        (e.g. ``vibe_home / "domains" / "ai" / "data-forge"``).
    """
    # 1. Resolve domain MCP entries (self-contained, no registry needed)
    try:
        resolved = resolver.resolve_domain_mcp(vibe_home, domain_key, project_root)
    except Exception as e:
        log_error(f"Domain MCP 解析失败 ({domain_key}): {e}")
        return

    if not resolved:
        return

    # 3. Read existing opencode.json or create default
    opencode_path = project_root / ".opencode" / OPECODE_CONFIG_NAME
    if opencode_path.is_file():
        try:
            cfg = config.read_jsonc(opencode_path)
        except Exception as e:
            _backup_and_fail(opencode_path, e)
            return  # unreachable, but safe
    else:
        cfg = _default_project_opencode_config()

    # 4. Merge domain MCP entries with vibe: prefix (additive update)
    mcp_block = cfg.setdefault("mcp", {})
    if not isinstance(mcp_block, dict):
        mcp_block = {}
        cfg["mcp"] = mcp_block
    mcp_block.update(resolved)

    # 5. Write back
    config.write_jsonc(opencode_path, cfg)

    for name in resolved:
        log_ok(f"  + {name}")
    log_ok(f"Domain MCP activated -> {opencode_path}")


# ── Domain MCP deactivation ───────────────────────────────────────

def deactivate_mcp_domain(
    project_root: Path, domain_key: str, domain_root: Path
) -> None:
    """Remove domain MCP entries from project ``opencode.json``.

    1. Read ``.opencode/opencode.json``.
    2. Scan domain's ``mcp/*.json`` to discover server names.
    3. Remove every ``vibe:{name}`` key from the config's ``mcp`` block.
    4. Write back.

    Parameters
    ----------
    project_root:
        Root directory of the user's project.
    domain_key:
        Domain identifier (used only for log messages).
    domain_root:
        Absolute path to the domain directory inside the vibe-stack repo.
    """
    opencode_path = project_root / ".opencode" / OPECODE_CONFIG_NAME
    if not opencode_path.is_file():
        return

    # Collect server names declared in the domain's MCP JSON files
    mcp_dir = domain_root / "mcp"
    if not mcp_dir.is_dir():
        return

    server_names: list[str] = []
    for mcp_file in sorted(mcp_dir.glob("*.json")):
        try:
            data = config.read_jsonc(mcp_file)
        except Exception:
            continue
        mcp_block = data.get("mcp", {})
        if isinstance(mcp_block, dict):
            server_names.extend(mcp_block.keys())

    if not server_names:
        return

    # Read the current project config
    try:
        cfg = config.read_jsonc(opencode_path)
    except Exception as e:
        log_error(f"无法读取 {opencode_path}: {e}")
        return

    mcp: dict = cfg.setdefault("mcp", {})
    if not isinstance(mcp, dict):
        return

    # Remove vibe:-prefixed entries that belong to this domain
    removed_any = False
    for name in server_names:
        key = f"{MCP_DOMAIN_PREFIX}{name}"
        if key in mcp:
            del mcp[key]
            removed_any = True
            log_info(f"    - {key}")

    if not removed_any:
        return

    config.write_jsonc(opencode_path, cfg)
    log_ok(f"Domain MCP deactivated: {domain_key}")


# ── OMO config lifecycle ──────────────────────────────────────────

def activate_omo_config(project_root: Path) -> None:
    """Create ``.opencode/oh-my-openagent.jsonc`` with basic schema if
    it does not already exist.

    The default config declares ``agent_definitions: ["agents/"]`` so
    that OhMyOpenAgent auto-discovers agent definitions.
    """
    omo_path = project_root / ".opencode" / OMO_CONFIG_NAME

    # Ensure the .opencode/ directory exists
    omo_path.parent.mkdir(parents=True, exist_ok=True)

    if omo_path.is_file():
        return

    cfg = _default_omo_config()
    config.write_jsonc(omo_path, cfg)
    log_ok(f"Created {omo_path}")


def deactivate_omo_config(project_root: Path) -> None:
    """Remove the project ``oh-my-openagent.jsonc`` when no agents or
    MCP entries remain (i.e. the config is an empty skeleton).

    Also cleans up the ``.opencode/`` directory if it becomes empty.
    """
    omo_path = project_root / ".opencode" / OMO_CONFIG_NAME
    if not omo_path.is_file():
        return

    try:
        cfg = config.read_jsonc(omo_path)
    except Exception as e:
        log_warn(f"无法读取 {omo_path}: {e}")
        return

    has_agents = bool(cfg.get("agent_definitions"))
    has_mcp = bool(cfg.get("mcp"))

    if not has_agents and not has_mcp:
        omo_path.unlink()
        log_ok(f"Removed empty {OMO_CONFIG_NAME}")

        # Clean up .opencode/ directory if empty
        dot_dir = omo_path.parent
        if dot_dir.is_dir():
            try:
                _cleanup_empty_dir(dot_dir)
            except OSError:
                pass


# ── Internal helpers ──────────────────────────────────────────────

def _cleanup_empty_dir(path: Path) -> None:
    """Remove *path* if it contains no files, recursing into subdirectories."""
    if not path.is_dir():
        return
    # Recurse into subdirectories first
    for child in sorted(path.iterdir()):
        if child.is_dir():
            _cleanup_empty_dir(child)
    # Remove the directory itself if now empty
    if not any(path.iterdir()):
        path.rmdir()
