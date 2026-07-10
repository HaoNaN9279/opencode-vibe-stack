"""Tests for MCP path resolver (RED phase — TDD).

Tests the ``resolve_mcp_config()`` function which reads an MCP JSON config
file, resolves ``${...}`` placeholders in command elements against environment
variables and a fallback paths config, and returns prefixed entries.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


# ============================================================================
# Helpers
# ============================================================================


def _write_mcp_json(path: Path, content: dict) -> None:
    """Write a dict as JSON to the given path, creating parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, indent=2), encoding="utf-8")


def _write_paths_config(path: Path, content: dict) -> None:
    """Write a paths config as JSON to the given path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, indent=2), encoding="utf-8")


# ============================================================================
# resolve_mcp_config
# ============================================================================


class TestResolveMcpConfig:
    """Tests for resolve_mcp_config()."""

    @staticmethod
    def _call(mcp_json_path: Path, namespace: str, project_root: Path) -> dict:
        from vibe_stack.sync.mcp_resolver import resolve_mcp_config

        return resolve_mcp_config(mcp_json_path, namespace, project_root)

    # ------------------------------------------------------------------
    # env var resolution
    # ------------------------------------------------------------------

    def test_resolves_specific_env_var(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Resolve ``${MCP_PATH_MY_SERVER}`` from env var ``MCP_PATH_MY_SERVER``."""
        monkeypatch.setenv("MCP_PATH_MY_SERVER", "/usr/bin/my-server")
        mcp_json = tmp_path / "mcp.json"
        _write_mcp_json(mcp_json, {
            "mcpServers": {
                "my-server": {
                    "type": "local",
                    "command": ["${MCP_PATH_MY_SERVER}", "--port=8080"],
                    "enabled": True,
                }
            }
        })

        result = self._call(mcp_json, "dcc_blender", tmp_path)

        key = "vibe:dcc_blender_my-server"
        assert key in result
        assert result[key]["command"] == ["/usr/bin/my-server", "--port=8080"]

    def test_resolves_general_mcp_path_fallback(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Resolve ``${MCP_PATH}`` from env var ``MCP_PATH`` when specific var is unset."""
        # No specific env var
        monkeypatch.setenv("MCP_PATH", "/opt/tools/server")
        mcp_json = tmp_path / "mcp.json"
        _write_mcp_json(mcp_json, {
            "mcpServers": {
                "my-server": {
                    "type": "local",
                    "command": ["${MCP_PATH_MY_SERVER}", "start"],
                    "enabled": True,
                }
            }
        })

        result = self._call(mcp_json, "ns", tmp_path)

        assert result["vibe:ns_my-server"]["command"] == ["/opt/tools/server", "start"]

    def test_resolves_placeholder_named_mcp_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Resolve ``${MCP_PATH}`` placeholder directly from ``MCP_PATH`` env var."""
        monkeypatch.setenv("MCP_PATH", "/usr/local/bin/tool")
        mcp_json = tmp_path / "mcp.json"
        _write_mcp_json(mcp_json, {
            "mcpServers": {
                "my-server": {
                    "type": "local",
                    "command": ["${MCP_PATH}", "serve"],
                    "enabled": True,
                }
            }
        })

        result = self._call(mcp_json, "ns", tmp_path)

        assert result["vibe:ns_my-server"]["command"] == ["/usr/local/bin/tool", "serve"]

    def test_specific_env_var_priority_over_general(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Specific ``MCP_PATH_X`` env var takes priority over ``MCP_PATH``."""
        monkeypatch.setenv("MCP_PATH_MY_SERVER", "/specific/path")
        monkeypatch.setenv("MCP_PATH", "/general/path")
        mcp_json = tmp_path / "mcp.json"
        _write_mcp_json(mcp_json, {
            "mcpServers": {
                "my-server": {
                    "type": "local",
                    "command": ["${MCP_PATH_MY_SERVER}", "run"],
                    "enabled": True,
                }
            }
        })

        result = self._call(mcp_json, "ns", tmp_path)

        assert result["vibe:ns_my-server"]["command"] == ["/specific/path", "run"]

    # ------------------------------------------------------------------
    # paths config fallback
    # ------------------------------------------------------------------

    def test_falls_back_to_paths_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Fall back to ~/.config/opencode/vibe-mcp-paths.json when env not set."""
        # unset all relevant env vars
        monkeypatch.delenv("MCP_PATH_MY_SERVER", raising=False)
        monkeypatch.delenv("MCP_PATH", raising=False)

        home = tmp_path / "mock_home"
        monkeypatch.setattr(Path, "home", lambda: home)
        paths_config = home / ".config" / "opencode" / "vibe-mcp-paths.json"
        _write_paths_config(paths_config, {"my-server": "/from/config/tool"})

        mcp_json = tmp_path / "mcp.json"
        _write_mcp_json(mcp_json, {
            "mcpServers": {
                "my-server": {
                    "type": "local",
                    "command": ["${MCP_PATH_MY_SERVER}", "run"],
                    "enabled": True,
                }
            }
        })

        result = self._call(mcp_json, "ns", tmp_path)

        # env vars not set → should use paths config
        assert result["vibe:ns_my-server"]["command"] == ["/from/config/tool", "run"]

    def test_env_priority_over_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Environment variable takes priority over vibe-mcp-paths.json."""
        monkeypatch.setenv("MCP_PATH_MY_SERVER", "/env/path")

        home = tmp_path / "mock_home"
        monkeypatch.setattr(Path, "home", lambda: home)
        paths_config = home / ".config" / "opencode" / "vibe-mcp-paths.json"
        _write_paths_config(paths_config, {"my-server": "/config/path"})

        mcp_json = tmp_path / "mcp.json"
        _write_mcp_json(mcp_json, {
            "mcpServers": {
                "my-server": {
                    "type": "local",
                    "command": ["${MCP_PATH_MY_SERVER}", "run"],
                    "enabled": True,
                }
            }
        })

        result = self._call(mcp_json, "ns", tmp_path)

        # env should win over config
        assert result["vibe:ns_my-server"]["command"] == ["/env/path", "run"]

    # ------------------------------------------------------------------
    # fallback to as-is (rely on PATH)
    # ------------------------------------------------------------------

    def test_falls_back_to_as_is_when_nothing_resolves(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Leave placeholder as-is when no env var, no config, relying on PATH."""
        monkeypatch.delenv("MCP_PATH_MY_SERVER", raising=False)
        monkeypatch.delenv("MCP_PATH", raising=False)
        # no paths config at all — mock home to isolate from real config
        home = tmp_path / "mock_home"
        monkeypatch.setattr(Path, "home", lambda: home)

        mcp_json = tmp_path / "mcp.json"
        _write_mcp_json(mcp_json, {
            "mcpServers": {
                "my-server": {
                    "type": "local",
                    "command": ["${MCP_PATH_MY_SERVER}", "--port=8080"],
                    "enabled": True,
                }
            }
        })

        result = self._call(mcp_json, "ns", tmp_path)

        # placeholder stays because binary might be on PATH
        assert result["vibe:ns_my-server"]["command"] == [
            "${MCP_PATH_MY_SERVER}",
            "--port=8080",
        ]

    def test_unknown_placeholder_stays(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``${UNKNOWN_VAR}`` stays as-is since no resolution matches."""
        monkeypatch.delenv("UNKNOWN_VAR", raising=False)
        mcp_json = tmp_path / "mcp.json"
        _write_mcp_json(mcp_json, {
            "mcpServers": {
                "my-server": {
                    "type": "local",
                    "command": ["${UNKNOWN_VAR}", "arg"],
                    "enabled": True,
                }
            }
        })

        result = self._call(mcp_json, "ns", tmp_path)

        assert result["vibe:ns_my-server"]["command"] == ["${UNKNOWN_VAR}", "arg"]

    # ------------------------------------------------------------------
    # key prefixing
    # ------------------------------------------------------------------

    def test_keys_prefixed_with_vibe_namespace(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returned dict has keys prefixed ``vibe:{namespace}_``."""
        monkeypatch.setenv("MCP_PATH_MY_SERVER", "/bin/my-server")
        mcp_json = tmp_path / "mcp.json"
        _write_mcp_json(mcp_json, {
            "mcpServers": {
                "my-server": {
                    "type": "local",
                    "command": ["${MCP_PATH_MY_SERVER}"],
                    "enabled": True,
                }
            }
        })

        result = self._call(mcp_json, "dcc_blender", tmp_path)

        assert "vibe:dcc_blender_my-server" in result
        assert "my-server" not in result  # not the raw key

    def test_multiple_servers_all_prefixed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Multiple servers all get proper namespace prefixing."""
        monkeypatch.setenv("MCP_PATH_FOO", "/bin/foo")
        monkeypatch.setenv("MCP_PATH_BAR", "/bin/bar")
        mcp_json = tmp_path / "mcp.json"
        _write_mcp_json(mcp_json, {
            "mcpServers": {
                "foo": {
                    "type": "local",
                    "command": ["${MCP_PATH_FOO}"],
                    "enabled": True,
                },
                "bar": {
                    "type": "local",
                    "command": ["${MCP_PATH_BAR}"],
                    "enabled": False,
                },
            }
        })

        result = self._call(mcp_json, "dcc_blender", tmp_path)

        assert set(result.keys()) == {
            "vibe:dcc_blender_foo",
            "vibe:dcc_blender_bar",
        }
        assert result["vibe:dcc_blender_foo"]["command"] == ["/bin/foo"]
        assert result["vibe:dcc_blender_bar"]["command"] == ["/bin/bar"]
        assert result["vibe:dcc_blender_bar"]["enabled"] is False

    # ------------------------------------------------------------------
    # Windows paths
    # ------------------------------------------------------------------

    def test_handles_windows_path_in_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Handle Windows-style paths in environment variables."""
        monkeypatch.setenv("MCP_PATH_MY_SERVER", r"C:\tools\my-server.exe")
        mcp_json = tmp_path / "mcp.json"
        _write_mcp_json(mcp_json, {
            "mcpServers": {
                "my-server": {
                    "type": "local",
                    "command": ["${MCP_PATH_MY_SERVER}", "--port=8080"],
                    "enabled": True,
                }
            }
        })

        result = self._call(mcp_json, "ns", tmp_path)

        assert result["vibe:ns_my-server"]["command"] == [
            r"C:\tools\my-server.exe",
            "--port=8080",
        ]

    def test_handles_windows_path_in_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Handle Windows-style paths in vibe-mcp-paths.json."""
        monkeypatch.delenv("MCP_PATH_MY_SERVER", raising=False)
        monkeypatch.delenv("MCP_PATH", raising=False)

        home = tmp_path / "mock_home"
        monkeypatch.setattr(Path, "home", lambda: home)
        paths_config = home / ".config" / "opencode" / "vibe-mcp-paths.json"
        _write_paths_config(paths_config, {"my-server": r"D:\apps\server.exe"})

        mcp_json = tmp_path / "mcp.json"
        _write_mcp_json(mcp_json, {
            "mcpServers": {
                "my-server": {
                    "type": "local",
                    "command": ["${MCP_PATH_MY_SERVER}"],
                    "enabled": True,
                }
            }
        })

        result = self._call(mcp_json, "ns", tmp_path)

        assert result["vibe:ns_my-server"]["command"] == [r"D:\apps\server.exe"]

    # ------------------------------------------------------------------
    # JSONC support
    # ------------------------------------------------------------------

    def test_handles_jsonc_with_comments(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Handle JSONC input files with comments."""
        monkeypatch.setenv("MCP_PATH_MY_SERVER", "/bin/my-server")
        jsonc_path = tmp_path / "mcp.jsonc"
        jsonc_path.parent.mkdir(parents=True, exist_ok=True)
        jsonc_path.write_text(
            """\
{
    // This is a comment
    "mcpServers": {
        "my-server": {
            "type": "local",
            /* inline comment */
            "command": ["${MCP_PATH_MY_SERVER}", "--port=8080"],
            "enabled": true
        }
    }
}
""",
            encoding="utf-8",
        )

        result = self._call(jsonc_path, "ns", tmp_path)

        assert result["vibe:ns_my-server"]["command"] == ["/bin/my-server", "--port=8080"]

    # ------------------------------------------------------------------
    # missing paths config
    # ------------------------------------------------------------------

    def test_handles_missing_paths_config_gracefully(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Gracefully handle missing vibe-mcp-paths.json."""
        monkeypatch.delenv("MCP_PATH_MY_SERVER", raising=False)
        monkeypatch.delenv("MCP_PATH", raising=False)
        # Isolate from real home config
        home = tmp_path / "mock_home"
        monkeypatch.setattr(Path, "home", lambda: home)
        # NOTE: we do NOT create vibe-mcp-paths.json

        mcp_json = tmp_path / "mcp.json"
        _write_mcp_json(mcp_json, {
            "mcpServers": {
                "my-server": {
                    "type": "local",
                    "command": ["${MCP_PATH_MY_SERVER}"],
                    "enabled": True,
                }
            }
        })

        result = self._call(mcp_json, "ns", tmp_path)

        # Should not crash — fall through to as-is
        assert result["vibe:ns_my-server"]["command"] == ["${MCP_PATH_MY_SERVER}"]

    # ------------------------------------------------------------------
    # legacy "mcp" key
    # ------------------------------------------------------------------

    def test_supports_legacy_mcp_key(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Support legacy ``"mcp"`` key (not ``"mcpServers"``)."""
        monkeypatch.setenv("MCP_PATH_MY_SERVER", "/bin/tool")
        mcp_json = tmp_path / "mcp.json"
        _write_mcp_json(mcp_json, {
            "mcp": {
                "my-server": {
                    "type": "local",
                    "command": ["${MCP_PATH_MY_SERVER}"],
                    "enabled": True,
                }
            }
        })

        result = self._call(mcp_json, "ns", tmp_path)

        assert result["vibe:ns_my-server"]["command"] == ["/bin/tool"]

    def test_mcp_servers_key_takes_priority_over_mcp(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When both ``mcpServers`` and ``mcp`` are present, prefer ``mcpServers``."""
        monkeypatch.setenv("MCP_PATH_A", "/bin/a")
        monkeypatch.setenv("MCP_PATH_B", "/bin/b")
        mcp_json = tmp_path / "mcp.json"
        _write_mcp_json(mcp_json, {
            "mcpServers": {
                "server-a": {
                    "type": "local",
                    "command": ["${MCP_PATH_A}"],
                    "enabled": True,
                }
            },
            "mcp": {
                "server-b": {
                    "type": "local",
                    "command": ["${MCP_PATH_B}"],
                    "enabled": False,
                }
            },
        })

        result = self._call(mcp_json, "ns", tmp_path)

        # Only mcpServers should be resolved; "mcp" is ignored when "mcpServers" exists
        assert "vibe:ns_server-a" in result
        assert "vibe:ns_server-b" not in result

    # ------------------------------------------------------------------
    # edge cases
    # ------------------------------------------------------------------

    def test_empty_servers_returns_empty_dict(
        self, tmp_path: Path
    ) -> None:
        """Empty mcpServers returns empty dict."""
        mcp_json = tmp_path / "mcp.json"
        _write_mcp_json(mcp_json, {"mcpServers": {}})

        result = self._call(mcp_json, "ns", tmp_path)

        assert result == {}

    def test_no_mcp_servers_key_returns_empty_dict(
        self, tmp_path: Path
    ) -> None:
        """Config with neither mcpServers nor mcp key returns empty dict."""
        mcp_json = tmp_path / "mcp.json"
        _write_mcp_json(mcp_json, {"other": "stuff"})

        result = self._call(mcp_json, "ns", tmp_path)

        assert result == {}

    def test_missing_config_file_returns_empty_dict(
        self, tmp_path: Path
    ) -> None:
        """Missing MCP config file returns empty dict gracefully."""
        nonexistent = tmp_path / "does_not_exist.json"

        result = self._call(nonexistent, "ns", tmp_path)

        assert result == {}

    def test_server_without_command_preserved_as_is(
        self, tmp_path: Path
    ) -> None:
        """Server entry without a command field is preserved unchanged."""
        mcp_json = tmp_path / "mcp.json"
        _write_mcp_json(mcp_json, {
            "mcpServers": {
                "my-server": {
                    "type": "remote",
                    "url": "https://example.com",
                    "enabled": True,
                }
            }
        })

        result = self._call(mcp_json, "ns", tmp_path)

        assert result["vibe:ns_my-server"]["type"] == "remote"
        assert result["vibe:ns_my-server"]["url"] == "https://example.com"

    def test_command_with_multiple_placeholders(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Resolve multiple placeholders in a single command element."""
        monkeypatch.setenv("MCP_PATH_MY_SERVER", "/bin/server")
        monkeypatch.setenv("MCP_PATH_CONFIG", "/etc/config")
        mcp_json = tmp_path / "mcp.json"
        _write_mcp_json(mcp_json, {
            "mcpServers": {
                "my-server": {
                    "type": "local",
                    "command": [
                        "${MCP_PATH_MY_SERVER}",
                        "--config=${MCP_PATH_CONFIG}",
                    ],
                    "enabled": True,
                }
            }
        })

        result = self._call(mcp_json, "ns", tmp_path)

        assert result["vibe:ns_my-server"]["command"] == [
            "/bin/server",
            "--config=/etc/config",
        ]

    def test_does_not_modify_original_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returned dict is a new object; does not mutate input config on disk."""
        monkeypatch.setenv("MCP_PATH_MY_SERVER", "/bin/server")
        mcp_json = tmp_path / "mcp.json"
        original = {
            "mcpServers": {
                "my-server": {
                    "type": "local",
                    "command": ["${MCP_PATH_MY_SERVER}"],
                    "enabled": True,
                }
            }
        }
        _write_mcp_json(mcp_json, original)

        result = self._call(mcp_json, "ns", tmp_path)

        # Original file content unchanged
        assert json.loads(mcp_json.read_text()) == original
        # Result has resolved values
        assert result["vibe:ns_my-server"]["command"] == ["/bin/server"]
