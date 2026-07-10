"""Stack definition loader — discover and load ``stacks/*.json`` files.

Stacks are preset combinations of domains defined as JSON files in the
``stacks/`` directory of the vibe-stack repository.

Functions:
    discover_stacks: Scan ``stacks/*.json`` and return (name, data) tuples.
    load_stack: Load a stack by name and return its list of domain keys.
"""

from __future__ import annotations

import json
from pathlib import Path

from vibe_stack.errors import StackNotFoundError, VibeStackError


def discover_stacks(vibe_home: Path) -> list[tuple[str, dict]]:
    """Scan ``stacks/*.json`` files and return parsed stack definitions.

    Each JSON file is parsed and returned as a ``(name, data)`` tuple where
    *name* is the filename stem (e.g. ``"game-dev"`` for ``game-dev.json``)
    and *data* is the full parsed JSON dictionary.

    Args:
        vibe_home: Root of the vibe-stack repository (parent of ``stacks/``).

    Returns:
        List of ``(name, data)`` tuples, one per ``.json`` file found.
        Returns an empty list if the ``stacks/`` directory is missing or empty.
    """
    stacks_dir = vibe_home / "stacks"
    if not stacks_dir.is_dir():
        return []

    results: list[tuple[str, dict]] = []
    for entry in sorted(stacks_dir.iterdir()):
        if entry.suffix.lower() == ".json":
            name = entry.stem
            data = json.loads(entry.read_text(encoding="utf-8"))
            results.append((name, data))
    return results


def load_stack(vibe_home: Path, stack_name: str) -> list[str]:
    """Load a stack definition by name and return its domain keys.

    Looks for a file named ``{stack_name}.json`` inside the ``stacks/``
    directory, parses it, and returns the ``domains`` list.

    Args:
        vibe_home: Root of the vibe-stack repository (parent of ``stacks/``).
        stack_name: Stack name — the filename stem (e.g. ``"game-dev"``).

    Returns:
        List of domain keys (e.g. ``["game-dev/unity", "game-dev/unreal"]``).

    Raises:
        StackNotFoundError: If no ``{stack_name}.json`` file exists.
        VibeStackError: If the file content is not valid JSON.
    """
    stack_file = vibe_home / "stacks" / f"{stack_name}.json"
    if not stack_file.is_file():
        raise StackNotFoundError(
            f"stack '{stack_name}' not found at {stack_file}"
        )

    try:
        data = json.loads(stack_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise VibeStackError(
            f"invalid JSON in stack file '{stack_name}.json': {exc}"
        ) from exc

    return list(data.get("domains", []))
