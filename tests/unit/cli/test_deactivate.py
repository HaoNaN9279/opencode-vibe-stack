"""Tests for cmd_deactivate CLI command (RED phase — TDD).

Tests:
  1. Single domain deactivate — calls deactivate_domain, prints success
  2. Not active warning — catches DomainNotActiveError, continues
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from vibe_stack.errors import DomainNotActiveError


class TestCmdDeactivate:
    """Tests for cmd_deactivate()."""

    def test_single_deactivate_calls_deactivate_and_prints(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given a single domain to deactivate,
        When cmd_deactivate is called,
        Then deactivate_domain is called and success message is printed."""
        from vibe_stack.cli.commands.deactivate import cmd_deactivate

        vh = tmp_path / "vibe-home"
        pr = tmp_path / "project"

        with patch(
            "vibe_stack.cli.commands.deactivate.deactivate_domain",
        ) as mock_deactivate:
            cmd_deactivate(vh, pr, ["dcc/blender"])

        mock_deactivate.assert_called_once_with(vh, pr, "dcc/blender")

        captured = capsys.readouterr()
        assert "Deactivated" in captured.out
        assert "dcc/blender" in captured.out

    def test_not_active_warning_continues(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given one domain raises DomainNotActiveError,
        When cmd_deactivate is called with multiple domains,
        Then warning is printed and remaining domains are processed."""
        from vibe_stack.cli.commands.deactivate import cmd_deactivate

        vh = tmp_path / "vibe-home"
        pr = tmp_path / "project"

        def fake_deactivate(_vh: object, _pr: object, domain_key: str) -> None:
            if domain_key == "inactive/domain":
                raise DomainNotActiveError(
                    f"domain '{domain_key}' is not active"
                )
            # others succeed silently

        with patch(
            "vibe_stack.cli.commands.deactivate.deactivate_domain",
            side_effect=fake_deactivate,
        ) as mock_deactivate:
            cmd_deactivate(vh, pr, ["inactive/domain", "dcc/blender"])

        assert mock_deactivate.call_count == 2

        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert "not active" in captured.out
        assert "Deactivated" in captured.out  # second one succeeded

    def test_multiple_deactivate_calls_for_each(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given multiple domains to deactivate,
        When cmd_deactivate is called,
        Then deactivate_domain is called for each."""
        from vibe_stack.cli.commands.deactivate import cmd_deactivate

        vh = tmp_path / "vibe-home"
        pr = tmp_path / "project"

        with patch(
            "vibe_stack.cli.commands.deactivate.deactivate_domain",
        ) as mock_deactivate:
            cmd_deactivate(vh, pr, ["dcc/blender", "game-dev/unity"])

        assert mock_deactivate.call_count == 2
        mock_deactivate.assert_any_call(vh, pr, "dcc/blender")
        mock_deactivate.assert_any_call(vh, pr, "game-dev/unity")
