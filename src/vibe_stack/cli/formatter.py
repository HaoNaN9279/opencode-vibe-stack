"""CLI output formatters for vibe-stack commands.

All format functions support a ``json_output`` parameter for machine-readable
output.  Plain-text output is designed for human readability.
"""

from __future__ import annotations

import json
from collections import OrderedDict
from typing import Any


def format_domain_list(
    domains: list[tuple[str, str, str]],
    json_output: bool = False,
) -> str:
    """Format a list of domains grouped by category.

    Each tuple is ``(domain_key, name, description)`` where *domain_key* is
    a slash-delimited identifier such as ``"dcc/blender"``.

    Parameters:
        domains: Sequence of ``(key, name, description)`` tuples.
        json_output: When *True*, return JSON instead of plain text.

    Returns:
        Formatted string (plain text or JSON).
    """
    if json_output:
        entries: list[dict[str, str]] = []
        for key, name, desc in domains:
            entries.append({"key": key, "name": name, "description": desc})
        return json.dumps({"domains": entries}, indent=2, ensure_ascii=False)

    if not domains:
        return "No domains available."

    # Group by category (the part before the first '/').
    grouped: dict[str, list[tuple[str, str, str]]] = OrderedDict()
    for key, name, desc in sorted(domains, key=lambda x: x[0]):
        category = key.split("/")[0] if "/" in key else "_other"
        if category not in grouped:
            grouped[category] = []
        grouped[category].append((key, name, desc))

    lines: list[str] = []
    for cat_idx, (category, items) in enumerate(grouped.items()):
        if cat_idx > 0:
            lines.append("")
        lines.append(f"{category.upper()}:")
        for key, name, desc in items:
            short_key = key.split("/", 1)[1] if "/" in key else key
            display_name = name if name else short_key
            parts = [f"  {short_key}"]
            if display_name and display_name != short_key:
                parts.append(display_name)
            if desc:
                parts.append(desc)
            lines.append("    ".join(parts))

    return "\n".join(lines)


def format_domain_info(
    meta: Any,
    domain_key: str,
    namespace: str,
    json_output: bool = False,
) -> str:
    """Format detailed information about a single domain.

    Parameters:
        meta: A :class:`~vibe_stack.model.domain.DomainMeta` instance (or any
            object with ``name``, ``description``, ``version``, ``tags``, and
            ``dependencies`` attributes).
        domain_key: Slash-delimited domain key (e.g. ``"dcc/blender"``).
        namespace: Underscore-delimited namespace (e.g. ``"dcc_blender"``).
        json_output: When *True*, return JSON instead of plain text.

    Returns:
        Formatted string (plain text or JSON).
    """
    if json_output:
        return json.dumps(
            {
                "key": domain_key,
                "name": meta.name,
                "description": meta.description,
                "version": meta.version,
                "tags": list(meta.tags or []),
                "namespace": namespace,
                "dependencies": list(meta.dependencies or []),
            },
            indent=2,
            ensure_ascii=False,
        )

    lines: list[str] = [
        f"Domain: {domain_key}",
        f"  Name:        {meta.name}",
        f"  Description: {meta.description}",
        f"  Version:     {meta.version}",
        f"  Namespace:   {namespace}",
    ]
    tags = list(meta.tags or [])
    lines.append(f"  Tags:        {', '.join(tags) if tags else '(none)'}")
    deps = list(meta.dependencies or [])
    lines.append(f"  Dependencies: {', '.join(deps) if deps else '(none)'}")
    return "\n".join(lines)


def format_status(
    active_domains: list[str],
    json_output: bool = False,
) -> str:
    """Format the current active-domain status.

    Parameters:
        active_domains: List of domain keys that are currently active.
        json_output: When *True*, return JSON instead of plain text.

    Returns:
        Formatted string (plain text or JSON).
    """
    if json_output:
        return json.dumps(
            {"active_domains": list(active_domains)},
            indent=2,
            ensure_ascii=False,
        )

    if not active_domains:
        return "No active domains."
    lines: list[str] = ["Active Domains:"]
    for key in active_domains:
        lines.append(f"  - {key}")
    return "\n".join(lines)


def format_sync_result(
    created: int,
    updated: int,
    deleted: int,
    json_output: bool = False,
) -> str:
    """Format a domain-sync result summary.

    Parameters:
        created: Number of items created.
        updated: Number of items updated.
        deleted: Number of items deleted.
        json_output: When *True*, return JSON instead of plain text.

    Returns:
        Formatted string (plain text or JSON).
    """
    if json_output:
        return json.dumps(
            {
                "created": created,
                "updated": updated,
                "deleted": deleted,
            },
            indent=2,
            ensure_ascii=False,
        )

    return f"Sync complete: {created} created, {updated} updated, {deleted} deleted"
