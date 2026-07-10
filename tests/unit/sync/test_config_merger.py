"""Tests for config merger (RED phase — TDD).

Tests the three functions of config_merger.py:
    merge_instructions, merge_skills_paths, merge_mcp_servers.
"""

from __future__ import annotations

import pytest

from vibe_stack.errors import ConfigMergeError


# ============================================================================
# merge_instructions
# ============================================================================


class TestMergeInstructions:
    """Tests for merge_instructions()."""

    @staticmethod
    def _call(current: list[str], namespace: str, mode: str) -> list[str]:
        from vibe_stack.sync.config_merger import merge_instructions

        return merge_instructions(current, namespace, mode)

    def test_appends_entry_when_adding_and_not_present(self) -> None:
        """mode="add": appends ".opencode/rules/{namespace}/*.md" if not present."""
        result = self._call(
            current=["rules/global.md"],
            namespace="dcc_blender",
            mode="add",
        )
        assert result == [
            "rules/global.md",
            ".opencode/rules/dcc_blender/*.md",
        ]

    def test_does_not_duplicate_when_entry_already_present(self) -> None:
        """mode="add": does NOT duplicate if already present."""
        result = self._call(
            current=[
                "rules/global.md",
                ".opencode/rules/dcc_blender/*.md",
            ],
            namespace="dcc_blender",
            mode="add",
        )
        assert result == [
            "rules/global.md",
            ".opencode/rules/dcc_blender/*.md",
        ]

    def test_preserves_existing_entries_and_adds_at_end(self) -> None:
        """mode="add": preserves existing entries, only adds at end."""
        result = self._call(
            current=["a.md", "b.md"],
            namespace="ns_test",
            mode="add",
        )
        assert result == ["a.md", "b.md", ".opencode/rules/ns_test/*.md"]

    def test_removes_entry_when_found(self) -> None:
        """mode="remove": removes ".opencode/rules/{namespace}/*.md" entry."""
        result = self._call(
            current=[
                "a.md",
                ".opencode/rules/dcc_blender/*.md",
                "b.md",
            ],
            namespace="dcc_blender",
            mode="remove",
        )
        assert result == ["a.md", "b.md"]

    def test_returns_unchanged_list_when_entry_not_found_on_remove(self) -> None:
        """mode="remove": returns unchanged list if entry not found."""
        result = self._call(
            current=["a.md", "b.md"],
            namespace="dcc_blender",
            mode="remove",
        )
        assert result == ["a.md", "b.md"]

    def test_preserves_other_entries_on_remove(self) -> None:
        """mode="remove": preserves other entries."""
        result = self._call(
            current=[
                ".opencode/rules/dcc_blender/*.md",
                "other.md",
            ],
            namespace="dcc_blender",
            mode="remove",
        )
        assert result == ["other.md"]

    def test_handles_empty_current_list_on_add(self) -> None:
        """Handles empty current list on add."""
        result = self._call(
            current=[],
            namespace="ns",
            mode="add",
        )
        assert result == [".opencode/rules/ns/*.md"]

    def test_handles_empty_current_list_on_remove(self) -> None:
        """Handles empty current list on remove."""
        result = self._call(
            current=[],
            namespace="ns",
            mode="remove",
        )
        assert result == []

    def test_raises_config_merge_error_for_invalid_mode(self) -> None:
        """Raises ConfigMergeError for invalid mode."""
        with pytest.raises(ConfigMergeError):
            self._call(current=[], namespace="ns", mode="invalid")

    def test_does_not_mutate_input_list(self) -> None:
        """Returns a new list — does not mutate the input."""
        original = ["a.md"]
        result = self._call(original, namespace="ns", mode="add")
        assert original == ["a.md"]
        assert result is not original


# ============================================================================
# merge_skills_paths
# ============================================================================


class TestMergeSkillsPaths:
    """Tests for merge_skills_paths()."""

    @staticmethod
    def _call(current: list[str], namespace: str, mode: str) -> list[str]:
        from vibe_stack.sync.config_merger import merge_skills_paths

        return merge_skills_paths(current, namespace, mode)

    def test_appends_entry_when_adding_and_not_present(self) -> None:
        """mode="add": appends ".opencode/skills/{namespace}" if not present."""
        result = self._call(
            current=["~/.config/opencode/skills/my-skill"],
            namespace="dcc_blender",
            mode="add",
        )
        assert result == [
            "~/.config/opencode/skills/my-skill",
            ".opencode/skills/dcc_blender",
        ]

    def test_does_not_duplicate_when_entry_already_present(self) -> None:
        """mode="add": no duplicates."""
        result = self._call(
            current=[
                "~/.config/opencode/skills/a",
                ".opencode/skills/dcc_blender",
            ],
            namespace="dcc_blender",
            mode="add",
        )
        assert result == [
            "~/.config/opencode/skills/a",
            ".opencode/skills/dcc_blender",
        ]

    def test_removes_entry_when_found(self) -> None:
        """mode="remove": removes ".opencode/skills/{namespace}"."""
        result = self._call(
            current=[
                "a",
                ".opencode/skills/dcc_blender",
                "b",
            ],
            namespace="dcc_blender",
            mode="remove",
        )
        assert result == ["a", "b"]

    def test_preserves_users_own_entries(self) -> None:
        """Preserves user's own skills.paths entries."""
        result = self._call(
            current=["/home/user/my-skill", "/shared/team-skill"],
            namespace="dcc_blender",
            mode="add",
        )
        assert result == [
            "/home/user/my-skill",
            "/shared/team-skill",
            ".opencode/skills/dcc_blender",
        ]

    def test_returns_unchanged_list_when_entry_not_found_on_remove(self) -> None:
        """mode="remove": returns unchanged list if entry not found."""
        result = self._call(
            current=["a"],
            namespace="dcc_blender",
            mode="remove",
        )
        assert result == ["a"]

    def test_handles_empty_current_list_on_add(self) -> None:
        """Handles empty current list on add."""
        result = self._call(current=[], namespace="ns", mode="add")
        assert result == [".opencode/skills/ns"]

    def test_handles_empty_current_list_on_remove(self) -> None:
        """Handles empty current list on remove."""
        result = self._call(current=[], namespace="ns", mode="remove")
        assert result == []

    def test_raises_config_merge_error_for_invalid_mode(self) -> None:
        """Raises ConfigMergeError for invalid mode."""
        with pytest.raises(ConfigMergeError):
            self._call(current=[], namespace="ns", mode="invalid")

    def test_does_not_mutate_input_list(self) -> None:
        """Returns a new list — does not mutate the input."""
        original = ["a"]
        result = self._call(original, namespace="ns", mode="add")
        assert original == ["a"]
        assert result is not original


# ============================================================================
# merge_mcp_servers
# ============================================================================


class TestMergeMcpServers:
    """Tests for merge_mcp_servers()."""

    @staticmethod
    def _call(
        current: dict, entries: dict, mode: str
    ) -> dict:
        from vibe_stack.sync.config_merger import merge_mcp_servers

        return merge_mcp_servers(current, entries, mode)

    def test_adds_entries_prefixed_with_vibe(self) -> None:
        """mode="add": adds entries, prefixed with "vibe:"."""
        result = self._call(
            current={},
            entries={"data-forge": {"command": "foo"}},
            mode="add",
        )
        assert result == {"vibe:data-forge": {"command": "foo"}}

    def test_preserves_user_mcp_servers_on_add(self) -> None:
        """mode="add": only touches keys starting with "vibe:" — preserves user MCP."""
        result = self._call(
            current={
                "my-server": {"command": "node"},
                "vibe:old-entry": {"command": "old"},
            },
            entries={"data-forge": {"command": "foo"}},
            mode="add",
        )
        assert result["my-server"] == {"command": "node"}
        assert result["vibe:data-forge"] == {"command": "foo"}

    def test_replaces_existing_vibe_entries_with_same_key(self) -> None:
        """mode="add": replaces existing vibe: entries with same key."""
        result = self._call(
            current={
                "vibe:data-forge": {"command": "old"},
            },
            entries={"data-forge": {"command": "new"}},
            mode="add",
        )
        assert result == {"vibe:data-forge": {"command": "new"}}

    def test_removes_entries_by_exact_key_match(self) -> None:
        """mode="remove": removes all entries whose keys match (by key, not prefix)."""
        result = self._call(
            current={
                "vibe:data-forge": {"command": "foo"},
                "vibe:blender": {"command": "bar"},
                "my-server": {"command": "node"},
            },
            entries={"vibe:data-forge": {}, "vibe:blender": {}},
            mode="remove",
        )
        assert result == {"my-server": {"command": "node"}}

    def test_never_touches_non_vibe_keys_on_remove(self) -> None:
        """mode="remove": never touches non-"vibe:" keys."""
        result = self._call(
            current={
                "my-server": {"command": "node"},
                "vibe:data-forge": {"command": "foo"},
            },
            entries={"vibe:data-forge": {}},
            mode="remove",
        )
        assert result == {"my-server": {"command": "node"}}
        assert "vibe:data-forge" not in result

    def test_handles_empty_current_dict_on_add(self) -> None:
        """Handles empty current dict on add."""
        result = self._call(
            current={},
            entries={"svc": {"command": "x"}},
            mode="add",
        )
        assert result == {"vibe:svc": {"command": "x"}}

    def test_handles_empty_current_dict_on_remove(self) -> None:
        """Handles empty current dict on remove."""
        result = self._call(
            current={},
            entries={"vibe:svc": {}},
            mode="remove",
        )
        assert result == {}

    def test_handles_empty_entries_dict_on_add(self) -> None:
        """When entries dict is empty on add, returns copy of current."""
        current = {"my-server": {"command": "node"}}
        result = self._call(current, entries={}, mode="add")
        assert result == current
        assert result is not current

    def test_raises_config_merge_error_for_invalid_mode(self) -> None:
        """Raises ConfigMergeError for invalid mode."""
        with pytest.raises(ConfigMergeError):
            self._call(current={}, entries={}, mode="invalid")

    def test_does_not_mutate_input_dict(self) -> None:
        """Returns a new dict — does not mutate the input."""
        original = {"a": 1}
        result = self._call(original, entries={}, mode="add")
        assert original == {"a": 1}
        assert result is not original

    def test_preserves_untouched_user_keys_on_add(self) -> None:
        """mode="add": user keys remain completely untouched."""
        result = self._call(
            current={
                "my-server": {"command": "node"},
                "another": {"command": "python"},
            },
            entries={"data-forge": {"command": "foo"}},
            mode="add",
        )
        assert len(result) == 3
        assert result["my-server"] == {"command": "node"}
        assert result["another"] == {"command": "python"}
        assert result["vibe:data-forge"] == {"command": "foo"}
