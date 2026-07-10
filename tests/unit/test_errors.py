"""Tests for the vibe-stack exception hierarchy."""

from __future__ import annotations

from vibe_stack.errors import (
    ConfigMergeError,
    DomainAlreadyActiveError,
    DomainNotFoundError,
    DomainNotActiveError,
    MCPResolveError,
    StackNotFoundError,
    StateFileError,
    SyncError,
    VibeStackError,
)


class TestVibeStackError:
    """Tests for the base VibeStackError exception."""

    def test_is_exception_subclass(self) -> None:
        """VibeStackError should inherit from Exception."""
        assert issubclass(VibeStackError, Exception)

    def test_can_raise_with_message(self) -> None:
        """VibeStackError should be raiseable with a message string."""
        raised = False
        try:
            raise VibeStackError("something went wrong")
        except VibeStackError as e:
            raised = True
            assert str(e) == "something went wrong"
        assert raised

    def test_message_preserved(self) -> None:
        """The message passed to VibeStackError should be preserved."""
        err = VibeStackError("test message")
        assert str(err) == "test message"
        assert err.args[0] == "test message"


class TestDomainNotFoundError:
    """Tests for DomainNotFoundError."""

    def test_inherits_vibe_stack_error(self) -> None:
        assert issubclass(DomainNotFoundError, VibeStackError)

    def test_can_raise_with_message(self) -> None:
        try:
            raise DomainNotFoundError("domain 'ai/data-forge' not found")
        except DomainNotFoundError as e:
            assert str(e) == "domain 'ai/data-forge' not found"

    def test_catch_as_vibe_stack_error(self) -> None:
        """Should be catchable as VibeStackError."""
        try:
            raise DomainNotFoundError("missing domain")
        except VibeStackError:
            pass


class TestDomainAlreadyActiveError:
    """Tests for DomainAlreadyActiveError."""

    def test_inherits_vibe_stack_error(self) -> None:
        assert issubclass(DomainAlreadyActiveError, VibeStackError)

    def test_can_raise_with_message(self) -> None:
        try:
            raise DomainAlreadyActiveError("domain 'dcc/blender' is already active")
        except DomainAlreadyActiveError as e:
            assert str(e) == "domain 'dcc/blender' is already active"

    def test_catch_as_vibe_stack_error(self) -> None:
        try:
            raise DomainAlreadyActiveError("duplicate domain")
        except VibeStackError:
            pass


class TestDomainNotActiveError:
    """Tests for DomainNotActiveError."""

    def test_inherits_vibe_stack_error(self) -> None:
        assert issubclass(DomainNotActiveError, VibeStackError)

    def test_can_raise_with_message(self) -> None:
        try:
            raise DomainNotActiveError("domain 'game-dev/unity' is not active")
        except DomainNotActiveError as e:
            assert str(e) == "domain 'game-dev/unity' is not active"

    def test_catch_as_vibe_stack_error(self) -> None:
        try:
            raise DomainNotActiveError("inactive domain")
        except VibeStackError:
            pass


class TestStackNotFoundError:
    """Tests for StackNotFoundError."""

    def test_inherits_vibe_stack_error(self) -> None:
        assert issubclass(StackNotFoundError, VibeStackError)

    def test_can_raise_with_message(self) -> None:
        try:
            raise StackNotFoundError("stack 'game-dev' not found")
        except StackNotFoundError as e:
            assert str(e) == "stack 'game-dev' not found"

    def test_catch_as_vibe_stack_error(self) -> None:
        try:
            raise StackNotFoundError("missing stack")
        except VibeStackError:
            pass


class TestConfigMergeError:
    """Tests for ConfigMergeError."""

    def test_inherits_vibe_stack_error(self) -> None:
        assert issubclass(ConfigMergeError, VibeStackError)

    def test_can_raise_with_message(self) -> None:
        try:
            raise ConfigMergeError("failed to merge opencode.json")
        except ConfigMergeError as e:
            assert str(e) == "failed to merge opencode.json"

    def test_catch_as_vibe_stack_error(self) -> None:
        try:
            raise ConfigMergeError("merge failure")
        except VibeStackError:
            pass


class TestMCPResolveError:
    """Tests for MCPResolveError."""

    def test_inherits_vibe_stack_error(self) -> None:
        assert issubclass(MCPResolveError, VibeStackError)

    def test_can_raise_with_message(self) -> None:
        try:
            raise MCPResolveError("unresolved MCP server: data-forge")
        except MCPResolveError as e:
            assert str(e) == "unresolved MCP server: data-forge"

    def test_catch_as_vibe_stack_error(self) -> None:
        try:
            raise MCPResolveError("mcp error")
        except VibeStackError:
            pass


class TestStateFileError:
    """Tests for StateFileError."""

    def test_inherits_vibe_stack_error(self) -> None:
        assert issubclass(StateFileError, VibeStackError)

    def test_can_raise_with_message(self) -> None:
        try:
            raise StateFileError("corrupt state file")
        except StateFileError as e:
            assert str(e) == "corrupt state file"

    def test_catch_as_vibe_stack_error(self) -> None:
        try:
            raise StateFileError("state error")
        except VibeStackError:
            pass


class TestSyncError:
    """Tests for SyncError."""

    def test_inherits_vibe_stack_error(self) -> None:
        assert issubclass(SyncError, VibeStackError)

    def test_can_raise_with_message(self) -> None:
        try:
            raise SyncError("symlink sync failed")
        except SyncError as e:
            assert str(e) == "symlink sync failed"

    def test_catch_as_vibe_stack_error(self) -> None:
        try:
            raise SyncError("sync error")
        except VibeStackError:
            pass
