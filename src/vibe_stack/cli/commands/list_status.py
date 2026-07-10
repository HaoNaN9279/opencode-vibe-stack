"""cmd_list and cmd_status — list available domains and show active status."""

from __future__ import annotations

from pathlib import Path

from vibe_stack.cli.formatter import format_domain_list, format_status
from vibe_stack.loader.domain_loader import discover_domains
from vibe_stack.sync.state_manager import list_active_domains


def cmd_list(
    vibe_home: Path,
    json_output: bool = False,
) -> None:
    """Print a list of all available domains.

    Args:
        vibe_home: Root of the vibe-stack repository.
        json_output: If ``True``, output JSON instead of plain text.
    """
    domains = discover_domains(vibe_home)
    # Extract (key, name, description) tuples for the formatter.
    formatted = [
        (key, meta.name, meta.description) for key, meta, _root in domains
    ]
    output = format_domain_list(formatted, json_output=json_output)
    print(output)


def cmd_status(
    vibe_home: Path,
    project_root: Path,
    json_output: bool = False,
) -> None:
    """Print the list of currently active domains in the project.

    Args:
        vibe_home: Root of the vibe-stack repository (unused by this command
            but kept for CLI interface consistency).
        project_root: Root of the project being configured.
        json_output: If ``True``, output JSON instead of plain text.
    """
    active = list_active_domains(project_root)
    output = format_status(active, json_output=json_output)
    print(output)
