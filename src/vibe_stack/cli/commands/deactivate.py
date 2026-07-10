"""cmd_deactivate — deactivate one or more domains from the current project."""

from __future__ import annotations

from pathlib import Path

from vibe_stack.errors import DomainNotActiveError
from vibe_stack.sync.engine import deactivate_domain


def cmd_deactivate(
    vibe_home: Path,
    project_root: Path,
    domains: list[str],
) -> None:
    """Deactivate one or more domains from the project.

    Iterates over *domains*, calling :func:`deactivate_domain` for each.
    Catches ``DomainNotActiveError``, printing a warning and continuing
    with the remaining domains.

    Args:
        vibe_home: Root of the vibe-stack repository.
        project_root: Root of the project.
        domains: List of domain keys to deactivate.
    """
    for domain_key in domains:
        try:
            deactivate_domain(vibe_home, project_root, domain_key)
            print(f"Deactivated: {domain_key}")
        except DomainNotActiveError as exc:
            print(f"Warning: {exc}")
