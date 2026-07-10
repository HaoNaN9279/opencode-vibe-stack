"""Tests for the main CLI entry point — routing and argument parsing.

Tests verify that main() routes argv to the correct command functions
with the expected arguments. Command execution is NOT tested here — each
command has its own dedicated test file.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

# All test modules use the same mock path for vibe_home and project_root.
_MOCK_VIBE_HOME = Path("/fake/vibe-home")
# Resolve immediately so that Path.cwd().resolve() (which the CLI calls) is
# idempotent — on Windows /fake/project resolves to D:/fake/project.
_MOCK_PROJECT_ROOT = Path("/fake/project").resolve()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _patch_all_commands(monkeypatch: pytest.MonkeyPatch) -> dict[str, MagicMock]:
    """Replace every command function with a MagicMock.

    Returns a dict keyed by module-qualified name for assertion convenience.
    """
    mocks: dict[str, MagicMock] = {}
    targets: list[tuple[str, str]] = [
        ("vibe_stack.cli.commands.list_status", "cmd_list"),
        ("vibe_stack.cli.commands.list_status", "cmd_status"),
        ("vibe_stack.cli.commands.info", "cmd_info"),
        ("vibe_stack.cli.commands.activate", "cmd_activate"),
        ("vibe_stack.cli.commands.deactivate", "cmd_deactivate"),
        ("vibe_stack.cli.commands.use_stack", "cmd_use_stack"),
        ("vibe_stack.cli.commands.sync", "cmd_sync"),
    ]
    for module, func in targets:
        mock = MagicMock()
        monkeypatch.setattr(f"{module}.{func}", mock)
        mocks[func] = mock
    return mocks


def _setup_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure detect_vibe_home returns a fake path so tests don't walk the
    real filesystem. Also fix Path.cwd() for deterministic project_root."""
    monkeypatch.setattr(
        "vibe_stack.utils.path_util.detect_vibe_home",
        lambda: _MOCK_VIBE_HOME,
    )
    monkeypatch.setattr(
        "vibe_stack.cli.Path.cwd",
        lambda: _MOCK_PROJECT_ROOT,
    )


# ---------------------------------------------------------------------------
# Command routing tests
# ---------------------------------------------------------------------------


class TestCmdListRouting:
    """Tests for 'list' command routing."""

    def test_list_calls_cmd_list(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given argv=['list'], When main is called, Then cmd_list is invoked."""
        _setup_env(monkeypatch)
        mocks = _patch_all_commands(monkeypatch)

        from vibe_stack.cli import main

        main(["list"])

        mocks["cmd_list"].assert_called_once_with(
            _MOCK_VIBE_HOME, json_output=False,
        )
        mocks["cmd_status"].assert_not_called()

    def test_list_json_calls_cmd_list_with_json(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given argv=['list', '--json'], Then cmd_list gets json_output=True."""
        _setup_env(monkeypatch)
        mocks = _patch_all_commands(monkeypatch)

        from vibe_stack.cli import main

        main(["list", "--json"])

        mocks["cmd_list"].assert_called_once_with(
            _MOCK_VIBE_HOME, json_output=True,
        )


class TestCmdStatusRouting:
    """Tests for 'status' command routing."""

    def test_status_calls_cmd_status(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given argv=['status'], Then cmd_status is invoked."""
        _setup_env(monkeypatch)
        mocks = _patch_all_commands(monkeypatch)

        from vibe_stack.cli import main

        main(["status"])

        mocks["cmd_status"].assert_called_once_with(
            _MOCK_VIBE_HOME, _MOCK_PROJECT_ROOT, json_output=False,
        )


class TestCmdInfoRouting:
    """Tests for 'info' command routing."""

    def test_info_calls_cmd_info(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given argv=['info', 'dcc/blender'], Then cmd_info is called."""
        _setup_env(monkeypatch)
        mocks = _patch_all_commands(monkeypatch)

        from vibe_stack.cli import main

        main(["info", "dcc/blender"])

        mocks["cmd_info"].assert_called_once_with(
            _MOCK_VIBE_HOME, "dcc/blender", json_output=False,
        )

    def test_info_json_calls_cmd_info_with_json(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given argv=['info', 'dcc/blender', '--json'],
        Then cmd_info gets json_output=True."""
        _setup_env(monkeypatch)
        mocks = _patch_all_commands(monkeypatch)

        from vibe_stack.cli import main

        main(["info", "dcc/blender", "--json"])

        mocks["cmd_info"].assert_called_once_with(
            _MOCK_VIBE_HOME, "dcc/blender", json_output=True,
        )


class TestCmdActivateRouting:
    """Tests for 'activate' command routing."""

    def test_activate_single_calls_cmd_activate(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given argv=['activate', 'dcc/blender'],
        Then cmd_activate is called with one domain."""
        _setup_env(monkeypatch)
        mocks = _patch_all_commands(monkeypatch)

        from vibe_stack.cli import main

        main(["activate", "dcc/blender"])

        mocks["cmd_activate"].assert_called_once_with(
            _MOCK_VIBE_HOME, _MOCK_PROJECT_ROOT, ["dcc/blender"],
        )

    def test_activate_multiple_calls_cmd_activate_with_list(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given argv=['activate', 'dcc/blender', 'dcc/maya'],
        Then cmd_activate gets both domains."""
        _setup_env(monkeypatch)
        mocks = _patch_all_commands(monkeypatch)

        from vibe_stack.cli import main

        main(["activate", "dcc/blender", "dcc/maya"])

        mocks["cmd_activate"].assert_called_once_with(
            _MOCK_VIBE_HOME, _MOCK_PROJECT_ROOT, ["dcc/blender", "dcc/maya"],
        )


class TestCmdDeactivateRouting:
    """Tests for 'deactivate' command routing."""

    def test_deactivate_calls_cmd_deactivate(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given argv=['deactivate', 'dcc/blender'],
        Then cmd_deactivate is called."""
        _setup_env(monkeypatch)
        mocks = _patch_all_commands(monkeypatch)

        from vibe_stack.cli import main

        main(["deactivate", "dcc/blender"])

        mocks["cmd_deactivate"].assert_called_once_with(
            _MOCK_VIBE_HOME, _MOCK_PROJECT_ROOT, ["dcc/blender"],
        )


class TestCmdUseStackRouting:
    """Tests for 'use-stack' command routing."""

    def test_use_stack_with_name_calls_cmd_use_stack(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given argv=['use-stack', 'game-dev'],
        Then cmd_use_stack gets stack_name='game-dev'."""
        _setup_env(monkeypatch)
        mocks = _patch_all_commands(monkeypatch)

        from vibe_stack.cli import main

        main(["use-stack", "game-dev"])

        mocks["cmd_use_stack"].assert_called_once_with(
            _MOCK_VIBE_HOME, _MOCK_PROJECT_ROOT, "game-dev",
        )

    def test_use_stack_no_name_calls_cmd_use_stack_empty(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given argv=['use-stack'],
        Then cmd_use_stack gets empty string as stack_name."""
        _setup_env(monkeypatch)
        mocks = _patch_all_commands(monkeypatch)

        from vibe_stack.cli import main

        main(["use-stack"])

        mocks["cmd_use_stack"].assert_called_once_with(
            _MOCK_VIBE_HOME, _MOCK_PROJECT_ROOT, "",
        )


class TestCmdSyncRouting:
    """Tests for 'sync' command routing."""

    def test_sync_calls_cmd_sync(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given argv=['sync'], Then cmd_sync is called."""
        _setup_env(monkeypatch)
        mocks = _patch_all_commands(monkeypatch)

        from vibe_stack.cli import main

        main(["sync"])

        mocks["cmd_sync"].assert_called_once_with(
            _MOCK_VIBE_HOME, _MOCK_PROJECT_ROOT,
        )


# ---------------------------------------------------------------------------
# Meta / global flag tests
# ---------------------------------------------------------------------------


class TestVersion:
    """Tests for --version flag."""

    def test_version_prints_and_exits(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given argv=['--version'], When main is called,
        Then argparse prints version and exits with code 0."""
        _setup_env(monkeypatch)
        _patch_all_commands(monkeypatch)

        from vibe_stack.cli import main

        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])

        assert exc_info.value.code == 0


class TestHelp:
    """Tests for --help / -h flag."""

    def test_help_prints_and_exits(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given argv=['--help'], When main is called,
        Then argparse prints help and exits."""
        _setup_env(monkeypatch)
        _patch_all_commands(monkeypatch)

        from vibe_stack.cli import main

        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])

        assert exc_info.value.code == 0


class TestNoCommand:
    """Tests for invocations with no command."""

    def test_no_command_shows_usage(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given argv=[], When main is called,
        Then usage message is printed and no command runs."""
        _setup_env(monkeypatch)
        mocks = _patch_all_commands(monkeypatch)

        from vibe_stack.cli import main

        main([])

        captured = capsys.readouterr()
        assert "usage:" in captured.out

        # No command function should have been called.
        for mock in mocks.values():
            mock.assert_not_called()


class TestInvalidCommand:
    """Tests for unknown/invalid subcommands."""

    def test_invalid_command_shows_error(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given argv=['invalid-command'], When main is called,
        Then argparse raises SystemExit(2)."""
        _setup_env(monkeypatch)
        _patch_all_commands(monkeypatch)

        from vibe_stack.cli import main

        with pytest.raises(SystemExit) as exc_info:
            main(["invalid-command"])

        assert exc_info.value.code == 2


class TestVibeHomeFromEnv:
    """Tests for VIBE_STACK_HOME environment variable override."""

    def test_vibe_home_from_env_overrides_detect(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given VIBE_STACK_HOME is set and argv=['list'],
        When main is called,
        Then the env-provided path is used as vibe_home."""
        monkeypatch.setenv("VIBE_STACK_HOME", "/custom/vibe-home")
        # detect_vibe_home should NOT be called when env var is set.
        mock_detect = MagicMock(return_value=_MOCK_VIBE_HOME)
        monkeypatch.setattr(
            "vibe_stack.utils.path_util.detect_vibe_home", mock_detect,
        )
        monkeypatch.setattr(
            "vibe_stack.cli.Path.cwd", lambda: _MOCK_PROJECT_ROOT,
        )
        mocks = _patch_all_commands(monkeypatch)

        from vibe_stack.cli import main

        main(["list"])

        mock_detect.assert_not_called()
        # _resolve_vibe_home() calls Path(env_val).resolve(), so the
        # passed path is already resolved.
        mocks["cmd_list"].assert_called_once_with(
            Path("/custom/vibe-home").resolve(), json_output=False,
        )
