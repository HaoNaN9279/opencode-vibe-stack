"""Exception hierarchy for vibe-stack.

All custom exceptions inherit from :class:`VibeStackError`, which itself
inherits from the built-in :class:`Exception`.
"""

from __future__ import annotations


class VibeStackError(Exception):
    """Base exception for all vibe-stack errors.

    All custom exceptions in vibe-stack should inherit from this class
    rather than directly from :class:`Exception`, allowing callers to
    catch all vibe-stack-specific errors with a single except clause.

    Parameters:
        message: A human-readable description of the error.
    """

    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(message)


class DomainNotFoundError(VibeStackError):
    """Raised when a requested domain does not exist.

    Examples:
        >>> raise DomainNotFoundError("domain 'ai/data-forge' not found")
    """


class DomainAlreadyActiveError(VibeStackError):
    """Raised when attempting to activate a domain that is already active.

    Examples:
        >>> raise DomainAlreadyActiveError("domain 'dcc/blender' is already active")
    """


class DomainNotActiveError(VibeStackError):
    """Raised when attempting to deactivate or use a domain that is not active.

    Examples:
        >>> raise DomainNotActiveError("domain 'game-dev/unity' is not active")
    """


class StackNotFoundError(VibeStackError):
    """Raised when a requested stack does not exist.

    Examples:
        >>> raise StackNotFoundError("stack 'game-dev' not found")
    """


class ConfigMergeError(VibeStackError):
    """Raised when merging configuration files fails.

    Examples:
        >>> raise ConfigMergeError("failed to merge opencode.json")
    """


class MCPResolveError(VibeStackError):
    """Raised when an MCP server reference cannot be resolved.

    Examples:
        >>> raise MCPResolveError("unresolved MCP server: data-forge")
    """


class StateFileError(VibeStackError):
    """Raised when the state file cannot be read, written, or is corrupt.

    Examples:
        >>> raise StateFileError("corrupt state file")
    """


class SyncError(VibeStackError):
    """Raised when symlink synchronisation fails.

    Examples:
        >>> raise SyncError("symlink sync failed")
    """
