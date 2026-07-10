"""Tests for MCP data model dataclasses."""

from __future__ import annotations

from vibe_stack.model.mcp import MCPServerEntry


class TestMCPServerEntry:
    """Tests for MCPServerEntry dataclass."""

    def test_defaults(self) -> None:
        """MCPServerEntry should default type='local', enabled=True, extra={}."""
        entry = MCPServerEntry(name="data-forge")
        assert entry.name == "data-forge"
        assert entry.type == "local"
        assert entry.command is None
        assert entry.enabled is True
        assert entry.extra == {}

    def test_is_dataclass(self) -> None:
        """MCPServerEntry should be a stdlib dataclass."""
        from dataclasses import is_dataclass

        assert is_dataclass(MCPServerEntry)

    def test_with_command_local(self) -> None:
        """MCPServerEntry should support local type with command list."""
        entry = MCPServerEntry(
            name="data-forge",
            type="local",
            command=["python", "-m", "data_forge", "--port", "8080"],
        )
        assert entry.name == "data-forge"
        assert entry.type == "local"
        assert entry.enabled is True
        assert entry.command == ["python", "-m", "data_forge", "--port", "8080"]

    def test_remote_type(self) -> None:
        """MCPServerEntry should support type='remote' with no command."""
        entry = MCPServerEntry(name="remote-api", type="remote")
        assert entry.name == "remote-api"
        assert entry.type == "remote"
        assert entry.command is None
        assert entry.enabled is True

    def test_disabled_entry(self) -> None:
        """MCPServerEntry should support enabled=False."""
        entry = MCPServerEntry(name="deprecated-server", enabled=False)
        assert entry.enabled is False

    def test_extra_fields(self) -> None:
        """MCPServerEntry.extra should accept arbitrary dict for future extension."""
        entry = MCPServerEntry(
            name="data-forge",
            extra={
                "env": {"DATA_FORGE_HOME": "/opt/data-forge"},
                "timeout": 30000,
                "auto_restart": True,
            },
        )
        assert entry.extra["env"] == {"DATA_FORGE_HOME": "/opt/data-forge"}
        assert entry.extra["timeout"] == 30000
        assert entry.extra["auto_restart"] is True

    def test_repr_includes_name(self) -> None:
        """MCPServerEntry repr should include the server name."""
        entry = MCPServerEntry(name="data-forge")
        r = repr(entry)
        assert "data-forge" in r
