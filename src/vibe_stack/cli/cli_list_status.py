"""list and status commands — list available domains and show active ones."""

from __future__ import annotations

from pathlib import Path

from vibe_stack import manifest
from vibe_stack.constants import VIBE_STACK_DIR_TYPES


def list_all_domains(vibe_home: Path) -> list[tuple[str, str, Path]]:
    """Scan ``domains/`` and return ``(category, domain, domain_root)`` for each valid domain.

    A domain is considered valid if it has at least one config subdirectory
    (``rules/``, ``agents/``, ``commands/``, ``mcp/``, ``skills/``, ``tools/``).
    """
    result: list[tuple[str, str, Path]] = []
    domains_dir = vibe_home / "domains"
    if not domains_dir.is_dir():
        return result

    for cat_dir in sorted(domains_dir.iterdir()):
        if not cat_dir.is_dir():
            continue
        category = cat_dir.name
        for domain_dir in sorted(cat_dir.iterdir()):
            if not domain_dir.is_dir():
                continue
            domain = domain_dir.name
            # Skip domains that have NO config subdirectories
            has_configs = any(
                (domain_dir / sub).is_dir() for sub in VIBE_STACK_DIR_TYPES
            )
            if has_configs:
                result.append((category, domain, domain_dir))
    return result


def cmd_list(vibe_home: Path, project_root: Path) -> None:
    """List all available domains, marking active ones with ``*``."""
    active_domains = set(manifest.list_active_domains(project_root))
    all_domains = list_all_domains(vibe_home)

    print("Available Domains:")
    print()

    current_cat = ""
    for category, domain, _ in all_domains:
        domain_key = f"{category}/{domain}"

        # Print category header when category changes
        if category != current_cat:
            if current_cat:
                print()
            print(f"  [{category}]")
            current_cat = category

        # Mark active domains with *
        if domain_key in active_domains:
            print(f"  * {domain}")
        else:
            print(f"    {domain}")

    print()
    print("  * = active in current project")
    print()
    print("Use 'vibe-stack status' for details on active domains.")


def cmd_status(vibe_home: Path, project_root: Path) -> None:
    """Show active domains and their link counts per type.

    Reads the project manifest and prints each active domain with a
    breakdown of how many symlinks exist per config type.
    """
    print(f"Active Domains in {project_root}:")
    print()

    dot_dir = project_root / ".opencode"
    if not dot_dir.is_dir():
        print("  No .opencode/ directory found. No domains active.")
        return

    data = manifest.read_manifest(project_root)
    domains = data.get("domains", {})

    if not domains:
        print(
            "  No domains active. Use 'vibe-stack activate <category/domain>"
            "' to add one."
        )
        return

    for domain_key in sorted(domains.keys()):
        info = domains[domain_key]
        links = info.get("links", {})
        # Count links per type (e.g. rules/, skills/, agents/)
        type_counts: dict[str, int] = {}
        for link_path in links:
            type_name = link_path.split("/")[0]
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        print(f"  \u25cf {domain_key}")
        for t in sorted(type_counts.keys()):
            c = type_counts[t]
            print(f"    {t}/: {c} links")
