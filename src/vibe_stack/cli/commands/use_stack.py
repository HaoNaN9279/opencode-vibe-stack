"""CLI command — activate all domains from a stack preset.

A *stack* is a named collection of domains defined in a ``stacks/*.json``
file within the vibe-stack repository.  This command provides two modes:

* **Empty stack name** — scan and print all available stacks.
* **Named stack** — load the stack definition and activate every domain
  it contains via the sync engine.

Functions:
    cmd_use_stack: Activate all domains from a stack preset.
"""

from __future__ import annotations

from pathlib import Path

from vibe_stack.errors import StackNotFoundError
from vibe_stack.loader.stack_loader import discover_stacks, load_stack
from vibe_stack.sync.engine import activate_domain


def cmd_use_stack(
    vibe_home: Path,
    project_root: Path,
    stack_name: str = "",
) -> None:
    """Activate all domains from a stack preset.

    When *stack_name* is empty, this function discovers and prints every
    available stack definition (name, description and domain count).
    Callers can use this output to decide which stack to apply.

    When *stack_name* is provided, the corresponding ``stacks/{name}.json``
    file is loaded.  Each domain key listed in that file is then activated
    via :func:`vibe_stack.sync.engine.activate_domain`.

    Args:
        vibe_home: Root of the vibe-stack repository (contains
            ``stacks/`` directory).
        project_root: Root of the project being configured.
        stack_name: Name of the stack preset to apply.  Pass an empty
            string (default) to list available stacks.

    Raises:
        StackNotFoundError: Propagated from :func:`load_stack` when
            ``stacks/{stack_name}.json`` does not exist.  Not raised
            directly — the function prints an error message instead.
    """
    if not stack_name:
        stacks = discover_stacks(vibe_home)
        if stacks:
            print("Available stacks:")
            for name, data in stacks:
                desc = data.get("description") or data.get("name", "")
                domains = data.get("domains", [])
                print(f"  {name}  - {desc} ({len(domains)} domains)")
        else:
            print("No stacks available.")
        return

    try:
        domains = load_stack(vibe_home, stack_name)
    except StackNotFoundError as exc:
        print(f"Error: {exc}")
        return

    for domain_key in domains:
        activate_domain(vibe_home, project_root, domain_key)
