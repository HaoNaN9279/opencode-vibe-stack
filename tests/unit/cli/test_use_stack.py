"""Tests for cmd_use_stack CLI command (RED phase — TDD).

Tests three scenarios:
  1. Valid stack name → loads stack and activates each domain
  2. Empty stack name → lists available stacks
  3. Non-existent stack → prints error (catches StackNotFoundError)
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from vibe_stack.cli.commands.use_stack import cmd_use_stack


def _make_vibe_home(tmp_path: Path) -> Path:
    """Create a fake vibe-stack repo with stacks/ directory."""
    vh = tmp_path / "vibe-home"
    stacks_dir = vh / "stacks"
    stacks_dir.mkdir(parents=True)

    (stacks_dir / "game-dev.json").write_text(json.dumps({
        "name": "Game Development (Full)",
        "description": "All game dev domains",
        "domains": ["game-dev/unity", "game-dev/unreal"],
    }), encoding="utf-8")

    (stacks_dir / "dcc.json").write_text(json.dumps({
        "name": "DCC Tools (Full)",
        "description": "All DCC tools: Blender, Maya, Houdini",
        "domains": ["dcc/blender", "dcc/maya"],
    }), encoding="utf-8")

    return vh


def _make_project_root(tmp_path: Path) -> Path:
    """Create a fake project root with .opencode/ dir."""
    pr = tmp_path / "project"
    (pr / ".opencode").mkdir(parents=True, exist_ok=True)
    return pr


class TestCmdUseStack:
    """Tests for cmd_use_stack()."""

    # -- scenario 1: valid stack name activates all domains ---------------

    def test_valid_stack_name_activates_all_domains(
        self, tmp_path: Path,
    ) -> None:
        """Given a valid stack name,
        When cmd_use_stack is called,
        Then activate_domain is called for each domain in the stack."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        with patch("vibe_stack.cli.commands.use_stack.activate_domain") as mock_activate:
            cmd_use_stack(vh, pr, "game-dev")

        assert mock_activate.call_count == 2
        mock_activate.assert_any_call(vh, pr, "game-dev/unity")
        mock_activate.assert_any_call(vh, pr, "game-dev/unreal")

    def test_valid_stack_name_empty_domains(
        self, tmp_path: Path,
    ) -> None:
        """Given a stack with an empty domains list,
        When cmd_use_stack is called,
        Then activate_domain is not called."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        # Add a stack with empty domains
        stacks_dir = vh / "stacks"
        (stacks_dir / "empty.json").write_text(json.dumps({
            "name": "Empty Stack",
            "domains": [],
        }), encoding="utf-8")

        with patch("vibe_stack.cli.commands.use_stack.activate_domain") as mock_activate:
            cmd_use_stack(vh, pr, "empty")

        mock_activate.assert_not_called()

    # -- scenario 2: empty stack name lists available stacks -------------

    def test_empty_stack_name_lists_available_stacks(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given an empty stack name,
        When cmd_use_stack is called,
        Then available stacks and their descriptions are printed."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        cmd_use_stack(vh, pr, "")

        captured = capsys.readouterr()
        assert "game-dev" in captured.out
        assert "dcc" in captured.out
        assert "All game dev domains" in captured.out or "Game Development" in captured.out
        assert "All DCC tools" in captured.out or "DCC Tools" in captured.out

    def test_empty_stack_name_no_stacks_available(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given empty stack name and no stacks/ directory,
        When cmd_use_stack is called,
        Then a message indicating no stacks are available is printed."""
        vh = tmp_path / "vibe-home"  # no stacks/ dir
        pr = _make_project_root(tmp_path)

        cmd_use_stack(vh, pr, "")

        captured = capsys.readouterr()
        # Should indicate no stacks
        assert any(word in captured.out.lower() for word in
                   ["available", "no stacks", "not found", "none"])

    # -- scenario 3: non-existent stack prints error ---------------------

    def test_nonexistent_stack_prints_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given a non-existent stack name,
        When cmd_use_stack is called,
        Then an error message is printed and no exception is raised."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        # Should not raise — cmd_use_stack should catch StackNotFoundError
        cmd_use_stack(vh, pr, "nonexistent")

        captured = capsys.readouterr()
        assert "error" in captured.out.lower() or "not found" in captured.out.lower()
