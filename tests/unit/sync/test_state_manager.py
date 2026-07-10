"""Tests for state file manager (RED phase — TDD).

Tests the six functions of state_manager.py:
    read_state, write_state, add_domain, remove_domain,
    list_active_domains, ensure_state_file.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from vibe_stack.errors import StateFileError
from vibe_stack.model.state import ActivationState, DomainState
from vibe_stack.sync.state_manager import (
    add_domain,
    ensure_state_file,
    list_active_domains,
    read_state,
    remove_domain,
    write_state,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _state_file_root(tmp_path: Path) -> Path:
    """Return the project root with ".opencode/" created inside."""
    root = tmp_path / "project"
    (root / ".opencode").mkdir(parents=True, exist_ok=True)
    return root


def _write_raw_state(root: Path, content: str) -> None:
    """Write raw JSON string to the state file."""
    sf = root / ".opencode" / ".vibe-stack-state.json"
    sf.write_text(content, encoding="utf-8")


def _make_domain_state(key: str) -> DomainState:
    """Build a minimal DomainState for a given key."""
    ns = key.replace("/", "_")
    return DomainState(
        domain_key=key,
        namespace=ns,
        activated_at="2025-07-10T12:00:00Z",
    )


# ---------------------------------------------------------------------------
# read_state
# ---------------------------------------------------------------------------


class TestReadState:
    """Tests for read_state()."""

    def test_returns_default_activation_state_for_missing_file(
        self, tmp_path: Path
    ) -> None:
        """Given no state file, read_state should return default ActivationState."""
        root = _state_file_root(tmp_path)
        result = read_state(root)
        assert isinstance(result, ActivationState)
        assert result.version == 2
        assert result.domains == {}

    def test_returns_correct_state_for_valid_file(
        self, tmp_path: Path
    ) -> None:
        """Given a valid state file, read_state should return correct data."""
        root = _state_file_root(tmp_path)
        ds = _make_domain_state("dcc/blender")
        expected = ActivationState(
            version=2,
            domains={ds.domain_key: ds},
        )
        _write_raw_state(root, json.dumps(asdict(expected)))

        result = read_state(root)
        assert result.version == 2
        assert "dcc/blender" in result.domains
        assert result.domains["dcc/blender"].domain_key == "dcc/blender"
        assert result.domains["dcc/blender"].namespace == "dcc_blender"

    def test_raises_state_file_error_for_corrupted_json(
        self, tmp_path: Path
    ) -> None:
        """Given a corrupted JSON file, read_state should raise StateFileError."""
        root = _state_file_root(tmp_path)
        _write_raw_state(root, "this is not valid {{{ json")

        with pytest.raises(StateFileError):
            read_state(root)

    def test_returns_empty_state_for_empty_file(
        self, tmp_path: Path
    ) -> None:
        """Given an empty file, read_state should return default ActivationState."""
        root = _state_file_root(tmp_path)
        _write_raw_state(root, "")

        result = read_state(root)
        assert isinstance(result, ActivationState)
        assert result.version == 2
        assert result.domains == {}


# ---------------------------------------------------------------------------
# write_state
# ---------------------------------------------------------------------------


class TestWriteState:
    """Tests for write_state()."""

    def test_creates_valid_json_file(self, tmp_path: Path) -> None:
        """Given an ActivationState, write_state should create a valid JSON file."""
        root = _state_file_root(tmp_path)
        ds = _make_domain_state("ai/data-forge")
        state = ActivationState(domains={ds.domain_key: ds})

        write_state(root, state)

        sf = root / ".opencode" / ".vibe-stack-state.json"
        assert sf.exists()

        raw = json.loads(sf.read_text(encoding="utf-8"))
        assert raw["version"] == 2
        assert "ai/data-forge" in raw["domains"]
        assert raw["domains"]["ai/data-forge"]["domain_key"] == "ai/data-forge"

    def test_round_trip_write_then_read(self, tmp_path: Path) -> None:
        """Given a state, write then read should return equivalent data."""
        root = _state_file_root(tmp_path)
        ds = _make_domain_state("game-dev/unity")
        original = ActivationState(domains={ds.domain_key: ds})

        write_state(root, original)
        restored = read_state(root)

        assert restored.version == original.version
        assert list(restored.domains.keys()) == list(original.domains.keys())
        restored_ds = restored.domains["game-dev/unity"]
        assert restored_ds.domain_key == ds.domain_key
        assert restored_ds.namespace == ds.namespace
        assert restored_ds.activated_at == ds.activated_at
        assert restored_ds.files == ds.files
        assert restored_ds.directories == ds.directories
        assert restored_ds.opencode_entries == ds.opencode_entries


# ---------------------------------------------------------------------------
# add_domain
# ---------------------------------------------------------------------------


class TestAddDomain:
    """Tests for add_domain()."""

    def test_adds_new_domain_to_activation_state(self) -> None:
        """Given an empty state, add_domain should insert a new DomainState."""
        state = ActivationState()
        ds = _make_domain_state("dcc/maya")

        add_domain(state, ds)

        assert "dcc/maya" in state.domains
        assert state.domains["dcc/maya"] is ds

    def test_overwrites_existing_domain_with_same_key(self) -> None:
        """Given an existing domain key, add_domain should overwrite it."""
        ds_old = _make_domain_state("dcc/houdini")
        state = ActivationState(domains={"dcc/houdini": ds_old})

        ds_new = DomainState(
            domain_key="dcc/houdini",
            namespace="dcc_houdini",
            activated_at="2026-01-01T00:00:00Z",
            files=["rules/houdini.md"],
        )

        add_domain(state, ds_new)

        assert "dcc/houdini" in state.domains
        assert state.domains["dcc/houdini"] is ds_new
        assert state.domains["dcc/houdini"].files == ["rules/houdini.md"]


# ---------------------------------------------------------------------------
# remove_domain
# ---------------------------------------------------------------------------


class TestRemoveDomain:
    """Tests for remove_domain()."""

    def test_returns_true_and_removes_existing_key(self) -> None:
        """Given an existing key, remove_domain should return True and remove it."""
        ds = _make_domain_state("ai/data-forge")
        state = ActivationState(domains={ds.domain_key: ds})

        result = remove_domain(state, "ai/data-forge")

        assert result is True
        assert "ai/data-forge" not in state.domains

    def test_returns_false_for_non_existent_key(self) -> None:
        """Given a non-existent key, remove_domain should return False."""
        state = ActivationState()

        result = remove_domain(state, "no/such-domain")

        assert result is False
        assert state.domains == {}


# ---------------------------------------------------------------------------
# list_active_domains
# ---------------------------------------------------------------------------


class TestListActiveDomains:
    """Tests for list_active_domains()."""

    def test_returns_sorted_list_of_domain_keys(
        self, tmp_path: Path
    ) -> None:
        """Given a state with multiple domains, should return sorted keys."""
        root = _state_file_root(tmp_path)
        ds_a = _make_domain_state("dcc/blender")
        ds_b = _make_domain_state("ai/data-forge")
        ds_c = _make_domain_state("game-dev/unity")
        state = ActivationState(
            domains={
                ds_c.domain_key: ds_c,
                ds_a.domain_key: ds_a,
                ds_b.domain_key: ds_b,
            }
        )
        write_state(root, state)

        result = list_active_domains(root)

        assert result == ["ai/data-forge", "dcc/blender", "game-dev/unity"]

    def test_returns_empty_list_when_no_domains_active(
        self, tmp_path: Path
    ) -> None:
        """Given an empty state, list_active_domains should return empty list."""
        root = _state_file_root(tmp_path)
        write_state(root, ActivationState())

        result = list_active_domains(root)

        assert result == []

    def test_returns_empty_list_when_file_missing(
        self, tmp_path: Path
    ) -> None:
        """Given no state file, list_active_domains should return empty list."""
        root = _state_file_root(tmp_path)

        result = list_active_domains(root)

        assert result == []


# ---------------------------------------------------------------------------
# ensure_state_file
# ---------------------------------------------------------------------------


class TestEnsureStateFile:
    """Tests for ensure_state_file()."""

    def test_creates_file_if_missing(self, tmp_path: Path) -> None:
        """Given no state file, ensure_state_file should create one."""
        root = _state_file_root(tmp_path)
        sf = root / ".opencode" / ".vibe-stack-state.json"
        assert not sf.exists()

        result = ensure_state_file(root)

        assert isinstance(result, ActivationState)
        assert result.version == 2
        assert result.domains == {}
        assert sf.exists()

    def test_returns_existing_state_if_file_exists(
        self, tmp_path: Path
    ) -> None:
        """Given an existing state file, ensure_state_file should return it."""
        root = _state_file_root(tmp_path)
        ds = _make_domain_state("dcc/photoshop")
        existing = ActivationState(domains={ds.domain_key: ds})
        write_state(root, existing)

        result = ensure_state_file(root)

        assert result.version == 2
        assert "dcc/photoshop" in result.domains
        assert result.domains["dcc/photoshop"].domain_key == "dcc/photoshop"


# ---------------------------------------------------------------------------
# Integration — full lifecycle
# ---------------------------------------------------------------------------


class TestIntegrationFullLifecycle:
    """Integration test: add → read → remove → read full cycle."""

    def test_add_read_remove_read_cycle(self, tmp_path: Path) -> None:
        """Full lifecycle: activate domain, persist, verify, deactivate, verify."""
        root = _state_file_root(tmp_path)

        # Start with ensure_state_file
        state = ensure_state_file(root)
        assert state.domains == {}

        # Add two domains
        add_domain(state, _make_domain_state("dcc/blender"))
        add_domain(state, _make_domain_state("ai/data-forge"))
        write_state(root, state)

        # Read back and verify both present
        restored = read_state(root)
        assert len(restored.domains) == 2
        assert sorted(restored.domains.keys()) == ["ai/data-forge", "dcc/blender"]

        # list_active_domains should match
        assert list_active_domains(root) == ["ai/data-forge", "dcc/blender"]

        # Remove one domain
        removed = remove_domain(state, "dcc/blender")
        assert removed is True
        write_state(root, state)

        # Read back — only one remains
        restored2 = read_state(root)
        assert len(restored2.domains) == 1
        assert "dcc/blender" not in restored2.domains
        assert "ai/data-forge" in restored2.domains

        # list_active_domains after removal
        assert list_active_domains(root) == ["ai/data-forge"]
