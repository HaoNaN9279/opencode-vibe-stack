"""cmd_sync — synchronise core config and all active domains."""

from __future__ import annotations

from pathlib import Path

from vibe_stack.cli.formatter import format_sync_result
from vibe_stack.sync.engine import sync


def cmd_sync(
    vibe_home: Path,
    project_root: Path,
) -> None:
    """Synchronise core config and all active domains.

    Calls :func:`~vibe_stack.sync.engine.sync` to perform a full sync
    (core + all active domains) and prints a result summary.

    Args:
        vibe_home: Root of the vibe-stack repository.
        project_root: Root of the project.
    """
    sync(vibe_home, project_root)
    output = format_sync_result(
        created=0,
        updated=0,
        deleted=0,
        json_output=False,
    )
    print(output)
