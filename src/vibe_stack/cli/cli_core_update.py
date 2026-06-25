"""core-update command — re-sync core symlinks, refresh MCP config, and
sync domain links from the active manifest.

Port of ``bin/vibe-stack/commands/core-update.sh`` (299 lines, shell + Python)
to pure Python with full cross-platform support.
"""

from __future__ import annotations

import os
from pathlib import Path

from vibe_stack import config
from vibe_stack import manifest as manifest_mod
from vibe_stack import symlinks
from vibe_stack.constants import (
    ACTIVE_MANIFEST_NAME,
    OPENCODE_CONFIG_DIR,
    OPECODE_CONFIG_NAME,
    VIBE_STACK_DIR_TYPES,
)
from vibe_stack.mcp import activate_mcp_core
from vibe_stack.utils import log_info, log_ok, log_warn


def cmd_core_update(vibe_home: Path, project_root: Path) -> None:
    """Re-sync core symlinks and domain links for the current project.

    1. Re-sync per-item core symlinks from ``vibe_home/core/`` →
       ``~/.config/opencode/``.
    2. Update user-level ``opencode.json`` with core rules instructions
       and skills path.
    3. Refresh core MCP configuration via :func:`activate_mcp_core`.
    4. Sync active project domain symlinks (if a ``.vibe-stack-active.json``
       manifest exists): verify, repair, detect new files, update manifest.
    """
    # ── Part A: Core → User Config per-item link sync ─────────────
    log_info("Re-syncing core symlinks...")
    print()

    for type_name in VIBE_STACK_DIR_TYPES:
        src = vibe_home / "core" / type_name
        dest = OPENCODE_CONFIG_DIR / type_name

        if not src.is_dir():
            log_warn(f"Skipping {type_name}: source not found at {src}")
            continue

        OPENCODE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if type_name == "tools":
            symlinks.link_tools_directory(src, dest)
        elif type_name == "mcp":
            # Only link companion folders for MCP JSON configs
            for mcp_file in sorted(src.glob("*.json")):
                folder_name = mcp_file.stem
                companion_dir = src / folder_name
                if companion_dir.is_dir():
                    link_name = folder_name
                    link_path = dest / link_name
                    symlinks.remove_link(link_path)
                    symlinks.create_dir_link(companion_dir, link_path)
        else:
            symlinks.link_directory_contents(src, dest)
        log_ok(f"{type_name}/ -> per-item links synced")

    # ── Part A2: Update opencode.json instructions & skills ────────
    _ensure_opencode_config()

    # ── Part A3: Core MCP activation ───────────────────────────────
    print()
    log_info("Refreshing core MCP configuration...")
    activate_mcp_core(vibe_home)

    # ── Part B: Domain → Project Config Sync ───────────────────────
    manifest_file = project_root / ".opencode" / ACTIVE_MANIFEST_NAME
    if manifest_file.is_file():
        _sync_domain_links(vibe_home, project_root)
    else:
        print()
        log_info("No active domains — skipping domain sync.")


# ── helpers ────────────────────────────────────────────────────────


def _ensure_opencode_config() -> None:
    """Ensure user-level ``opencode.json`` has instructions and skills paths.

    Modifies ``~/.config/opencode/opencode.json`` in place:
    * ``instructions`` ← includes ``~/.config/opencode/rules/*.md``
    * ``skills.paths`` ← includes ``"skills"``
    """
    opencode_path = OPENCODE_CONFIG_DIR / OPECODE_CONFIG_NAME
    log_info(f"Updating core rules in {opencode_path} ...")

    # Read existing or start with empty dict
    if opencode_path.is_file():
        try:
            cfg = config.read_jsonc(opencode_path)
        except Exception as e:
            log_warn(f"Cannot read {opencode_path}, using defaults: {e}")
            cfg = {}
    else:
        cfg = {}

    modified = False

    # ── 1. Ensure core rules instructions ──────────────────────
    instructions: list = cfg.setdefault("instructions", [])
    if not isinstance(instructions, list):
        instructions = []
        cfg["instructions"] = instructions

    rule_glob = "~/.config/opencode/rules/*.md"
    if rule_glob not in instructions:
        instructions.append(rule_glob)
        modified = True
        log_ok("  Added core rules to instructions")

    # ── 2. Ensure skills.paths ─────────────────────────────────
    skills: dict = cfg.setdefault("skills", {})
    if not isinstance(skills, dict):
        skills = {}
        cfg["skills"] = skills

    paths: list = skills.setdefault("paths", [])
    if not isinstance(paths, list):
        paths = []
        skills["paths"] = paths

    if "skills" not in paths:
        paths.append("skills")
        modified = True
        log_ok("  Registered core skills in skills.paths")

    # Write back when anything changed or file was missing
    if modified or not opencode_path.is_file():
        config.write_jsonc(opencode_path, cfg)


def _sync_domain_links(vibe_home: Path, project_root: Path) -> None:
    """Sync domain symlinks driven by ``.vibe-stack-active.json``.

    For each active domain entry:
    1. **Verify existing links** — if the destination symlink target is
       wrong, fix it; if the destination is missing, create it.
    2. **Remove stale links** — if the source file/directory was deleted
       from the domain, remove the dead link.
    3. **Detect new items** — scan each domain type directory for files
       not yet recorded in the manifest and create links for them.
    4. **Update manifest** — write back updated link mapping when changes
       are made.
    """
    print()
    log_info("Syncing domain links...")

    data = manifest_mod.read_manifest(project_root)
    domains: dict = data.get("domains", {})

    if not domains:
        log_info("  No active domains in manifest.")
        return

    dot_opencode = project_root / ".opencode"

    for domain_key, info in list(domains.items()):
        links: dict = info.get("links", {})
        updated_links: dict[str, str] = {}
        changes_detected = False

        # ── 1. Verify existing links ───────────────────────────
        for dest_rel, src_rel in links.items():
            src_full = vibe_home / src_rel
            dest_full = dot_opencode / dest_rel

            if src_full.exists():
                # Source still exists — verify/recreate link
                if dest_full.is_symlink():
                    # Symlink exists — check if target matches
                    try:
                        current_target = os.readlink(str(dest_full))
                    except OSError:
                        current_target = ""
                    if current_target != str(src_full):
                        symlinks.remove_link(dest_full)
                        _create_link(src_full, dest_full)
                        changes_detected = True
                        log_ok(f"  FIXED: {dest_rel}")
                elif not dest_full.exists():
                    # Missing — create it
                    dest_full.parent.mkdir(parents=True, exist_ok=True)
                    _create_link(src_full, dest_full)
                    changes_detected = True
                    log_ok(f"  CREATED: {dest_rel}")
                else:
                    # Exists but not a symlink (user file or junction) — skip
                    log_info(f"  SKIP (not symlink): {dest_rel}")
                updated_links[dest_rel] = src_rel
            else:
                # Source deleted — stale link
                if dest_full.is_symlink() or dest_full.exists():
                    symlinks.remove_link(dest_full)
                    changes_detected = True
                    log_ok(f"  REMOVED (stale): {dest_rel}")
                changes_detected = True
                # Do NOT add to updated_links — entry is removed

        # ── 2. Check for new items in domain source dirs ───────
        parts = domain_key.split("/", 1)
        category = parts[0]
        domain_name = parts[1] if len(parts) > 1 else category
        domain_root = vibe_home / "domains" / category / domain_name

        prefix = f"{category}_{domain_name}"

        for type_dir in VIBE_STACK_DIR_TYPES:
            type_path = domain_root / type_dir
            if not type_path.is_dir():
                continue

            if type_dir == "tools":
                # Per-item links: directories keep original name, files get prefix
                for item in sorted(type_path.iterdir()):
                    item_name = item.name
                    if item.is_dir():
                        linked_name = item_name
                    else:
                        linked_name = f"{prefix}_{item_name}"
                    dest_rel = f"{type_dir}/{linked_name}"
                    src_rel = (
                        f"domains/{category}/{domain_name}/{type_dir}/{item_name}"
                    )

                    if dest_rel not in updated_links:
                        src_full = vibe_home / src_rel
                        dest_full = dot_opencode / dest_rel
                        dest_full.parent.mkdir(parents=True, exist_ok=True)
                        _create_link(src_full, dest_full)
                        updated_links[dest_rel] = src_rel
                        changes_detected = True
                        log_ok(f"  NEW: {dest_rel}")
                continue

            if type_dir == "mcp":
                # Only process companion folders of .json configs
                for mcp_file in sorted(type_path.glob("*.json")):
                    folder_name = mcp_file.stem
                    companion_dir = type_path / folder_name
                    if companion_dir.is_dir():
                        prefixed_name = f"{prefix}_{folder_name}"
                        dest_rel = f"{type_dir}/{prefixed_name}"
                        src_rel = (
                            f"domains/{category}/{domain_name}/{type_dir}/{folder_name}"
                        )

                        if dest_rel not in updated_links:
                            src_full = vibe_home / src_rel
                            dest_full = dot_opencode / dest_rel
                            dest_full.parent.mkdir(parents=True, exist_ok=True)
                            _create_link(src_full, dest_full)
                            updated_links[dest_rel] = src_rel
                            changes_detected = True
                            log_ok(f"  NEW: {dest_rel}")
                continue

            for item in sorted(type_path.iterdir()):
                item_name = item.name
                prefixed_name = f"{prefix}_{item_name}"
                dest_rel = f"{type_dir}/{prefixed_name}"
                src_rel = (
                    f"domains/{category}/{domain_name}/{type_dir}/{item_name}"
                )

                if dest_rel not in updated_links:
                    # New item not yet in manifest — create link
                    src_full = vibe_home / src_rel
                    dest_full = dot_opencode / dest_rel
                    dest_full.parent.mkdir(parents=True, exist_ok=True)
                    _create_link(src_full, dest_full)
                    updated_links[dest_rel] = src_rel
                    changes_detected = True
                    log_ok(f"  NEW: {dest_rel}")

        # ── 3. Persist updated manifest ────────────────────────
        if changes_detected:
            info["links"] = updated_links
            manifest_mod.write_manifest(project_root, data)
            log_ok(f"  UPDATED: {domain_key}")


def _create_link(src: Path, dest: Path) -> None:
    """Create a link at *dest* pointing to *src*, using the appropriate
    method for the source type (directory junction or file symlink).

    Handles cleanup of any existing content at *dest* first.
    """
    symlinks.remove_link(dest)
    if src.is_dir():
        symlinks.create_dir_link(src, dest)
    else:
        symlinks.create_symlink(src, dest)
