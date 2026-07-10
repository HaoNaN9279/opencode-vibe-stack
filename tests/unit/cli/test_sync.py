"""Tests for cmd_sync CLI command (RED phase — TDD).

Tests:
  1. Sync runs without error — calls engine.sync, prints result
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


class TestCmdSync:
    """Tests for cmd_sync()."""

    def test_sync_runs_without_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given valid vibe_home and project_root,
        When cmd_sync is called,
        Then engine.sync is called and success message is printed."""
        from vibe_stack.cli.commands.sync import cmd_sync

        vh = tmp_path / "vibe-home"
        pr = tmp_path / "project"

        with patch(
            "vibe_stack.cli.commands.sync.sync",
        ) as mock_sync, patch(
            "vibe_stack.cli.commands.sync.format_sync_result",
            return_value="Sync complete: 3 created, 1 updated, 0 deleted",
        ) as mock_fmt:
            cmd_sync(vh, pr)

        mock_sync.assert_called_once_with(vh, pr)
        mock_fmt.assert_called_once_with(
            created=0, updated=0, deleted=0, json_output=False,
        )

        captured = capsys.readouterr()
        assert "Sync complete" in captured.out
