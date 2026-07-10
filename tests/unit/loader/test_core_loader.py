"""Tests for core config loader — load_core()."""

from __future__ import annotations

from pathlib import Path

import pytest

from vibe_stack.loader.core_loader import load_core
from vibe_stack.model.domain import CoreConfig


class TestLoadCore:
    """Tests for load_core() — loading core/ configuration."""

    # ------------------------------------------------------------------
    # Happy path — individual directory scanning
    # ------------------------------------------------------------------

    def test_scans_rules(self, tmp_path: Path) -> None:
        """load_core should find .md files in core/rules/."""
        core = tmp_path / "core"
        rules_dir = core / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "global.md").write_text("# Global")
        (rules_dir / "privacy.md").write_text("# Privacy")
        (rules_dir / "notes.txt").write_text("not a rule")  # ignored

        result = load_core(core)

        assert isinstance(result, CoreConfig)
        assert result.rules == sorted([rules_dir / "global.md", rules_dir / "privacy.md"])

    def test_scans_agents(self, tmp_path: Path) -> None:
        """load_core should find .md files in core/agents/."""
        core = tmp_path / "core"
        agents_dir = core / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "coder.md").write_text("# Coder")
        (agents_dir / "reviewer.md").write_text("# Reviewer")

        result = load_core(core)

        assert result.agents == sorted([agents_dir / "coder.md", agents_dir / "reviewer.md"])

    def test_scans_commands(self, tmp_path: Path) -> None:
        """load_core should find .md files in core/commands/."""
        core = tmp_path / "core"
        cmds_dir = core / "commands"
        cmds_dir.mkdir(parents=True)
        (cmds_dir / "deploy.md").write_text("# Deploy")
        (cmds_dir / "lint.md").write_text("# Lint")

        result = load_core(core)

        assert result.commands == sorted([cmds_dir / "deploy.md", cmds_dir / "lint.md"])

    def test_scans_mcp(self, tmp_path: Path) -> None:
        """load_core should find .json files and subdirs in core/mcp/."""
        core = tmp_path / "core"
        mcp_dir = core / "mcp"
        mcp_dir.mkdir(parents=True)
        (mcp_dir / "server.json").write_text("{}")
        (mcp_dir / "extra.json").write_text("{}")
        (mcp_dir / "notes.txt").write_text("ignored")
        sub = mcp_dir / "binary-server"
        sub.mkdir()
        (sub / "server.exe").write_text("")

        result = load_core(core)

        assert result.mcp_files == sorted([mcp_dir / "server.json", mcp_dir / "extra.json"])
        assert result.mcp_dirs == [sub]

    def test_scans_skills(self, tmp_path: Path) -> None:
        """load_core should find subdirs containing SKILL.md in core/skills/."""
        core = tmp_path / "core"
        skills_dir = core / "skills"
        skills_dir.mkdir(parents=True)

        (skills_dir / "python" / "SKILL.md").parent.mkdir(parents=True)
        (skills_dir / "python" / "SKILL.md").write_text("# Python")

        (skills_dir / "typescript" / "SKILL.md").parent.mkdir(parents=True)
        (skills_dir / "typescript" / "SKILL.md").write_text("# TypeScript")

        (skills_dir / "empty-dir").mkdir()  # no SKILL.md → ignored

        result = load_core(core)

        python_skill = skills_dir / "python"
        typescript_skill = skills_dir / "typescript"
        assert result.skills == sorted([python_skill, typescript_skill])

    # ------------------------------------------------------------------
    # Missing/optional directories
    # ------------------------------------------------------------------

    def test_missing_rules_returns_empty(self, tmp_path: Path) -> None:
        """load_core should return empty rules list when core/rules/ is missing."""
        core = tmp_path / "core"
        core.mkdir()
        result = load_core(core)
        assert result.rules == []

    def test_missing_agents_returns_empty(self, tmp_path: Path) -> None:
        """load_core should return empty agents list when core/agents/ is missing."""
        core = tmp_path / "core"
        core.mkdir()
        result = load_core(core)
        assert result.agents == []

    def test_missing_commands_returns_empty(self, tmp_path: Path) -> None:
        """load_core should return empty commands list when core/commands/ is missing."""
        core = tmp_path / "core"
        core.mkdir()
        result = load_core(core)
        assert result.commands == []

    def test_missing_mcp_returns_empty_lists(self, tmp_path: Path) -> None:
        """load_core should return empty mcp lists when core/mcp/ is missing."""
        core = tmp_path / "core"
        core.mkdir()
        result = load_core(core)
        assert result.mcp_files == []
        assert result.mcp_dirs == []

    def test_missing_skills_returns_empty(self, tmp_path: Path) -> None:
        """load_core should return empty skills list when core/skills/ is missing."""
        core = tmp_path / "core"
        core.mkdir()
        result = load_core(core)
        assert result.skills == []

    def test_entirely_missing_core_directory(self, tmp_path: Path) -> None:
        """load_core should handle a non-existent core directory gracefully."""
        core = tmp_path / "core"  # don't create it
        result = load_core(core)
        assert isinstance(result, CoreConfig)
        assert result.rules == []
        assert result.agents == []
        assert result.commands == []
        assert result.mcp_files == []
        assert result.mcp_dirs == []
        assert result.skills == []

    # ------------------------------------------------------------------
    # Combined / integration
    # ------------------------------------------------------------------

    def test_all_categories_together(self, tmp_path: Path) -> None:
        """load_core should populate all categories from a fully populated core/."""
        core = tmp_path / "core"

        # rules
        (core / "rules").mkdir(parents=True)
        (core / "rules" / "a.md").write_text("")

        # agents
        (core / "agents").mkdir(parents=True)
        (core / "agents" / "b.md").write_text("")

        # commands
        (core / "commands").mkdir(parents=True)
        (core / "commands" / "c.md").write_text("")

        # mcp
        (core / "mcp").mkdir(parents=True)
        (core / "mcp" / "d.json").write_text("")
        (core / "mcp" / "server").mkdir()
        (core / "mcp" / "server" / "exe").write_text("")

        # skills
        (core / "skills" / "skill-a" / "SKILL.md").parent.mkdir(parents=True)
        (core / "skills" / "skill-a" / "SKILL.md").write_text("")

        result = load_core(core)

        assert len(result.rules) == 1
        assert len(result.agents) == 1
        assert len(result.commands) == 1
        assert len(result.mcp_files) == 1
        assert len(result.mcp_dirs) == 1
        assert len(result.skills) == 1

    def test_returns_core_config_dataclass(self, tmp_path: Path) -> None:
        """load_core should always return a CoreConfig dataclass instance."""
        core = tmp_path / "core"
        core.mkdir()
        result = load_core(core)
        assert isinstance(result, CoreConfig)

    def test_results_sorted(self, tmp_path: Path) -> None:
        """load_core should return sorted lists for deterministic output."""
        core = tmp_path / "core"

        rules_dir = core / "rules"
        rules_dir.mkdir(parents=True)
        for name in ("z.md", "a.md", "m.md"):
            (rules_dir / name).write_text("")

        result = load_core(core)

        names = [p.name for p in result.rules]
        assert names == sorted(names)

    def test_only_md_files_in_rules(self, tmp_path: Path) -> None:
        """load_core should only pick .md files from rules/ (skip non-.md)."""
        core = tmp_path / "core"
        rules_dir = core / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "valid.md").write_text("")
        (rules_dir / "script.py").write_text("")
        (rules_dir / "data.json").write_text("")
        (rules_dir / "notes.txt").write_text("")

        result = load_core(core)

        assert len(result.rules) == 1
        assert result.rules[0].suffix == ".md"

    def test_only_md_files_in_agents(self, tmp_path: Path) -> None:
        """load_core should only pick .md files from agents/."""
        core = tmp_path / "core"
        agents_dir = core / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "agent.md").write_text("")
        (agents_dir / "agent.yaml").write_text("")
        (agents_dir / "readme.txt").write_text("")

        result = load_core(core)

        assert len(result.agents) == 1
        assert result.agents[0].suffix == ".md"

    def test_only_md_files_in_commands(self, tmp_path: Path) -> None:
        """load_core should only pick .md files from commands/."""
        core = tmp_path / "core"
        cmds_dir = core / "commands"
        cmds_dir.mkdir(parents=True)
        (cmds_dir / "cmd.md").write_text("")
        (cmds_dir / "script.sh").write_text("")

        result = load_core(core)

        assert len(result.commands) == 1
        assert result.commands[0].suffix == ".md"

    def test_only_json_files_in_mcp(self, tmp_path: Path) -> None:
        """load_core should only pick .json files for mcp_files."""
        core = tmp_path / "core"
        mcp_dir = core / "mcp"
        mcp_dir.mkdir(parents=True)
        (mcp_dir / "cfg.json").write_text("")
        (mcp_dir / "cfg.yaml").write_text("")
        (mcp_dir / "notes.txt").write_text("")

        result = load_core(core)

        assert len(result.mcp_files) == 1
        assert result.mcp_files[0].suffix == ".json"

    def test_skills_ignores_items_without_skill_md(self, tmp_path: Path) -> None:
        """load_core should skip subdirs that don't contain SKILL.md."""
        core = tmp_path / "core"
        skills_dir = core / "skills"
        skills_dir.mkdir(parents=True)

        # has SKILL.md
        (skills_dir / "valid-skill" / "SKILL.md").parent.mkdir()
        (skills_dir / "valid-skill" / "SKILL.md").write_text("")

        # file, not dir
        (skills_dir / "some-file.txt").write_text("")

        # empty dir
        (skills_dir / "empty-dir").mkdir()

        # dir without SKILL.md
        (skills_dir / "no-skill" / "helper.py").parent.mkdir()
        (skills_dir / "no-skill" / "helper.py").write_text("")

        result = load_core(core)

        assert result.skills == [skills_dir / "valid-skill"]

    def test_mcp_subdirs_only_directories(self, tmp_path: Path) -> None:
        """load_core should only include directories from mcp/ as mcp_dirs, not files."""
        core = tmp_path / "core"
        mcp_dir = core / "mcp"
        mcp_dir.mkdir(parents=True)

        (mcp_dir / "server-a").mkdir()
        (mcp_dir / "server-b").mkdir()
        (mcp_dir / "notes.txt").write_text("")
        (mcp_dir / "config.yaml").write_text("")

        result = load_core(core)

        assert result.mcp_dirs == sorted([mcp_dir / "server-a", mcp_dir / "server-b"])
