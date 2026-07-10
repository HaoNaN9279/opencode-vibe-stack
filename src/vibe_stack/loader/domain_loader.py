"""Domain loader: discover and load domain configurations.

Provides two pure functions:

* :func:`discover_domains` — recursively find all ``domain.json`` files
  under ``domains/`` and return their metadata.
* :func:`load_domain` — parse a single domain's ``domain.json`` and scan
  its subdirectories into a :class:`~vibe_stack.model.domain.DomainConfig`.
"""

from __future__ import annotations

import json
from pathlib import Path

from vibe_stack.errors import DomainNotFoundError, VibeStackError
from vibe_stack.model.domain import DomainConfig, DomainMeta
from vibe_stack.utils.path_util import namespace_from_key

_DOMAINS_DIR = "domains"
_DOMAIN_JSON = "domain.json"


def discover_domains(vibe_home: Path) -> list[tuple[str, DomainMeta, Path]]:
    """Recursively scan ``vibe_home/domains/**/domain.json``.

    Args:
        vibe_home: Root directory of the vibe-stack project (must contain
            a ``domains/`` subdirectory).

    Returns:
        Sorted list of ``(domain_key, DomainMeta, domain_root)`` tuples.
        *domain_key* is the forward-slash-delimited relative path from
        ``domains/`` to the directory containing ``domain.json``.
        Results are sorted alphabetically by *domain_key* for deterministic
        ordering.

        Returns an empty list when no ``domain.json`` files are found.

    Examples:
        >>> from pathlib import Path
        >>> # Assume vibe_home/domains/dcc/blender/domain.json exists.
        >>> results = discover_domains(vibe_home)
        >>> len(results) > 0
        True
    """
    domains_dir = vibe_home / _DOMAINS_DIR
    if not domains_dir.is_dir():
        return []

    results: list[tuple[str, DomainMeta, Path]] = []
    for config_path in sorted(domains_dir.rglob(_DOMAIN_JSON)):
        domain_root = config_path.parent
        # Compute relative path from domains/ to the domain root.
        try:
            rel = domain_root.relative_to(domains_dir)
        except ValueError:
            # Path not under domains/ — should not happen with rglob but
            # guard against symlink shenanigans.
            continue

        domain_key = rel.as_posix()
        if not domain_key or domain_key == ".":
            # domain.json directly in domains/ itself or its immediate
            # child — skip (domains must live in a named subdirectory).
            continue

        meta = _parse_domain_meta(config_path)
        results.append((domain_key, meta, domain_root))

    # Sort by domain_key for deterministic output.
    results.sort(key=lambda item: item[0])
    return results


def load_domain(vibe_home: Path, domain_key: str) -> DomainConfig:
    """Load a single domain configuration by its *domain_key*.

    Scans all subdirectories and returns a fully-populated
    :class:`~vibe_stack.model.domain.DomainConfig`.

    Args:
        vibe_home: Root directory of the vibe-stack project.
        domain_key: Forward-slash-delimited domain identifier
            (e.g. ``"dcc/blender"``).

    Returns:
        Complete domain configuration with all file lists populated.

    Raises:
        DomainNotFoundError: If no ``domain.json`` exists at the expected
            location ``vibe_home/domains/<domain_key>/domain.json``.
        VibeStackError: If ``domain.json`` is missing required fields
            (``name``, ``description``, ``version``).

    Examples:
        >>> config = load_domain(vibe_home, "dcc/blender")
        >>> config.namespace
        'dcc_blender'
        >>> len(config.rules) >= 0
        True
    """
    domain_root = vibe_home / _DOMAINS_DIR / domain_key
    config_path = domain_root / _DOMAIN_JSON

    if not config_path.is_file():
        raise DomainNotFoundError(
            f"domain '{domain_key}' not found at {config_path}"
        )

    meta = _parse_domain_meta(config_path)
    namespace = namespace_from_key(domain_key)

    return DomainConfig(
        meta=meta,
        domain_key=domain_key,
        namespace=namespace,
        domain_root=domain_root,
        rules=_scan_rules(domain_root),
        agents=_scan_agents(domain_root),
        commands=_scan_commands(domain_root),
        mcp_files=_scan_mcp_files(domain_root),
        mcp_dirs=_scan_mcp_dirs(domain_root),
        skills=_scan_skills(domain_root),
    )


# ── internal helpers (single-use, scoped to this module) ─────────────


def _parse_domain_meta(config_path: Path) -> DomainMeta:
    """Parse ``domain.json`` at *config_path* into a :class:`DomainMeta`.

    Raises:
        VibeStackError: If any required field (``name``, ``description``,
            ``version``) is missing from the JSON data.
    """
    raw = config_path.read_text(encoding="utf-8")
    try:
        data: dict[str, object] = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise VibeStackError(
            f"invalid JSON in {config_path}: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise VibeStackError(
            f"domain.json at {config_path} must be a JSON object"
        )

    # Validate required fields.
    missing = [f for f in ("name", "description", "version") if f not in data]
    if missing:
        raise VibeStackError(
            f"domain.json at {config_path} is missing required fields: "
            f"{', '.join(missing)}"
        )

    return DomainMeta(
        name=str(data["name"]),
        description=str(data["description"]),
        version=str(data["version"]),
        tags=_as_str_list(data.get("tags", [])),
        dependencies=_as_str_list(data.get("dependencies", [])),
    )


def _as_str_list(value: object) -> list[str]:
    """Coerce *value* into a list of strings. Returns ``[]`` on failure."""
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _scan_rules(domain_root: Path) -> list[Path]:
    """Scan ``domain_root/rules/*.md``, returned sorted."""
    rules_dir = domain_root / "rules"
    if not rules_dir.is_dir():
        return []
    return sorted(rules_dir.glob("*.md"))


def _scan_agents(domain_root: Path) -> list[Path]:
    """Scan ``domain_root/agents/*.md``, returned sorted."""
    agents_dir = domain_root / "agents"
    if not agents_dir.is_dir():
        return []
    return sorted(agents_dir.glob("*.md"))


def _scan_commands(domain_root: Path) -> list[Path]:
    """Scan ``domain_root/commands/*.md``, returned sorted."""
    commands_dir = domain_root / "commands"
    if not commands_dir.is_dir():
        return []
    return sorted(commands_dir.glob("*.md"))


def _scan_mcp_files(domain_root: Path) -> list[Path]:
    """Scan ``domain_root/mcp/*.json`` for MCP config files, returned sorted."""
    mcp_dir = domain_root / "mcp"
    if not mcp_dir.is_dir():
        return []
    return sorted(mcp_dir.glob("*.json"))


def _scan_mcp_dirs(domain_root: Path) -> list[Path]:
    """Scan ``domain_root/mcp/`` for subdirectories, returned sorted."""
    mcp_dir = domain_root / "mcp"
    if not mcp_dir.is_dir():
        return []
    return sorted(
        entry for entry in mcp_dir.iterdir() if entry.is_dir()
    )


def _scan_skills(domain_root: Path) -> list[Path]:
    """Scan ``domain_root/skills/`` for subdirectories containing
    ``SKILL.md``, returned sorted."""
    skills_dir = domain_root / "skills"
    if not skills_dir.is_dir():
        return []
    result: list[Path] = []
    for entry in sorted(skills_dir.iterdir()):
        if entry.is_dir() and (entry / "SKILL.md").is_file():
            result.append(entry)
    return result
