"""cmd_info — display detailed information about a specific domain."""

from __future__ import annotations

from pathlib import Path

from vibe_stack.cli.formatter import format_domain_info
from vibe_stack.errors import DomainNotFoundError
from vibe_stack.loader.domain_loader import load_domain


def cmd_info(
    vibe_home: Path,
    domain_key: str,
    json_output: bool = False,
) -> None:
    """Print detailed information about a domain.

    Args:
        vibe_home: Root of the vibe-stack repository.
        domain_key: Slash-delimited domain identifier (e.g. ``"dcc/blender"``).
        json_output: If ``True``, output JSON instead of plain text.

    Raises:
        SystemExit(1): If the domain is not found.
    """
    try:
        config = load_domain(vibe_home, domain_key)
    except DomainNotFoundError:
        raise SystemExit(1)

    output = format_domain_info(
        config.meta,
        config.domain_key,
        config.namespace,
        json_output=json_output,
    )
    print(output)
