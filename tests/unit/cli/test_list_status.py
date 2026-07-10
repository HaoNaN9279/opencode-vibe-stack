"""Tests for cmd_list and cmd_status CLI commands (RED phase — TDD).

Tests:
  cmd_list: with domains, empty
  cmd_status: with active domains, empty
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from vibe_stack.model.domain import DomainMeta


class TestCmdList:
    """Tests for cmd_list()."""

    def test_list_with_domains_prints_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given discover_domains returns domains,
        When cmd_list is called,
        Then formatted domain list is printed."""
        from vibe_stack.cli.commands.list_status import cmd_list

        vh = tmp_path / "vibe-home"

        fake_domains: list[tuple[str, DomainMeta, Path]] = [
            ("ai/data-forge", DomainMeta(
                name="Data Forge", description="Data transformation MCP",
                version="1.0.0",
            ), Path("domains/ai/data-forge")),
            ("dcc/blender", DomainMeta(
                name="Blender", description="Blender 3D integration",
                version="1.0.0",
            ), Path("domains/dcc/blender")),
        ]

        with patch(
            "vibe_stack.cli.commands.list_status.discover_domains",
            return_value=fake_domains,
        ), patch(
            "vibe_stack.cli.commands.list_status.format_domain_list",
            return_value="LIST OUTPUT",
        ) as mock_fmt:
            cmd_list(vh)

        mock_fmt.assert_called_once()
        call_args = mock_fmt.call_args[0]
        # First positional arg should be list of (key, name, desc) tuples
        assert len(call_args[0]) == 2
        assert call_args[0][0] == ("ai/data-forge", "Data Forge", "Data transformation MCP")
        assert call_args[0][1] == ("dcc/blender", "Blender", "Blender 3D integration")
        # json_output defaults to False
        assert mock_fmt.call_args[1] == {"json_output": False}

        captured = capsys.readouterr()
        assert "LIST OUTPUT" in captured.out

    def test_list_empty_prints_empty_message(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given discover_domains returns empty list,
        When cmd_list is called,
        Then empty message is printed."""
        from vibe_stack.cli.commands.list_status import cmd_list

        vh = tmp_path / "vibe-home"

        with patch(
            "vibe_stack.cli.commands.list_status.discover_domains",
            return_value=[],
        ), patch(
            "vibe_stack.cli.commands.list_status.format_domain_list",
            return_value="No domains available.",
        ):
            cmd_list(vh)

        captured = capsys.readouterr()
        assert "No domains available." in captured.out


class TestCmdStatus:
    """Tests for cmd_status()."""

    def test_status_with_active_domains_prints_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given list_active_domains returns active domains,
        When cmd_status is called,
        Then formatted status is printed."""
        from vibe_stack.cli.commands.list_status import cmd_status

        vh = tmp_path / "vibe-home"
        pr = tmp_path / "project"

        with patch(
            "vibe_stack.cli.commands.list_status.list_active_domains",
            return_value=["dcc/blender", "game-dev/unity"],
        ), patch(
            "vibe_stack.cli.commands.list_status.format_status",
            return_value="STATUS OUTPUT",
        ) as mock_fmt:
            cmd_status(vh, pr)

        mock_fmt.assert_called_once_with(
            ["dcc/blender", "game-dev/unity"], json_output=False,
        )

        captured = capsys.readouterr()
        assert "STATUS OUTPUT" in captured.out

    def test_status_empty_prints_no_active_message(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given list_active_domains returns empty list,
        When cmd_status is called,
        Then no-active message is printed."""
        from vibe_stack.cli.commands.list_status import cmd_status

        vh = tmp_path / "vibe-home"
        pr = tmp_path / "project"

        with patch(
            "vibe_stack.cli.commands.list_status.list_active_domains",
            return_value=[],
        ), patch(
            "vibe_stack.cli.commands.list_status.format_status",
            return_value="No active domains.",
        ):
            cmd_status(vh, pr)

        captured = capsys.readouterr()
        assert "No active domains." in captured.out
