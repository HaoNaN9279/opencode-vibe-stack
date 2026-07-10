"""Tests for cmd_info CLI command (RED phase — TDD).

Tests three scenarios:
  1. Valid domain — prints formatted info
  2. Missing domain — raises SystemExit(1)
  3. JSON output — calls formatter with json_output=True
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from vibe_stack.errors import DomainNotFoundError
from vibe_stack.model.domain import DomainConfig, DomainMeta


class TestCmdInfo:
    """Tests for cmd_info()."""

    def test_valid_domain_prints_info(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given a valid domain key,
        When cmd_info is called,
        Then load_domain is called and formatted output is printed."""
        from vibe_stack.cli.commands.info import cmd_info

        vh = tmp_path / "vibe-home"

        fake_config = DomainConfig(
            meta=DomainMeta(
                name="blender",
                description="Blender 3D integration",
                version="1.0.0",
                tags=["dcc", "3d"],
            ),
            domain_key="dcc/blender",
            namespace="dcc_blender",
            domain_root=vh / "domains" / "dcc" / "blender",
        )

        with patch(
            "vibe_stack.cli.commands.info.load_domain", return_value=fake_config
        ) as mock_load, patch(
            "vibe_stack.cli.commands.info.format_domain_info",
            return_value="FAKE FORMATTED OUTPUT",
        ) as mock_fmt:
            cmd_info(vh, "dcc/blender")

        mock_load.assert_called_once_with(vh, "dcc/blender")
        mock_fmt.assert_called_once_with(
            fake_config.meta, fake_config.domain_key, fake_config.namespace,
            json_output=False,
        )
        captured = capsys.readouterr()
        assert "FAKE FORMATTED OUTPUT" in captured.out

    def test_missing_domain_raises_system_exit(
        self, tmp_path: Path,
    ) -> None:
        """Given a domain key that does not exist,
        When cmd_info is called,
        Then SystemExit(1) is raised."""
        from vibe_stack.cli.commands.info import cmd_info

        vh = tmp_path / "vibe-home"

        with patch(
            "vibe_stack.cli.commands.info.load_domain",
            side_effect=DomainNotFoundError("domain 'missing' not found"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                cmd_info(vh, "missing")

        assert exc_info.value.code == 1

    def test_json_output_calls_formatter_with_json_true(
        self, tmp_path: Path,
    ) -> None:
        """Given json_output=True,
        When cmd_info is called,
        Then formatter is called with json_output=True."""
        from vibe_stack.cli.commands.info import cmd_info

        vh = tmp_path / "vibe-home"

        fake_config = DomainConfig(
            meta=DomainMeta(
                name="blender",
                description="Blender 3D integration",
                version="1.0.0",
            ),
            domain_key="dcc/blender",
            namespace="dcc_blender",
            domain_root=vh / "domains" / "dcc" / "blender",
        )

        with patch(
            "vibe_stack.cli.commands.info.load_domain", return_value=fake_config
        ), patch(
            "vibe_stack.cli.commands.info.format_domain_info",
            return_value='{"key": "dcc/blender"}',
        ) as mock_fmt:
            cmd_info(vh, "dcc/blender", json_output=True)

        mock_fmt.assert_called_once_with(
            fake_config.meta, fake_config.domain_key, fake_config.namespace,
            json_output=True,
        )
