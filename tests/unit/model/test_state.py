"""Tests for state data model dataclasses."""

from __future__ import annotations

from dataclasses import asdict, replace

from vibe_stack.model.state import ActivationState, DomainState


class TestActivationState:
    """Tests for ActivationState dataclass."""

    def test_defaults(self) -> None:
        """ActivationState should default to version=2 and empty domains."""
        state = ActivationState()
        assert state.version == 2
        assert state.domains == {}

    def test_is_dataclass(self) -> None:
        """ActivationState should be a stdlib dataclass."""
        from dataclasses import is_dataclass

        assert is_dataclass(ActivationState)

    def test_add_domain_state(self) -> None:
        """ActivationState should accept DomainState instances in domains dict."""
        ds = DomainState(
            domain_key="dcc/blender",
            namespace="dcc_blender",
            activated_at="2025-01-01T00:00:00Z",
            files=["rules/blender.md"],
            directories=["skills/blender-tips"],
            opencode_entries={
                "instructions": ["dcc_blender/instructions.md"],
            },
        )
        state = ActivationState(domains={"dcc/blender": ds})
        assert "dcc/blender" in state.domains
        assert state.domains["dcc/blender"].namespace == "dcc_blender"

    def test_multiple_domains(self) -> None:
        """ActivationState should hold multiple DomainState entries."""
        ds1 = DomainState(
            domain_key="dcc/blender",
            namespace="dcc_blender",
            activated_at="2025-01-01T00:00:00Z",
        )
        ds2 = DomainState(
            domain_key="ai/data-forge",
            namespace="ai_data-forge",
            activated_at="2025-01-02T00:00:00Z",
        )
        state = ActivationState(domains={"dcc/blender": ds1, "ai/data-forge": ds2})
        assert len(state.domains) == 2


class TestDomainState:
    """Tests for DomainState dataclass."""

    def test_basic_construction(self) -> None:
        """DomainState should hold activation metadata for a single domain."""
        ds = DomainState(
            domain_key="dcc/blender",
            namespace="dcc_blender",
            activated_at="2025-07-10T12:00:00Z",
        )
        assert ds.domain_key == "dcc/blender"
        assert ds.namespace == "dcc_blender"
        assert ds.activated_at == "2025-07-10T12:00:00Z"
        assert ds.files == []
        assert ds.directories == []
        assert ds.opencode_entries == {}

    def test_is_dataclass(self) -> None:
        """DomainState should be a stdlib dataclass."""
        from dataclasses import is_dataclass

        assert is_dataclass(DomainState)

    def test_opencode_entries_example(self) -> None:
        """DomainState.opencode_entries should support instructions, skills, mcp."""
        ds = DomainState(
            domain_key="ai/data-forge",
            namespace="ai_data-forge",
            activated_at="2025-01-01T00:00:00Z",
            opencode_entries={
                "instructions": ["ai_data-forge/instructions.md"],
                "skills.paths": ["domains/ai/data-forge/skills/data-pipeline"],
                "mcpServers": ["data-forge"],
            },
        )
        assert ds.opencode_entries["instructions"] == ["ai_data-forge/instructions.md"]
        assert ds.opencode_entries["skills.paths"] == ["domains/ai/data-forge/skills/data-pipeline"]
        assert ds.opencode_entries["mcpServers"] == ["data-forge"]

    def test_files_and_directories_rel_paths(self) -> None:
        """DomainState files and directories should use relative paths."""
        ds = DomainState(
            domain_key="dcc/maya",
            namespace="dcc_maya",
            activated_at="2025-06-15T08:30:00Z",
            files=["rules/dcc_maya/maya.md", "agents/dcc_maya/rigger.md"],
            directories=["skills/dcc_maya/maya-scripting"],
        )
        assert len(ds.files) == 2
        assert len(ds.directories) == 1
        assert ds.files[0] == "rules/dcc_maya/maya.md"

    def test_serialize_deserialize_round_trip(self) -> None:
        """DomainState should survive asdict → replace round-trip."""
        ds = DomainState(
            domain_key="dcc/blender",
            namespace="dcc_blender",
            activated_at="2025-01-01T00:00:00Z",
            files=["rules/blender.md"],
            directories=["skills/blender-tips"],
            opencode_entries={"instructions": ["blender_instructions"]},
        )
        d = asdict(ds)
        assert d["domain_key"] == "dcc/blender"
        assert d["namespace"] == "dcc_blender"
        assert d["files"] == ["rules/blender.md"]
        assert d["opencode_entries"]["instructions"] == ["blender_instructions"]

        # Reconstruct via replace confirms it's a proper dataclass
        restored = replace(ds, domain_key="dcc/maya")
        assert restored.domain_key == "dcc/maya"
        assert restored.namespace == "dcc_blender"
