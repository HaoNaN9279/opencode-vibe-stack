"""State file manager for .vibe-stack-state.json.

Provides read/write/create operations for the activation state file stored at
``{project_root}/.opencode/.vibe-stack-state.json``.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from vibe_stack.errors import StateFileError
from vibe_stack.model.state import ActivationState, DomainState

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def _state_file_path(project_root: Path) -> Path:
    """Return the absolute path to the state file."""
    return project_root / ".opencode" / ".vibe-stack-state.json"


def _ensure_opencode_dir(project_root: Path) -> None:
    """Create the .opencode directory if it does not exist."""
    opencode_dir = project_root / ".opencode"
    opencode_dir.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


def _deserialize_state(raw: dict[str, object]) -> ActivationState:
    """Convert a raw dict (from JSON) into an ActivationState.

    Parameters:
        raw: Dictionary from ``json.loads``, expected to contain
            ``"version"`` (int) and ``"domains"`` (dict of
            ``str → domain dict``).

    Returns:
        A fully materialised ``ActivationState`` instance.
    """
    raw_domains: dict[str, object] = raw.get("domains", {})  # type: ignore[assignment]
    domains: dict[str, DomainState] = {}
    for key, ds_dict in raw_domains.items():
        domains[key] = DomainState(**ds_dict)  # type: ignore[arg-type]
    return ActivationState(
        version=raw.get("version", 2),  # type: ignore[arg-type]
        domains=domains,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def read_state(project_root: Path) -> ActivationState:
    """Read ``.vibe-stack-state.json`` from project.

    Returns the default ``ActivationState`` if the file is missing or
    empty.  Raises ``StateFileError`` if the file exists but contains
    unparseable JSON.

    Parameters:
        project_root: The root directory of the project.

    Returns:
        The deserialised ``ActivationState``.

    Raises:
        StateFileError: If the state file contains corrupted JSON.
    """
    sf = _state_file_path(project_root)

    if not sf.exists():
        return ActivationState()

    raw_text = sf.read_text(encoding="utf-8")

    # Treat empty file (or whitespace-only) as default state.
    if not raw_text.strip():
        return ActivationState()

    try:
        raw: object = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise StateFileError(f"corrupt state file: {exc}") from exc

    if not isinstance(raw, dict):
        raise StateFileError(
            f"expected JSON object at top level, got {type(raw).__name__}"
        )

    return _deserialize_state(raw)


def write_state(project_root: Path, state: ActivationState) -> None:
    """Write ``ActivationState`` to ``.vibe-stack-state.json``.

    Creates the ``.opencode/`` directory if it does not exist.

    Parameters:
        project_root: The root directory of the project.
        state: The activation state to persist.
    """
    _ensure_opencode_dir(project_root)
    sf = _state_file_path(project_root)
    sf.write_text(
        json.dumps(asdict(state), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def add_domain(state: ActivationState, ds: DomainState) -> None:
    """Add or overwrite a domain in the activation state.

    Parameters:
        state: The activation state to mutate in-place.
        ds: The domain state to insert.
    """
    state.domains[ds.domain_key] = ds


def remove_domain(state: ActivationState, key: str) -> bool:
    """Remove a domain from the activation state.

    Parameters:
        state: The activation state to mutate in-place.
        key: The domain key to remove.

    Returns:
        ``True`` if the key was present and removed, ``False``
        otherwise.
    """
    return state.domains.pop(key, None) is not None


def list_active_domains(project_root: Path) -> list[str]:
    """Return the sorted list of active domain keys.

    Parameters:
        project_root: The root directory of the project.

    Returns:
        Alphabetically sorted list of domain keys.
    """
    state = read_state(project_root)
    return sorted(state.domains.keys())


def ensure_state_file(project_root: Path) -> ActivationState:
    """Get the activation state, creating the file if it is missing.

    If the state file already exists it is read and returned as-is.
    Otherwise a default ``ActivationState`` is written to disk first.

    Parameters:
        project_root: The root directory of the project.

    Returns:
        The activation state.
    """
    sf = _state_file_path(project_root)
    if sf.exists():
        return read_state(project_root)

    state = ActivationState()
    write_state(project_root, state)
    return state
