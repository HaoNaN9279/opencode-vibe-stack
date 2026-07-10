"""cmd_activate — activate one or more domains in the current project."""

from __future__ import annotations

from pathlib import Path

from vibe_stack.errors import DomainAlreadyActiveError, DomainNotFoundError
from vibe_stack.sync.engine import activate_domain


def cmd_activate(
    vibe_home: Path,
    project_root: Path,
    domains: list[str],
) -> None:
    """Activate one or more domains in the project.

    Iterates over *domains*, calling :func:`activate_domain` for each.
    Catches ``DomainNotFoundError`` and ``DomainAlreadyActiveError``,
    printing a warning and continuing with the remaining domains.

    Args:
        vibe_home: Root of the vibe-stack repository.
        project_root: Root of the project being configured.
        domains: List of domain keys to activate.
    """
    for domain_key in domains:
        try:
            activate_domain(vibe_home, project_root, domain_key)
            print(f"Activated: {domain_key}")
        except DomainNotFoundError as exc:
            print(f"Warning: {exc}")
        except DomainAlreadyActiveError as exc:
            print(f"Warning: {exc}")
