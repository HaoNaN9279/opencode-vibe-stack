"""Tests for stack data model dataclasses."""

from __future__ import annotations

from vibe_stack.model.stack import StackMeta


class TestStackMeta:
    """Tests for StackMeta dataclass."""

    def test_basic_construction(self) -> None:
        """StackMeta should hold name, description, and domains list."""
        stack = StackMeta(
            name="Game Development (Full)",
            description="All game dev domains",
            domains=["game-dev/unity", "game-dev/unreal"],
        )
        assert stack.name == "Game Development (Full)"
        assert stack.description == "All game dev domains"
        assert stack.domains == ["game-dev/unity", "game-dev/unreal"]

    def test_defaults(self) -> None:
        """StackMeta should default description to '' and domains to []."""
        stack = StackMeta(name="test-stack")
        assert stack.name == "test-stack"
        assert stack.description == ""
        assert stack.domains == []

    def test_is_dataclass(self) -> None:
        """StackMeta should be a stdlib dataclass."""
        from dataclasses import is_dataclass

        assert is_dataclass(StackMeta)

    def test_empty_domains_list(self) -> None:
        """StackMeta with empty domains list should be valid."""
        stack = StackMeta(name="Empty Stack", description="No domains")
        assert stack.domains == []

    def test_from_dict_matching_stack_json(self) -> None:
        """StackMeta should match the structure of stacks/*.json files."""
        # Simulating what would come from game-dev.json
        stack = StackMeta(**{
            "name": "Game Development (Full)",
            "description": "All game development domains: Unity, Unreal Engine",
            "domains": ["game-dev/unity", "game-dev/unreal"],
        })
        assert stack.name == "Game Development (Full)"
        assert len(stack.domains) == 2
        assert "game-dev/unity" in stack.domains

    def test_indie_game_stack(self) -> None:
        """StackMeta for indie-game stack should combine multiple domains."""
        stack = StackMeta(
            name="Indie Game Dev",
            description="Unity + Blender + Data Forge",
            domains=["game-dev/unity", "dcc/blender", "ai/data-forge"],
        )
        assert len(stack.domains) == 3
