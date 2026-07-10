"""Tests for cmd_activate CLI command (RED phase — TDD).

Tests:
  1. Single domain activate — calls activate_domain, prints success
  2. Multiple domains activate — calls for each, prints success for each
  3. Already active warning — catches DomainAlreadyActiveError, continues
  4. Not found warning — catches DomainNotFoundError, continues
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from vibe_stack.errors import DomainAlreadyActiveError, DomainNotFoundError


class TestCmdActivate:
    """Tests for cmd_activate()."""

    def test_single_activate_calls_activate_and_prints(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given a single domain to activate,
        When cmd_activate is called,
        Then activate_domain is called and success message is printed."""
        from vibe_stack.cli.commands.activate import cmd_activate

        vh = tmp_path / "vibe-home"
        pr = tmp_path / "project"

        with patch(
            "vibe_stack.cli.commands.activate.activate_domain",
        ) as mock_activate:
            cmd_activate(vh, pr, ["dcc/blender"])

        mock_activate.assert_called_once_with(vh, pr, "dcc/blender")

        captured = capsys.readouterr()
        assert "Activated" in captured.out
        assert "dcc/blender" in captured.out

    def test_multiple_activate_calls_for_each(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given multiple domains to activate,
        When cmd_activate is called,
        Then activate_domain is called for each domain."""
        from vibe_stack.cli.commands.activate import cmd_activate

        vh = tmp_path / "vibe-home"
        pr = tmp_path / "project"

        with patch(
            "vibe_stack.cli.commands.activate.activate_domain",
        ) as mock_activate:
            cmd_activate(vh, pr, ["dcc/blender", "game-dev/unity"])

        assert mock_activate.call_count == 2
        mock_activate.assert_any_call(vh, pr, "dcc/blender")
        mock_activate.assert_any_call(vh, pr, "game-dev/unity")

        captured = capsys.readouterr()
        assert captured.out.count("Activated") == 2

    def test_already_active_warning_continues(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given one domain raises DomainAlreadyActiveError,
        When cmd_activate is called with multiple domains,
        Then warning is printed and remaining domains are processed."""
        from vibe_stack.cli.commands.activate import cmd_activate

        vh = tmp_path / "vibe-home"
        pr = tmp_path / "project"

        def fake_activate(_vh: object, _pr: object, domain_key: str) -> None:
            if domain_key == "dcc/blender":
                raise DomainAlreadyActiveError(
                    f"domain '{domain_key}' is already active"
                )
            # others succeed silently

        with patch(
            "vibe_stack.cli.commands.activate.activate_domain",
            side_effect=fake_activate,
        ) as mock_activate:
            cmd_activate(vh, pr, ["dcc/blender", "game-dev/unity"])

        assert mock_activate.call_count == 2

        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert "already active" in captured.out
        assert "Activated" in captured.out  # second one succeeded

    def test_not_found_warning_continues(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given one domain raises DomainNotFoundError,
        When cmd_activate is called with multiple domains,
        Then warning is printed and remaining domains are processed."""
        from vibe_stack.cli.commands.activate import cmd_activate

        vh = tmp_path / "vibe-home"
        pr = tmp_path / "project"

        def fake_activate(_vh: object, _pr: object, domain_key: str) -> None:
            if domain_key == "missing/domain":
                raise DomainNotFoundError(
                    f"domain '{domain_key}' not found"
                )
            # others succeed silently

        with patch(
            "vibe_stack.cli.commands.activate.activate_domain",
            side_effect=fake_activate,
        ) as mock_activate:
            cmd_activate(vh, pr, ["missing/domain", "dcc/blender"])

        assert mock_activate.call_count == 2

        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert "not found" in captured.out
        assert "Activated" in captured.out  # second one succeeded
