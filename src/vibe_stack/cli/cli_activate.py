"""activate command — activate domain(s) in the current project.

Activates one or more domains by:
1. Validating the domain exists in the vibe-stack repo
2. Checking it is not already active
3. Creating per-item symlinks for each config type (rules/agents/commands/mcp/skills/tools)
4. Resolving and registering domain MCP servers
5. Adding domain rules to opencode.json instructions
6. Registering domain skills path in opencode.json
7. Ensuring the OMO config skeleton exists
8. Recording the activation in the project manifest
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from vibe_stack import DomainNotFoundError
from vibe_stack import config
from vibe_stack import manifest
from vibe_stack import mcp
from vibe_stack import registry as registry_mod
from vibe_stack import symlinks
from vibe_stack.constants import OPECODE_CONFIG_NAME, VIBE_STACK_DIR_TYPES
from vibe_stack.utils import log_error, log_info, log_ok, log_warn


def _parse_domain_key(domain: str) -> tuple[str, str, str]:
    """Parse ``"cat/name"`` into ``(category, name, domain_key)``.

    The *domain_key* is the same as the input but the prefix used for
    symlink naming replaces ``/`` with ``_``.

    Raises :class:`DomainNotFoundError` if the domain does not contain
    exactly one ``/`` separator.
    """
    parts = domain.split("/")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise DomainNotFoundError(
            f"无效的领域名 '{domain}' — 请使用 'category/name' 格式"
        )
    category, name = parts
    return category, name, domain


def _make_symlink_prefix(category: str, name: str) -> str:
    """Derive the symlink name prefix from category and domain name."""
    return f"{category}_{name}"


def _collect_links(
    domain_root: Path,
    vibe_home: Path,
    prefix: str,
) -> dict[str, str]:
    """Build the links dict for manifest recording.

    Returns a mapping of ``"{type}/{prefix}_{item}"`` →
    ``"domains/{cat}/{name}/{type}/{item}"`` (relative to *vibe_home*).
    """
    links: dict[str, str] = {}
    for type_name in VIBE_STACK_DIR_TYPES:
        src_dir = domain_root / type_name
        if not src_dir.is_dir():
            continue
        if type_name == "tools":
            # Record per-item entries for tools.
            # Directories keep original name; files get domain prefix.
            for item in sorted(src_dir.iterdir()):
                if item.is_dir():
                    link_name = item.name
                else:
                    link_name = f"{prefix}_{item.name}" if prefix else item.name
                key = f"{type_name}/{link_name}"
                try:
                    rel_src = item.relative_to(vibe_home)
                except ValueError:
                    rel_src = item
                links[key] = str(rel_src).replace("\\", "/")
        else:
            for item in sorted(src_dir.iterdir()):
                link_name = f"{prefix}_{item.name}" if prefix else item.name
                key = f"{type_name}/{link_name}"
                try:
                    rel_src = item.relative_to(vibe_home)
                except ValueError:
                    rel_src = item
                links[key] = str(rel_src).replace("\\", "/")
    return links


def cmd_activate(
    vibe_home: Path,
    project_root: Path,
    domains: list[str],
) -> None:
    """Activate one or more domains in *project_root*.

    Parameters
    ----------
    vibe_home:
        vibe-stack repository root path.
    project_root:
        Root directory of the user's project (where ``.opencode/`` lives).
    domains:
        List of domain identifiers in ``"category/name"`` format
        (e.g. ``["ai/data-forge", "dcc/blender"]``).
    """
    # ── Pre-read the user MCP registry once ──────────────────────
    reg: dict | None = None
    try:
        reg = registry_mod.read_registry_from_home(vibe_home)
    except Exception as exc:
        log_warn(f"无法读取 MCP 注册表: {exc}")
        # Continue with reg=None — activate_mcp_domain will re-read and handle

    # ── Ensure .opencode/ directory exists ───────────────────────
    dot_dir = project_root / ".opencode"
    dot_dir.mkdir(parents=True, exist_ok=True)

    for domain_key in domains:
        log_info(f"激活领域: {domain_key}")

        # 1. Parse and validate domain exists
        try:
            category, name, _ = _parse_domain_key(domain_key)
        except DomainNotFoundError as e:
            log_error(str(e))
            continue

        domain_root = vibe_home / "domains" / category / name
        if not domain_root.is_dir():
            log_warn(
                f"领域不存在: domains/{category}/{name}/ — 跳过 {domain_key}"
            )
            continue

        # 2. Check not already active
        if manifest.has_domain(project_root, domain_key):
            log_warn(f"领域已激活: {domain_key} — 跳过")
            continue

        prefix = _make_symlink_prefix(category, name)

        # 3. Create symlinks for each config type
        for type_name in VIBE_STACK_DIR_TYPES:
            src_dir = domain_root / type_name
            dest_dir = dot_dir / type_name
            try:
                if type_name == "tools":
                    symlinks.link_tools_directory(src_dir, dest_dir, prefix=prefix)
                else:
                    symlinks.link_directory_contents(src_dir, dest_dir, prefix=prefix)
            except Exception as exc:
                log_warn(f"创建符号链接失败 ({type_name}): {exc} — 继续")

        # 4. Build links dict for manifest recording
        links = _collect_links(domain_root, vibe_home, prefix)

        # 5. Auto-init submodule venv (if applicable)
        submodule_pyproject = domain_root / "tools" / name / "pyproject.toml"
        submodule_venv = domain_root / "tools" / name / ".venv"
        if submodule_pyproject.exists() and not submodule_venv.exists():
            print(f"Initializing {name} virtual environment...")
            result = subprocess.run(
                ["uv", "sync"],
                cwd=str(submodule_pyproject.parent),
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                log_warn(
                    f"Warning: venv init for {name} failed. "
                    f"Run 'uv sync' manually in {submodule_pyproject.parent}"
                )

        # 6. Activate domain MCP
        try:
            mcp.activate_mcp_domain(
                vibe_home=vibe_home,
                project_root=project_root,
                domain_key=domain_key,
                domain_root=domain_root,
                registry=reg,
            )
        except Exception as exc:
            log_warn(f"Domain MCP 激活失败 ({domain_key}): {exc} — 继续")

        # 7. Update opencode.json instructions (add domain rules glob)
        opencode_path = dot_dir / OPECODE_CONFIG_NAME
        rules_glob = f".opencode/rules/{prefix}_*.md"
        rc = config.array_add(opencode_path, "instructions", rules_glob)
        if rc == 0:
            log_ok(f"  + instructions: {rules_glob}")
        elif rc == 2:
            log_info(f"  (instructions 已包含 {rules_glob})")
        else:
            log_warn(f"  无法更新 instructions (key 不存在或文件缺失)")

        # 8. Register domain skills path in opencode.json
        # Use nested_array_add because opencode.json uses "skills": {"paths": [...]}
        skills_path = ".opencode/skills/"
        rc2 = config.nested_array_add(
            opencode_path, "skills", "paths", skills_path
        )
        if rc2 == 0:
            log_ok(f"  + skills.paths: {skills_path}")
        elif rc2 == 2:
            log_info(f"  (skills.paths 已包含 {skills_path})")
        else:
            # File may not exist yet; that's fine — it'll be picked up later
            pass

        # 9. Ensure OMO config skeleton exists
        try:
            mcp.activate_omo_config(project_root)
        except Exception as exc:
            log_warn(f"OMO 配置初始化失败: {exc}")

        # 10. Record activation in manifest
        try:
            manifest.add_domain(project_root, domain_key, links)
            log_ok(f"领域已激活: {domain_key}")
        except Exception as exc:
            log_error(f"写入 manifest 失败 ({domain_key}): {exc}")
