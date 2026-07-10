"""Tests for stack loader: discover_stacks() and load_stack()."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vibe_stack.errors import StackNotFoundError, VibeStackError
from vibe_stack.loader.stack_loader import discover_stacks, load_stack


class TestDiscoverStacks:
    """Tests for discover_stacks()."""

    def test_finds_all_json_files(self, tmp_path: Path) -> None:
        """discover_stacks should find all .json files in stacks/ directory."""
        stacks_dir = tmp_path / "stacks"
        stacks_dir.mkdir()
        (stacks_dir / "game-dev.json").write_text(
            json.dumps({"name": "Game Dev", "domains": ["game-dev/unity"]})
        )
        (stacks_dir / "dcc.json").write_text(
            json.dumps({"name": "DCC", "domains": ["dcc/blender"]})
        )
        result = discover_stacks(tmp_path)
        names = {name for name, _ in result}
        assert names == {"game-dev", "dcc"}

    def test_returns_name_and_dict_tuples(self, tmp_path: Path) -> None:
        """Each result should be a (name, dict) tuple with parsed JSON."""
        stacks_dir = tmp_path / "stacks"
        stacks_dir.mkdir()
        (stacks_dir / "game-dev.json").write_text(
            json.dumps({"name": "Game Dev", "domains": ["game-dev/unity"]})
        )
        result = discover_stacks(tmp_path)
        assert len(result) == 1
        name, data = result[0]
        assert name == "game-dev"
        assert isinstance(data, dict)
        assert data["name"] == "Game Dev"
        assert data["domains"] == ["game-dev/unity"]

    def test_empty_when_missing_stacks_dir(self, tmp_path: Path) -> None:
        """discover_stacks should return [] when stacks/ doesn't exist."""
        assert discover_stacks(tmp_path) == []

    def test_empty_when_stacks_dir_empty(self, tmp_path: Path) -> None:
        """discover_stacks should return [] when stacks/ is empty."""
        stacks_dir = tmp_path / "stacks"
        stacks_dir.mkdir()
        assert discover_stacks(tmp_path) == []

    def test_ignores_non_json_files(self, tmp_path: Path) -> None:
        """discover_stacks should only pick up .json files, not other files."""
        stacks_dir = tmp_path / "stacks"
        stacks_dir.mkdir()
        (stacks_dir / "game-dev.json").write_text(
            json.dumps({"name": "Game Dev", "domains": []})
        )
        (stacks_dir / "readme.md").write_text("# ignore")
        (stacks_dir / "notes.txt").write_text("ignore")
        result = discover_stacks(tmp_path)
        assert len(result) == 1
        assert result[0][0] == "game-dev"


class TestLoadStack:
    """Tests for load_stack()."""

    def test_returns_domain_list(self, tmp_path: Path) -> None:
        """load_stack should return a list of domain keys from the stack."""
        stacks_dir = tmp_path / "stacks"
        stacks_dir.mkdir()
        (stacks_dir / "game-dev.json").write_text(
            json.dumps({
                "name": "Game Development (Full)",
                "description": "All game dev domains",
                "domains": ["game-dev/unity", "game-dev/unreal"],
            })
        )
        result = load_stack(tmp_path, "game-dev")
        assert result == ["game-dev/unity", "game-dev/unreal"]

    def test_raises_stack_not_found(self, tmp_path: Path) -> None:
        """load_stack should raise StackNotFoundError for missing stack."""
        stacks_dir = tmp_path / "stacks"
        stacks_dir.mkdir()
        with pytest.raises(StackNotFoundError):
            load_stack(tmp_path, "nonexistent")

    def test_handles_empty_domains(self, tmp_path: Path) -> None:
        """load_stack should handle a stack with an empty domains list."""
        stacks_dir = tmp_path / "stacks"
        stacks_dir.mkdir()
        (stacks_dir / "empty.json").write_text(
            json.dumps({"name": "Empty Stack", "domains": []})
        )
        result = load_stack(tmp_path, "empty")
        assert result == []

    def test_raises_vibe_stack_error_for_invalid_json(self, tmp_path: Path) -> None:
        """load_stack should raise VibeStackError for invalid JSON content."""
        stacks_dir = tmp_path / "stacks"
        stacks_dir.mkdir()
        (stacks_dir / "bad.json").write_text("{invalid json}")
        with pytest.raises(VibeStackError):
            load_stack(tmp_path, "bad")

    def test_stack_name_strips_json_suffix(self, tmp_path: Path) -> None:
        """The stack name should be derived from the filename without .json."""
        stacks_dir = tmp_path / "stacks"
        stacks_dir.mkdir()
        (stacks_dir / "my-stack.json").write_text(
            json.dumps({"name": "My Stack", "domains": ["cat/name"]})
        )
        result = load_stack(tmp_path, "my-stack")
        assert result == ["cat/name"]
