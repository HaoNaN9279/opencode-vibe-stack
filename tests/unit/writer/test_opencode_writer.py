"""Tests for OpenCode JSON writer — the ONLY module that touches opencode.json.

Tests read_opencode(), write_opencode(), and merge_vibe_entries().
Follows TDD: tests written first (RED), then implementation (GREEN).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vibe_stack.errors import VibeStackError


# ============================================================================
# read_opencode
# ============================================================================


class TestReadOpencode:
    """Tests for read_opencode()."""

    @staticmethod
    def _call(path: Path) -> dict:
        from vibe_stack.writer.opencode_writer import read_opencode

        return read_opencode(path)

    def test_reads_valid_jsonc_and_returns_dict(self, tmp_path: Path) -> None:
        """Given a valid JSONC file, returns parsed dict."""
        path = tmp_path / "opencode.json"
        path.write_text('{\n  "instructions": ["rules/*.md"],\n  "version": 1\n}\n')
        result = self._call(path)
        assert result == {"instructions": ["rules/*.md"], "version": 1}

    def test_reads_jsonc_with_comments(self, tmp_path: Path) -> None:
        """Given JSONC with // and /* */ comments, parses correctly."""
        path = tmp_path / "opencode.json"
        path.write_text(
            "{\n"
            '  // main instructions\n'
            '  "instructions": ["~/.config/opencode/rules/*.md"],\n'
            '  "skills": {\n'
            '    /* user skill paths */\n'
            '    "paths": ["skills"]\n'
            "  }\n"
            "}\n"
        )
        result = self._call(path)
        assert result["instructions"] == ["~/.config/opencode/rules/*.md"]
        assert result["skills"]["paths"] == ["skills"]

    def test_returns_empty_dict_for_missing_file(self, tmp_path: Path) -> None:
        """Given a path that does not exist, returns {} without creating file."""
        missing = tmp_path / "nonexistent.json"
        result = self._call(missing)
        assert result == {}
        assert not missing.exists()

    def test_returns_empty_dict_for_empty_file(self, tmp_path: Path) -> None:
        """Given an empty file, returns {}."""
        path = tmp_path / "opencode.json"
        path.write_text("")
        result = self._call(path)
        assert result == {}

    def test_raises_vibe_stack_error_for_corrupt_json(self, tmp_path: Path) -> None:
        """Given corrupt JSON that cannot be parsed, raises VibeStackError."""
        path = tmp_path / "opencode.json"
        path.write_text("{ this is not valid json @@@ }")
        with pytest.raises(VibeStackError):
            self._call(path)


# ============================================================================
# write_opencode
# ============================================================================


class TestWriteOpencode:
    """Tests for write_opencode()."""

    @staticmethod
    def _call(path: Path, config: dict) -> None:
        from vibe_stack.writer.opencode_writer import write_opencode

        write_opencode(path, config)

    def test_writes_dict_as_formatted_json(self, tmp_path: Path) -> None:
        """Given a dict, writes formatted JSON with indent=2."""
        path = tmp_path / "opencode.json"
        config = {"instructions": ["~/.config/opencode/rules/*.md"], "version": 1}
        self._call(path, config)
        written = json.loads(path.read_text(encoding="utf-8"))
        assert written == config

    def test_creates_parent_directory_if_missing(self, tmp_path: Path) -> None:
        """Given a path with non-existent parent dir, creates it."""
        path = tmp_path / "subdir" / "opencode.json"
        config = {"key": "value"}
        self._call(path, config)
        assert path.exists()
        assert json.loads(path.read_text(encoding="utf-8")) == config

    def test_overwrites_existing_file(self, tmp_path: Path) -> None:
        """Given an existing file, overwrites it completely."""
        path = tmp_path / "opencode.json"
        path.write_text('{"old": "data"}')
        config = {"new": "content"}
        self._call(path, config)
        written = json.loads(path.read_text(encoding="utf-8"))
        assert written == {"new": "content"}
        assert "old" not in written

    def test_output_is_valid_json_not_jsonc(self, tmp_path: Path) -> None:
        """Written output is valid JSON (no comments)."""
        path = tmp_path / "opencode.json"
        config = {
            "$schema": "https://opencode.ai/config.json",
            "instructions": ["rules/*.md"],
        }
        self._call(path, config)
        raw = path.read_text(encoding="utf-8")
        # Must parse as JSON
        parsed = json.loads(raw)
        assert parsed == config
        # Must not contain comment markers
        assert "//" not in raw
        assert "/*" not in raw

    def test_preserves_dollar_schema_in_output(self, tmp_path: Path) -> None:
        """Given config with $schema, preserves it in written output."""
        path = tmp_path / "opencode.json"
        config = {
            "$schema": "https://opencode.ai/config.json",
            "instructions": ["rules/*.md"],
            "skills": {"paths": ["skills"]},
        }
        self._call(path, config)
        raw = path.read_text(encoding="utf-8")
        parsed = json.loads(raw)
        assert parsed["$schema"] == "https://opencode.ai/config.json"
        assert parsed["instructions"] == ["rules/*.md"]

    def test_round_trip_write_then_read(self, tmp_path: Path) -> None:
        """Given config written to disk, reading it back returns same data."""
        from vibe_stack.writer.opencode_writer import read_opencode, write_opencode

        path = tmp_path / "opencode.json"
        config = {
            "$schema": "https://opencode.ai/config.json",
            "instructions": ["~/.config/opencode/rules/*.md"],
            "skills": {"paths": ["skills"]},
            "mcp": {"my-server": {"type": "local", "command": ["node", "server.js"]}},
        }
        write_opencode(path, config)
        result = read_opencode(path)
        assert result == config


# ============================================================================
# merge_vibe_entries
# ============================================================================


class TestMergeVibeEntries:
    """Tests for merge_vibe_entries()."""

    @staticmethod
    def _call(
        current: dict,
        add: dict | None = None,
        remove: dict | None = None,
    ) -> dict:
        from vibe_stack.writer.opencode_writer import merge_vibe_entries

        return merge_vibe_entries(current, add, remove)

    # --- add: instructions ---

    def test_adds_instructions_entries_not_already_present(self) -> None:
        """Adds instruction entries that don't already exist."""
        result = self._call(
            current={"instructions": ["existing.md"]},
            add={"instructions": [".opencode/rules/dcc_blender/*.md"]},
        )
        assert result["instructions"] == [
            "existing.md",
            ".opencode/rules/dcc_blender/*.md",
        ]

    def test_does_not_duplicate_existing_instructions(self) -> None:
        """Does not add duplicate instruction entries."""
        result = self._call(
            current={"instructions": [".opencode/rules/dcc_blender/*.md"]},
            add={"instructions": [".opencode/rules/dcc_blender/*.md"]},
        )
        assert result["instructions"] == [".opencode/rules/dcc_blender/*.md"]

    # --- add: skills.paths ---

    def test_adds_skills_paths_under_skills_paths_key(self) -> None:
        """Adds skills.paths entries under the skills.paths key."""
        result = self._call(
            current={"skills": {"paths": ["existing-skill"]}},
            add={"skills.paths": [".opencode/skills/dcc_blender"]},
        )
        assert result["skills"]["paths"] == [
            "existing-skill",
            ".opencode/skills/dcc_blender",
        ]

    def test_does_not_duplicate_existing_skills_paths(self) -> None:
        """Does not add duplicate skills.paths entries."""
        result = self._call(
            current={"skills": {"paths": [".opencode/skills/dcc_blender"]}},
            add={"skills.paths": [".opencode/skills/dcc_blender"]},
        )
        assert result["skills"]["paths"] == [".opencode/skills/dcc_blender"]

    # --- add: MCP servers ---

    def test_adds_mcp_servers_with_vibe_prefix(self) -> None:
        """Adds MCP server entries with 'vibe:' prefix."""
        result = self._call(
            current={"mcp": {"user-server": {"command": ["node"]}}},
            add={"mcpServers": {"data-forge": {"command": ["data-forge"]}}},
        )
        assert "vibe:data-forge" in result["mcp"]
        assert result["mcp"]["vibe:data-forge"] == {"command": ["data-forge"]}

    def test_removes_existing_vibe_mcp_before_adding_new(self) -> None:
        """Removes all existing 'vibe:' MCP entries before adding new ones."""
        result = self._call(
            current={
                "mcp": {
                    "vibe:old-domain": {"command": ["old"]},
                    "vibe:another-old": {"command": ["another-old"]},
                    "user-server": {"command": ["node"]},
                }
            },
            add={"mcpServers": {"data-forge": {"command": ["data-forge"]}}},
        )
        assert "vibe:old-domain" not in result["mcp"]
        assert "vibe:another-old" not in result["mcp"]
        assert result["mcp"]["vibe:data-forge"] == {"command": ["data-forge"]}
        assert result["mcp"]["user-server"] == {"command": ["node"]}

    # --- remove: all ---

    def test_removes_entries_on_deactivate(self) -> None:
        """Removes specified instructions, skills.paths, and MCP entries."""
        result = self._call(
            current={
                "instructions": [
                    "user-rule.md",
                    ".opencode/rules/dcc_blender/*.md",
                ],
                "skills": {
                    "paths": ["user-skill", ".opencode/skills/dcc_blender"]
                },
                "mcp": {
                    "user-server": {"command": ["node"]},
                    "vibe:data-forge": {"command": ["df"]},
                    "vibe:blender": {"command": ["bl"]},
                },
            },
            remove={
                "instructions": [".opencode/rules/dcc_blender/*.md"],
                "skills.paths": [".opencode/skills/dcc_blender"],
                "mcpServers": {"data-forge": {}, "blender": {}},
            },
        )
        assert result["instructions"] == ["user-rule.md"]
        assert result["skills"]["paths"] == ["user-skill"]
        assert "vibe:data-forge" not in result["mcp"]
        assert "vibe:blender" not in result["mcp"]
        assert result["mcp"]["user-server"] == {"command": ["node"]}

    # --- preservation: MCP ---

    def test_preserves_user_mcp_servers_non_vibe_keys(self) -> None:
        """Never modifies non-'vibe:' MCP server entries."""
        result = self._call(
            current={
                "mcp": {
                    "my-server": {"command": ["node"]},
                    "team-server": {"command": ["python"]},
                }
            },
            add={"mcpServers": {"data-forge": {"command": ["df"]}}},
        )
        assert result["mcp"]["my-server"] == {"command": ["node"]}
        assert result["mcp"]["team-server"] == {"command": ["python"]}
        assert result["mcp"]["vibe:data-forge"] == {"command": ["df"]}

    def test_preserves_user_mcp_on_remove(self) -> None:
        """Removing vibe MCP entries never touches user MCP entries."""
        result = self._call(
            current={
                "mcp": {
                    "my-server": {"command": ["node"]},
                    "vibe:data-forge": {"command": ["df"]},
                }
            },
            remove={"mcpServers": {"data-forge": {}}},
        )
        assert result["mcp"] == {"my-server": {"command": ["node"]}}

    # --- preservation: instructions ---

    def test_preserves_user_instructions(self) -> None:
        """User's own instruction entries are never removed by add/remove."""
        result = self._call(
            current={"instructions": ["user-rule.md", "team-rule.md"]},
            add={"instructions": [".opencode/rules/dcc_blender/*.md"]},
        )
        assert "user-rule.md" in result["instructions"]
        assert "team-rule.md" in result["instructions"]
        assert ".opencode/rules/dcc_blender/*.md" in result["instructions"]

    def test_remove_only_removes_specified_instructions(self) -> None:
        """Only removes the specified instruction entries, preserves others."""
        result = self._call(
            current={
                "instructions": [
                    "user-rule.md",
                    ".opencode/rules/dcc_blender/*.md",
                    "other.md",
                ]
            },
            remove={"instructions": [".opencode/rules/dcc_blender/*.md"]},
        )
        assert result["instructions"] == ["user-rule.md", "other.md"]

    # --- preservation: skills.paths ---

    def test_preserves_user_skills_paths(self) -> None:
        """User's own skills.paths entries are preserved."""
        result = self._call(
            current={"skills": {"paths": ["/home/user/my-skill"]}},
            add={"skills.paths": [".opencode/skills/dcc_blender"]},
        )
        assert "/home/user/my-skill" in result["skills"]["paths"]
        assert ".opencode/skills/dcc_blender" in result["skills"]["paths"]

    def test_remove_only_removes_specified_skills_paths(self) -> None:
        """Only removes the specified skills.paths entries."""
        result = self._call(
            current={
                "skills": {
                    "paths": [
                        "user-skill",
                        ".opencode/skills/dcc_blender",
                        "team-skill",
                    ]
                }
            },
            remove={"skills.paths": [".opencode/skills/dcc_blender"]},
        )
        assert result["skills"]["paths"] == ["user-skill", "team-skill"]

    # --- immutability ---

    def test_returns_new_dict_no_mutation(self) -> None:
        """Returns a new dict — never mutates the input."""
        original = {
            "instructions": ["orig.md"],
            "skills": {"paths": ["orig-skill"]},
            "mcp": {"orig-server": {"command": ["node"]}},
        }
        result = self._call(
            original,
            add={
                "instructions": [".opencode/rules/ns/*.md"],
                "skills.paths": [".opencode/skills/ns"],
                "mcpServers": {"ns": {"command": ["x"]}},
            },
        )
        assert result is not original
        assert original["instructions"] == ["orig.md"]
        assert original["skills"]["paths"] == ["orig-skill"]
        assert original["mcp"] == {"orig-server": {"command": ["node"]}}

    # --- edge cases ---

    def test_handles_empty_current_dict(self) -> None:
        """Handles empty current dict gracefully — creates needed keys."""
        result = self._call(
            current={},
            add={
                "instructions": [".opencode/rules/dcc_blender/*.md"],
                "skills.paths": [".opencode/skills/dcc_blender"],
                "mcpServers": {"data-forge": {"command": ["df"]}},
            },
        )
        assert result["instructions"] == [".opencode/rules/dcc_blender/*.md"]
        assert result["skills"]["paths"] == [".opencode/skills/dcc_blender"]
        assert result["mcp"]["vibe:data-forge"] == {"command": ["df"]}

    def test_creates_mcp_key_when_adding_mcp_entries(self) -> None:
        """Creates 'mcp' key in result if MCP entries need to be added."""
        result = self._call(
            current={"instructions": ["rule.md"]},
            add={"mcpServers": {"data-forge": {"command": ["df"]}}},
        )
        assert "mcp" in result
        assert result["mcp"]["vibe:data-forge"] == {"command": ["df"]}
        assert result["instructions"] == ["rule.md"]

    def test_none_add_and_remove_return_copy(self) -> None:
        """When both add and remove are None, returns a deep copy."""
        current = {"instructions": ["a.md"], "skills": {"paths": ["b"]}}
        result = self._call(current)
        assert result == current
        assert result is not current
        assert result["instructions"] is not current["instructions"]

    def test_add_with_no_instructions_creates_empty_list(self) -> None:
        """When adding skills.paths to empty current, only creates needed keys."""
        result = self._call(
            current={},
            add={"skills.paths": [".opencode/skills/ns"]},
        )
        assert result["skills"]["paths"] == [".opencode/skills/ns"]
        # instructions not touched — lazy key creation
        assert "instructions" not in result

    def test_simultaneous_add_and_remove(self) -> None:
        """Add and remove can be applied together."""
        result = self._call(
            current={
                "instructions": [
                    "user-rule.md",
                    ".opencode/rules/old-ns/*.md",
                ],
                "skills": {
                    "paths": ["user-skill", ".opencode/skills/old-ns"]
                },
                "mcp": {
                    "user-server": {"command": ["node"]},
                    "vibe:old-ns": {"command": ["old"]},
                },
            },
            add={
                "instructions": [".opencode/rules/new-ns/*.md"],
                "skills.paths": [".opencode/skills/new-ns"],
                "mcpServers": {"new-ns": {"command": ["new"]}},
            },
            remove={
                "instructions": [".opencode/rules/old-ns/*.md"],
                "skills.paths": [".opencode/skills/old-ns"],
                "mcpServers": {"old-ns": {}},
            },
        )
        assert result["instructions"] == [
            "user-rule.md",
            ".opencode/rules/new-ns/*.md",
        ]
        assert result["skills"]["paths"] == [
            "user-skill",
            ".opencode/skills/new-ns",
        ]
        assert result["mcp"] == {
            "user-server": {"command": ["node"]},
            "vibe:new-ns": {"command": ["new"]},
        }

    def test_mcp_add_preserves_non_mcp_keys(self) -> None:
        """Adding MCP entries does not affect other top-level keys."""
        result = self._call(
            current={
                "instructions": ["rule.md"],
                "skills": {"paths": ["skill"]},
                "version": 2,
            },
            add={"mcpServers": {"svc": {"command": ["x"]}}},
        )
        assert result["instructions"] == ["rule.md"]
        assert result["skills"]["paths"] == ["skill"]
        assert result["version"] == 2
        assert result["mcp"]["vibe:svc"] == {"command": ["x"]}


# ============================================================================
# Integration: read → merge → write → read
# ============================================================================


class TestIntegration:
    """Integration tests for the full opencode.json lifecycle."""

    def test_full_lifecycle_read_merge_write_read(self, tmp_path: Path) -> None:
        """Given an existing opencode.json, merging and writing persists correctly."""
        from vibe_stack.writer.opencode_writer import (
            merge_vibe_entries,
            read_opencode,
            write_opencode,
        )

        path = tmp_path / "opencode.json"

        # Step 1: Create initial config
        initial = {
            "$schema": "https://opencode.ai/config.json",
            "instructions": ["~/.config/opencode/rules/*.md"],
            "skills": {"paths": ["skills"]},
            "mcp": {
                "user-server": {
                    "type": "local",
                    "command": ["node", "server.js"],
                }
            },
        }
        write_opencode(path, initial)

        # Step 2: Read it back
        current = read_opencode(path)
        assert current == initial

        # Step 3: Activate a domain (merge vibe entries)
        merged = merge_vibe_entries(
            current,
            add={
                "instructions": [".opencode/rules/dcc_blender/*.md"],
                "skills.paths": [".opencode/skills/dcc_blender"],
                "mcpServers": {
                    "blender-mcp": {
                        "type": "local",
                        "command": ["blender-mcp"],
                    }
                },
            },
        )

        # Step 4: Write merged back
        write_opencode(path, merged)

        # Step 5: Read again and verify
        final = read_opencode(path)

        # User entries preserved
        assert final["$schema"] == "https://opencode.ai/config.json"
        assert "~/.config/opencode/rules/*.md" in final["instructions"]
        assert "skills" in final["skills"]["paths"]
        assert final["mcp"]["user-server"]["command"] == ["node", "server.js"]

        # Vibe entries added
        assert ".opencode/rules/dcc_blender/*.md" in final["instructions"]
        assert ".opencode/skills/dcc_blender" in final["skills"]["paths"]
        assert final["mcp"]["vibe:blender-mcp"]["command"] == ["blender-mcp"]

        # Step 6: Deactivate (remove vibe entries)
        deactivated = merge_vibe_entries(
            final,
            remove={
                "instructions": [".opencode/rules/dcc_blender/*.md"],
                "skills.paths": [".opencode/skills/dcc_blender"],
                "mcpServers": {"blender-mcp": {}},
            },
        )
        write_opencode(path, deactivated)
        after_remove = read_opencode(path)

        # Vibe entries removed
        assert ".opencode/rules/dcc_blender/*.md" not in after_remove["instructions"]
        assert (
            ".opencode/skills/dcc_blender" not in after_remove["skills"]["paths"]
        )
        assert "vibe:blender-mcp" not in after_remove["mcp"]

        # User entries still preserved
        assert "~/.config/opencode/rules/*.md" in after_remove["instructions"]
        assert "skills" in after_remove["skills"]["paths"]
        assert after_remove["mcp"]["user-server"]["command"] == ["node", "server.js"]
