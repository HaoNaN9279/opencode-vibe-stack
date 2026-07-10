"""Tests for file copier (RED phase — TDD).

Tests the three functions and one dataclass of copier.py:
    FileChanges, sync_domain_files, remove_domain_files, sync_core_files.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from vibe_stack.model.domain import CoreConfig, DomainConfig, DomainMeta
from vibe_stack.model.state import DomainState
from vibe_stack.sync.copier import (
    FileChanges,
    remove_domain_files,
    sync_core_files,
    sync_domain_files,
)


# ── helpers ───────────────────────────────────────────────────────────


def _touch(path: Path, content: str = "") -> Path:
    """Create a file (and parent directories) at *path* with *content*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _make_domain_config(
    domain_root: Path,
    domain_key: str = "dcc/blender",
    rules: list[str] | None = None,
    agents: list[str] | None = None,
    commands: list[str] | None = None,
    mcp_files: list[str] | None = None,
    mcp_dirs: list[str] | None = None,
    skills: list[str] | None = None,
) -> DomainConfig:
    """Build a DomainConfig with file lists as simple string names."""
    meta = DomainMeta(name="blender", description="test", version="1.0")
    ns = domain_key.replace("/", "_")

    def _paths(names: list[str] | None, subdir: str) -> list[Path]:
        if not names:
            return []
        return [domain_root / (f"{subdir}/{n}" if subdir else n) for n in names]

    return DomainConfig(
        meta=meta,
        domain_key=domain_key,
        namespace=ns,
        domain_root=domain_root,
        rules=_paths(rules, "rules"),
        agents=_paths(agents, "agents"),
        commands=_paths(commands, "commands"),
        mcp_files=_paths(mcp_files, "mcp"),
        mcp_dirs=_paths(mcp_dirs, "mcp"),
        skills=_paths(skills, "skills"),
    )


def _make_domain_state(
    domain_key: str = "dcc/blender",
    files: list[str] | None = None,
    directories: list[str] | None = None,
) -> DomainState:
    """Build a minimal DomainState with given files/directories."""
    ns = domain_key.replace("/", "_")
    return DomainState(
        domain_key=domain_key,
        namespace=ns,
        activated_at="2025-07-10T12:00:00Z",
        files=files or [],
        directories=directories or [],
    )


def _read_content(path: Path) -> str:
    """Read file content, return empty string if missing."""
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return ""


# ── FileChanges ───────────────────────────────────────────────────────


class TestFileChanges:
    """Tests for FileChanges dataclass."""

    def test_defaults_are_zero(self) -> None:
        """Given no arguments, When FileChanges is instantiated,
        Then all counts default to 0."""
        fc = FileChanges()
        assert fc.created == 0
        assert fc.updated == 0
        assert fc.deleted == 0

    def test_custom_values(self) -> None:
        """Given explicit counts, When FileChanges is instantiated,
        Then they are stored correctly."""
        fc = FileChanges(created=3, updated=2, deleted=1)
        assert fc.created == 3
        assert fc.updated == 2
        assert fc.deleted == 1

    def test_is_frozen_immutable(self) -> None:
        """FileChanges should be a frozen dataclass — no mutation allowed."""
        fc = FileChanges(created=1)
        with pytest.raises(Exception):
            fc.created = 5  # type: ignore[misc]


# ── sync_domain_files ─────────────────────────────────────────────────


class TestSyncDomainFiles:
    """Tests for sync_domain_files()."""

    # -- structure ------------------------------------------------------

    def test_creates_namespace_subdirectory_structure(
        self, tmp_path: Path
    ) -> None:
        """Given a DomainConfig with rule files, When sync_domain_files
        is called, Then files are placed under .opencode/rules/<namespace>/."""
        # Given
        source = tmp_path / "domain"
        dot = tmp_path / ".opencode"
        dc = _make_domain_config(source, rules=["blender.md"])
        _touch(dc.rules[0], "# Blender Rules")

        # When
        sync_domain_files(dc, dot)

        # Then
        expected = dot / "rules" / "dcc_blender" / "blender.md"
        assert expected.is_file()
        assert expected.read_text(encoding="utf-8") == "# Blender Rules"

    def test_structure_matches_compute_relative_target(
        self, tmp_path: Path
    ) -> None:
        """Given a DomainConfig, When sync_domain_files copies a rule,
        Then the target path equals compute_relative_target output."""
        from vibe_stack.utils.path_util import compute_relative_target

        source = tmp_path / "domain"
        dot = tmp_path / ".opencode"
        dc = _make_domain_config(source, rules=["style.md"])
        _touch(dc.rules[0], "content")

        sync_domain_files(dc, dot)

        expected_path = compute_relative_target(
            dc.rules[0], dot, dc.namespace, "rules"
        )
        assert expected_path.is_file()

    # -- content correctness --------------------------------------------

    def test_copies_file_content_exactly(self, tmp_path: Path) -> None:
        """Given a DomainConfig with a rule file, When sync_domain_files
        is called, Then the copied file has identical content."""
        source = tmp_path / "domain"
        dot = tmp_path / ".opencode"
        content = "## Rule 1\n\nSome rule content.\n"
        dc = _make_domain_config(source, agents=["agent.md"])
        _touch(dc.agents[0], content)

        sync_domain_files(dc, dot)

        target = dot / "agents" / "dcc_blender" / "agent.md"
        assert target.read_text(encoding="utf-8") == content

    def test_copies_multiple_types(self, tmp_path: Path) -> None:
        """Given a DomainConfig with rules, agents, commands, When
        sync_domain_files is called, Then all types land in correct dirs."""
        source = tmp_path / "domain"
        dot = tmp_path / ".opencode"
        dc = _make_domain_config(
            source,
            rules=["r.md"],
            agents=["a.md"],
            commands=["c.md"],
            mcp_files=["srv.json"],
        )
        for f in dc.rules + dc.agents + dc.commands + dc.mcp_files:
            _touch(f, "content")

        sync_domain_files(dc, dot)

        assert (dot / "rules" / "dcc_blender" / "r.md").is_file()
        assert (dot / "agents" / "dcc_blender" / "a.md").is_file()
        assert (dot / "commands" / "dcc_blender" / "c.md").is_file()
        assert (dot / "mcp" / "dcc_blender" / "srv.json").is_file()

    # -- idempotency ----------------------------------------------------

    def test_second_call_idempotent(self, tmp_path: Path) -> None:
        """Given a successful first sync, When sync_domain_files is
        called again with unchanged source, Then 0 files are created/updated."""
        source = tmp_path / "domain"
        dot = tmp_path / ".opencode"
        dc = _make_domain_config(source, rules=["r.md"])
        _touch(dc.rules[0], "unchanged")

        first = sync_domain_files(dc, dot)
        assert first.created > 0 or first.updated > 0

        # Record mtime after first sync
        target = dot / "rules" / "dcc_blender" / "r.md"
        mtime_after = target.stat().st_mtime

        second = sync_domain_files(dc, dot)

        # No files created or updated on second call
        assert second.created == 0
        assert second.updated == 0
        # Target mtime is unchanged (no re-copy)
        assert target.stat().st_mtime == mtime_after

    # -- incremental update ---------------------------------------------

    def test_recopies_when_source_modified(self, tmp_path: Path) -> None:
        """Given a synced file, When the source content changes,
        Then a second sync copies it again and reports 'updated'."""
        source = tmp_path / "domain"
        dot = tmp_path / ".opencode"
        dc = _make_domain_config(source, rules=["config.md"])
        _touch(dc.rules[0], "v1")

        sync_domain_files(dc, dot)

        # Modify source
        dc.rules[0].write_text("v2", encoding="utf-8")

        result = sync_domain_files(dc, dot)

        assert result.updated == 1
        assert result.created == 0
        target = dot / "rules" / "dcc_blender" / "config.md"
        assert target.read_text(encoding="utf-8") == "v2"

    # -- stale cleanup --------------------------------------------------

    def test_removes_target_when_source_deleted(self, tmp_path: Path) -> None:
        """Given a previously synced file, When the source file is
        removed from DomainConfig, Then the target is deleted."""
        source = tmp_path / "domain"
        dot = tmp_path / ".opencode"
        dc = _make_domain_config(source, rules=["keep.md", "remove.md"])
        _touch(dc.rules[0], "keep")
        _touch(dc.rules[1], "remove")

        sync_domain_files(dc, dot)
        target_remove = dot / "rules" / "dcc_blender" / "remove.md"
        assert target_remove.is_file()

        # Simulate source deletion: rebuild DomainConfig without remove.md
        dc2 = _make_domain_config(source, rules=["keep.md"])
        # But keep.md's source still exists; remove.md's source is still on
        # disk but NOT in dc2's files list — the function should detect
        # the target file has no matching source and delete it.
        result = sync_domain_files(dc2, dot)

        assert not target_remove.exists()
        assert result.deleted == 1

    def test_removes_stale_when_entire_type_removed(
        self, tmp_path: Path
    ) -> None:
        """Given a previously synced domain with agents, When the
        DomainConfig no longer lists any agents, Then agent targets
        are deleted."""
        source = tmp_path / "domain"
        dot = tmp_path / ".opencode"
        dc = _make_domain_config(source, rules=["r.md"], agents=["a.md"])
        _touch(dc.rules[0], "r")
        _touch(dc.agents[0], "a")

        sync_domain_files(dc, dot)

        # Agent target exists
        agent_target = dot / "agents" / "dcc_blender" / "a.md"
        assert agent_target.is_file()

        # Rebuild config without agents
        dc2 = _make_domain_config(source, rules=["r.md"])
        result = sync_domain_files(dc2, dot)

        assert not agent_target.exists()
        assert result.deleted >= 1

    # -- return values --------------------------------------------------

    def test_returns_file_changes_with_counts(self, tmp_path: Path) -> None:
        """Given a fresh sync with 2 new files, When sync_domain_files
        is called, Then FileChanges reports created=2."""
        source = tmp_path / "domain"
        dot = tmp_path / ".opencode"
        dc = _make_domain_config(source, rules=["a.md", "b.md"])
        _touch(dc.rules[0], "a")
        _touch(dc.rules[1], "b")

        result = sync_domain_files(dc, dot)

        assert isinstance(result, FileChanges)
        assert result.created == 2
        assert result.updated == 0
        assert result.deleted == 0

    def test_total_count_includes_all_changes(self, tmp_path: Path) -> None:
        """When syncing creates files, a subsequent run after modifying
        and deleting results in correct total counts."""
        source = tmp_path / "domain"
        dot = tmp_path / ".opencode"
        dc = _make_domain_config(source, rules=["a.md", "b.md", "c.md"])
        for f in dc.rules:
            _touch(f, "init")

        # First sync: all created
        r1 = sync_domain_files(dc, dot)
        assert r1.created == 3

        # Modify a.md, remove c.md
        dc2 = _make_domain_config(source, rules=["a.md", "b.md"])
        dc2.rules[0].write_text("modified", encoding="utf-8")

        r2 = sync_domain_files(dc2, dot)
        assert r2.created == 0
        assert r2.updated == 1  # a.md modified
        assert r2.deleted == 1  # c.md removed

    # -- skills as directories ------------------------------------------

    def test_copies_skill_as_directory_tree(self, tmp_path: Path) -> None:
        """Given a DomainConfig with a skill directory, When
        sync_domain_files is called, Then the entire dir tree is copied."""
        source = tmp_path / "domain"
        dot = tmp_path / ".opencode"
        skill_dir = source / "skills" / "render-skill"
        _touch(skill_dir / "SKILL.md", "# Render Skill")
        _touch(skill_dir / "helper.py", "# helper")
        (skill_dir / "assets").mkdir()
        _touch(skill_dir / "assets" / "icon.png", "fake-png")

        dc = _make_domain_config(source, skills=["render-skill"])

        result = sync_domain_files(dc, dot)

        target_skill = dot / "skills" / "dcc_blender" / "render-skill"
        assert target_skill.is_dir()
        assert (target_skill / "SKILL.md").is_file()
        assert (target_skill / "helper.py").is_file()
        assert (target_skill / "assets" / "icon.png").is_file()
        # Skill dir copy should count as 1 create (not each file)
        assert result.created >= 1

    def test_skill_dir_copy_preserves_content(self, tmp_path: Path) -> None:
        """Skill directory copy must preserve file contents exactly."""
        source = tmp_path / "domain"
        dot = tmp_path / ".opencode"
        skill_dir = source / "skills" / "my-skill"
        _touch(skill_dir / "SKILL.md", "skill body")
        _touch(skill_dir / "references" / "guide.md", "guide text")

        dc = _make_domain_config(source, skills=["my-skill"])
        sync_domain_files(dc, dot)

        target = dot / "skills" / "dcc_blender" / "my-skill"
        assert (target / "SKILL.md").read_text(encoding="utf-8") == "skill body"
        assert (target / "references" / "guide.md").read_text(
            encoding="utf-8"
        ) == "guide text"

    # -- mcp directories ------------------------------------------------

    def test_copies_mcp_directories(self, tmp_path: Path) -> None:
        """Given a DomainConfig with mcp_dirs (companion folders), When
        sync_domain_files is called, Then the dirs are copied as trees."""
        source = tmp_path / "domain"
        dot = tmp_path / ".opencode"
        mcp_dir = source / "mcp" / "blender-server"
        _touch(mcp_dir / "server.exe", "fake-binary")
        _touch(mcp_dir / "config.toml", "[server]\n")

        dc = _make_domain_config(
            source,
            mcp_files=["config.json"],
            mcp_dirs=["blender-server"],
        )
        _touch(source / "mcp" / "config.json", '{"name":"blender"}')

        result = sync_domain_files(dc, dot)

        target_dir = dot / "mcp" / "dcc_blender" / "blender-server"
        assert target_dir.is_dir()
        assert (target_dir / "server.exe").is_file()
        assert (target_dir / "config.toml").is_file()
        assert result.created >= 2  # mcp_file + mcp_dir


# ── remove_domain_files ───────────────────────────────────────────────


class TestRemoveDomainFiles:
    """Tests for remove_domain_files()."""

    def test_deletes_all_files_listed_in_domain_state(
        self, tmp_path: Path
    ) -> None:
        """Given a DomainState with tracked files, When
        remove_domain_files is called, Then all those files are deleted."""
        dot = tmp_path / ".opencode"
        dot.mkdir()

        f1 = dot / "rules" / "dcc_blender" / "blender.md"
        f2 = dot / "agents" / "dcc_blender" / "agent.md"
        _touch(f1, "r1")
        _touch(f2, "a1")

        ds = _make_domain_state(
            files=[
                "rules/dcc_blender/blender.md",
                "agents/dcc_blender/agent.md",
            ]
        )

        remove_domain_files(ds, dot)

        assert not f1.exists()
        assert not f2.exists()

    def test_deletes_all_directories_listed_in_domain_state(
        self, tmp_path: Path
    ) -> None:
        """Given a DomainState with tracked directories, When
        remove_domain_files is called, Then all those dirs are deleted."""
        dot = tmp_path / ".opencode"
        dot.mkdir()

        d1 = dot / "skills" / "dcc_blender" / "render-skill"
        _touch(d1 / "SKILL.md", "skill")
        d2 = dot / "mcp" / "dcc_blender" / "server"
        _touch(d2 / "bin.exe", "fake")

        ds = _make_domain_state(
            directories=[
                "skills/dcc_blender/render-skill",
                "mcp/dcc_blender/server",
            ]
        )

        remove_domain_files(ds, dot)

        assert not d1.exists()
        assert not d2.exists()

    def test_handles_nonexistent_paths_gracefully(
        self, tmp_path: Path
    ) -> None:
        """Given DomainState paths that don't exist on disk, When
        remove_domain_files is called, Then no error is raised."""
        dot = tmp_path / ".opencode"
        dot.mkdir()

        ds = _make_domain_state(
            files=["rules/dcc_blender/ghost.md"],
            directories=["skills/dcc_blender/ghost-skill"],
        )

        # Should not raise
        remove_domain_files(ds, dot)

    def test_handles_empty_state(self, tmp_path: Path) -> None:
        """Given an empty DomainState, When remove_domain_files is
        called, Then nothing happens."""
        dot = tmp_path / ".opencode"
        dot.mkdir()

        ds = _make_domain_state()

        # Should not raise
        remove_domain_files(ds, dot)


# ── sync_core_files ───────────────────────────────────────────────────


class TestSyncCoreFiles:
    """Tests for sync_core_files()."""

    def _make_core_source(self, core_root: Path) -> CoreConfig:
        """Create core config with touch'd files under *core_root*."""
        rules = [_touch(core_root / "rules" / "00-global.md", "# Global")]
        agents = [_touch(core_root / "agents" / "runner.md", "# Runner")]
        commands = [_touch(core_root / "commands" / "build.md", "# Build")]
        mcp_root = core_root / "mcp"
        mcp_files = [_touch(mcp_root / "playwright.json", '{"name":"pw"}')]
        mcp_dir = mcp_root / "playwright-server"
        _touch(mcp_dir / "server.js", "// server")
        mcp_dirs = [mcp_dir]
        skill_dir = core_root / "skills" / "caveman"
        _touch(skill_dir / "SKILL.md", "# Caveman")
        skills = [skill_dir]

        return CoreConfig(
            rules=rules,
            agents=agents,
            commands=commands,
            mcp_files=mcp_files,
            mcp_dirs=mcp_dirs,
            skills=skills,
        )

    def test_copies_rules_to_user_config_rules_dir(
        self, tmp_path: Path
    ) -> None:
        """Given a CoreConfig with rules, When sync_core_files is called,
        Then rules land in user_config/rules/ directly (no namespace)."""
        core_root = tmp_path / "core"
        user_config = tmp_path / "config" / "opencode"
        _touch(core_root / "rules" / "00-global.md", "# Global")
        cc = CoreConfig(rules=[core_root / "rules" / "00-global.md"])

        sync_core_files(cc, user_config)

        target = user_config / "rules" / "00-global.md"
        assert target.is_file()
        assert target.read_text(encoding="utf-8") == "# Global"

    def test_copies_skills_to_user_config_skills_dir(
        self, tmp_path: Path
    ) -> None:
        """Given a CoreConfig with skills, When sync_core_files is called,
        Then skill directories are copied as trees."""
        core_root = tmp_path / "core"
        user_config = tmp_path / "config" / "opencode"
        skill_dir = core_root / "skills" / "caveman"
        _touch(skill_dir / "SKILL.md", "# Caveman")
        cc = CoreConfig(skills=[skill_dir])

        sync_core_files(cc, user_config)

        target_dir = user_config / "skills" / "caveman"
        assert target_dir.is_dir()
        assert (target_dir / "SKILL.md").is_file()

    def test_copies_all_config_types(self, tmp_path: Path) -> None:
        """Given a complete CoreConfig, When sync_core_files is called,
        Then all types land in corresponding user_config subdirectories."""
        core_root = tmp_path / "core"
        user_config = tmp_path / "config" / "opencode"

        cc = self._make_core_source(core_root)

        sync_core_files(cc, user_config)

        assert (user_config / "rules" / "00-global.md").is_file()
        assert (user_config / "agents" / "runner.md").is_file()
        assert (user_config / "commands" / "build.md").is_file()
        assert (user_config / "mcp" / "playwright.json").is_file()
        assert (user_config / "mcp" / "playwright-server").is_dir()
        assert (user_config / "skills" / "caveman").is_dir()

    def test_does_not_use_namespace_subdirectory_for_core(
        self, tmp_path: Path
    ) -> None:
        """Core files go directly under user_config/<type>/, not nested
        under a namespace subdirectory (unlike domain files)."""
        core_root = tmp_path / "core"
        user_config = tmp_path / "config" / "opencode"
        _touch(core_root / "rules" / "00-global.md", "# G")
        cc = CoreConfig(rules=[core_root / "rules" / "00-global.md"])

        sync_core_files(cc, user_config)

        # Direct placement — no namespace intermediate dir
        assert (user_config / "rules" / "00-global.md").is_file()
        # There should be NO extra namespace subdirectory
        assert not any(
            d.is_dir() and d.name not in {"rules", "agents", "commands", "mcp", "skills"}
            for d in user_config.iterdir()
            if d.is_dir()
        )

    def test_core_file_content_preserved(self, tmp_path: Path) -> None:
        """Core file copy must preserve content exactly, including
        multi-line content."""
        core_root = tmp_path / "core"
        user_config = tmp_path / "config" / "opencode"
        content = "## Global Rules\n\n- Always use tabs\n- Never commit secrets\n"
        _touch(core_root / "rules" / "00-global.md", content)
        cc = CoreConfig(rules=[core_root / "rules" / "00-global.md"])

        sync_core_files(cc, user_config)

        target = user_config / "rules" / "00-global.md"
        assert target.read_text(encoding="utf-8") == content
