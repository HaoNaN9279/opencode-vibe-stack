"""Tests for path utility functions."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from vibe_stack.utils.path_util import (
    compute_relative_target,
    detect_vibe_home,
    ensure_dir,
    key_from_namespace,
    namespace_from_key,
)


# ---------------------------------------------------------------------------
# namespace_from_key
# ---------------------------------------------------------------------------


class TestNamespaceFromKey:
    """Tests for namespace_from_key."""

    def test_two_level_key(self) -> None:
        result = namespace_from_key("dcc/blender")
        assert result == "dcc_blender"

    def test_nested_three_levels(self) -> None:
        result = namespace_from_key("dcc/sub/deep")
        assert result == "dcc_sub_deep"

    def test_key_with_hyphen(self) -> None:
        result = namespace_from_key("ai/data-forge")
        assert result == "ai_data-forge"

    def test_simple_no_slash(self) -> None:
        result = namespace_from_key("simple")
        assert result == "simple"

    def test_key_with_multiple_slashes(self) -> None:
        result = namespace_from_key("a/b/c/d")
        assert result == "a_b_c_d"


# ---------------------------------------------------------------------------
# key_from_namespace
# ---------------------------------------------------------------------------


class TestKeyFromNamespace:
    """Tests for key_from_namespace."""

    def test_two_level_namespace(self) -> None:
        result = key_from_namespace("dcc_blender")
        assert result == "dcc/blender"

    def test_nested_three_levels(self) -> None:
        result = key_from_namespace("dcc_sub_deep")
        assert result == "dcc/sub/deep"

    def test_namespace_with_hyphen(self) -> None:
        result = key_from_namespace("ai_data-forge")
        assert result == "ai/data-forge"

    def test_single_level(self) -> None:
        result = key_from_namespace("simple")
        assert result == "simple"

    def test_many_underscores(self) -> None:
        result = key_from_namespace("a_b_c_d")
        assert result == "a/b/c/d"


# ---------------------------------------------------------------------------
# Round-trip identity
# ---------------------------------------------------------------------------


class TestRoundTrip:
    """Round-trip: key → namespace → key is identity."""

    @pytest.mark.parametrize(
        "domain_key",
        [
            "dcc/blender",
            "dcc/maya",
            "ai/data-forge",
            "game-dev/unity",
            "dcc/sub/deep",
            "simple",
        ],
    )
    def test_key_namespace_key_identity(self, domain_key: str) -> None:
        namespace = namespace_from_key(domain_key)
        result = key_from_namespace(namespace)
        assert result == domain_key


# ---------------------------------------------------------------------------
# ensure_dir
# ---------------------------------------------------------------------------


class TestEnsureDir:
    """Tests for ensure_dir."""

    def test_creates_nonexistent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            new_dir = Path(tmp) / "new" / "subdir"
            assert not new_dir.exists()
            ensure_dir(new_dir)
            assert new_dir.exists()
            assert new_dir.is_dir()

    def test_noop_on_existing_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            existing = Path(tmp) / "exists"
            existing.mkdir()
            mtime_before = existing.stat().st_mtime
            ensure_dir(existing)
            assert existing.exists()
            assert existing.stat().st_mtime == pytest.approx(mtime_before)

    def test_creates_deeply_nested_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            deep = Path(tmp) / "a" / "b" / "c" / "d"
            assert not deep.exists()
            ensure_dir(deep)
            assert deep.exists()
            assert deep.is_dir()


# ---------------------------------------------------------------------------
# detect_vibe_home
# ---------------------------------------------------------------------------


class TestDetectVibeHome:
    """Tests for detect_vibe_home."""

    def test_finds_project_root(self) -> None:
        """detect_vibe_home() should find the project root from within the project."""
        result = detect_vibe_home()
        assert result.exists()
        assert (result / "core" / "rules" / "00-global.md").exists()
        assert (result / "domains").exists()

    def test_finds_from_subdir(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """detect_vibe_home() should find root when cwd is a subdirectory."""
        project_root = detect_vibe_home()
        monkeypatch.chdir(str(project_root / "src" / "vibe_stack"))
        result = detect_vibe_home()
        assert result == project_root

    def test_raises_when_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """detect_vibe_home() should raise when walking up yields no match."""
        with tempfile.TemporaryDirectory() as tmp:
            monkeypatch.chdir(tmp)
            try:
                with pytest.raises(RuntimeError, match="vibe stack home not found"):
                    detect_vibe_home()
            finally:
                # Restore CWD before tmp dir is cleaned up, otherwise
                # Windows cannot delete the directory currently in use
                # as the process working directory.
                monkeypatch.undo()


# ---------------------------------------------------------------------------
# compute_relative_target
# ---------------------------------------------------------------------------


class TestComputeRelativeTarget:
    """Tests for compute_relative_target."""

    def test_rule_file_in_namespace(self) -> None:
        source = Path("/some/repo/domains/dcc/blender/rules/blender.md")
        dot_opencode = Path("/some/project/.opencode")
        namespace = "dcc_blender"
        target = compute_relative_target(source, dot_opencode, namespace, "rules")
        expected = Path("/some/project/.opencode/rules/dcc_blender/blender.md")
        assert target == expected

    def test_skill_directory_in_namespace(self) -> None:
        source = Path("/some/repo/domains/dcc/blender/skills/blender-tips")
        dot_opencode = Path("/some/project/.opencode")
        namespace = "dcc_blender"
        target = compute_relative_target(source, dot_opencode, namespace, "skills")
        expected = Path("/some/project/.opencode/skills/dcc_blender/blender-tips")
        assert target == expected

    def test_command_file(self) -> None:
        source = Path("/repo/domains/game-dev/unity/commands/build.md")
        dot_opencode = Path("/proj/.opencode")
        namespace = "game-dev_unity"
        target = compute_relative_target(source, dot_opencode, namespace, "commands")
        expected = Path("/proj/.opencode/commands/game-dev_unity/build.md")
        assert target == expected

    def test_deeply_nested_source(self) -> None:
        source = Path("/repo/domains/a/b/c/rules/readme.md")
        dot_opencode = Path("/proj/.opencode")
        namespace = "a_b_c"
        target = compute_relative_target(source, dot_opencode, namespace, "rules")
        expected = Path("/proj/.opencode/rules/a_b_c/readme.md")
        assert target == expected
