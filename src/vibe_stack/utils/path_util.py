"""Path utility functions for vibe-stack."""

from __future__ import annotations

from pathlib import Path

# Sentinel markers used to detect the vibe stack project root.
_MARKER_FILE = Path("core") / "rules" / "00-global.md"
_MARKER_DIR = "domains"


def namespace_from_key(domain_key: str) -> str:
    """Convert a domain key to a filesystem-safe namespace by replacing slashes.

    Args:
        domain_key: Domain key using forward slash as separator
            (e.g. ``"dcc/blender"``).

    Returns:
        Namespace string with slashes replaced by underscores
        (e.g. ``"dcc_blender"``).

    Examples:
        >>> namespace_from_key("dcc/blender")
        'dcc_blender'
        >>> namespace_from_key("dcc/sub/deep")
        'dcc_sub_deep'
        >>> namespace_from_key("simple")
        'simple'
    """
    return domain_key.replace("/", "_")


def key_from_namespace(namespace: str) -> str:
    """Convert a namespace back to a domain key by replacing underscores.

    Args:
        namespace: Namespace string using underscores as separator
            (e.g. ``"dcc_blender"``).

    Returns:
        Domain key with underscores replaced by forward slashes
        (e.g. ``"dcc/blender"``).

    Examples:
        >>> key_from_namespace("dcc_blender")
        'dcc/blender'
        >>> key_from_namespace("dcc_sub_deep")
        'dcc/sub/deep'
        >>> key_from_namespace("simple")
        'simple'
    """
    return namespace.replace("_", "/")


def ensure_dir(path: Path) -> None:
    """Create a directory and all its parents, no-op if it already exists.

    Args:
        path: Directory path to create.

    Examples:
        >>> ensure_dir(Path("/tmp/a/b/c"))
    """
    path.mkdir(parents=True, exist_ok=True)


def detect_vibe_home() -> Path:
    """Walk up from the current working directory to locate the vibe-stack root.

    The root is identified by the presence of both:
    1. ``core/rules/00-global.md``
    2. A ``domains/`` directory

    Returns:
        Absolute path to the vibe-stack project root.

    Raises:
        RuntimeError: If the project root cannot be found by walking up to the
            filesystem root.

    Examples:
        >>> detect_vibe_home()
        PosixPath('/home/user/.opencode-vibe-stack')
    """
    current = Path.cwd().resolve()
    for parent in (current, *current.parents):
        if (parent / _MARKER_FILE).is_file() and (parent / _MARKER_DIR).is_dir():
            return parent
    raise RuntimeError("vibe stack home not found")


def compute_relative_target(
    source: Path, dot_opencode: Path, namespace: str, dir_type: str
) -> Path:
    """Build the relative target path for a config item inside ``.opencode/``.

    Given a source path from the domain directory and the project's
    ``.opencode`` directory, compute the canonical destination path::

        <dot_opencode>/<dir_type>/<namespace>/<source.name>

    Args:
        source: Path to the source file or directory (only ``.name`` is used).
        dot_opencode: Path to the project ``.opencode`` directory.
        namespace: Namespace string (e.g. ``"dcc_blender"``).
        dir_type: Config directory type (e.g. ``"rules"``, ``"skills"``).

    Returns:
        The computed target path.

    Examples:
        >>> source = Path("/repo/domains/dcc/blender/rules/blender.md")
        >>> dot = Path("/proj/.opencode")
        >>> compute_relative_target(source, dot, "dcc_blender", "rules")
        PosixPath('/proj/.opencode/rules/dcc_blender/blender.md')
    """
    return dot_opencode / dir_type / namespace / source.name
