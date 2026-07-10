"""Integration tests for domain activation end-to-end workflows.

Tests the full activate_domain pipeline using real engine calls against a
temporary filesystem created via tmp_path.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vibe_stack.sync.engine import activate_domain
from vibe_stack.sync.state_manager import read_state


# ============================================================================
# Helpers
# ============================================================================


def _touch(path: Path, content: str = "") -> Path:
    """Create a file (and parent directories) at *path* with *content*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _make_vibe_home(tmp: Path) -> Path:
    """Create a fake vibe-stack repo with core/ and domains/dcc/blender/ structures.

    Returns the vibe_home root path.
    """
    vh = tmp / "vibe-home"

    # -- core/ --
    _touch(vh / "core" / "rules" / "00-global.md", "# Global Rules")
    _touch(vh / "core" / "skills" / "caveman" / "SKILL.md", "# Caveman Skill")

    # -- domains/dcc/blender --
    blender = vh / "domains" / "dcc" / "blender"
    _touch(blender / "domain.json", json.dumps({
        "name": "blender",
        "description": "Blender 3D integration",
        "version": "1.0.0",
    }))
    _touch(blender / "rules" / "blender.md", "# Blender Rules")
    _touch(blender / "skills" / "blender-tool" / "SKILL.md", "# Blender Tool Skill")

    return vh


def _make_project_root(tmp: Path) -> Path:
    """Create a fake project root with .opencode/ dir and a user file."""
    pr = tmp / "project"
    (pr / ".opencode").mkdir(parents=True, exist_ok=True)
    # User's own project file (should survive activation/deactivation)
    _touch(pr / ".opencode" / "rules" / "my-project-rule.md", "# My Project Rule")
    return pr


def _read_opencode(project_root: Path) -> dict:
    """Read opencode.json from project, return {} if missing."""
    p = project_root / ".opencode" / "opencode.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


# ============================================================================
# Test: activation end-to-end
# ============================================================================


class TestActivateFull:
    """End-to-end activation integration tests."""

    # -- scenario 1: copied files exist at expected paths ------------------

    def test_copied_rule_file_exists_under_namespace(
        self, tmp_path: Path
    ) -> None:
        """Given a domain with rule files,
        When activate_domain is called,
        Then the rule file is copied to .opencode/rules/{namespace}/."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "dcc/blender")

        ns = "dcc_blender"
        target = pr / ".opencode" / "rules" / ns / "blender.md"
        assert target.is_file()
        assert target.read_text(encoding="utf-8") == "# Blender Rules"

    def test_copied_skill_directory_exists_under_namespace(
        self, tmp_path: Path
    ) -> None:
        """Given a domain with a skills directory,
        When activate_domain is called,
        Then the skill directory is copied to .opencode/skills/{namespace}/."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "dcc/blender")

        ns = "dcc_blender"
        skill_file = pr / ".opencode" / "skills" / ns / "blender-tool" / "SKILL.md"
        assert skill_file.is_file()
        assert skill_file.read_text(encoding="utf-8") == "# Blender Tool Skill"

    # -- scenario 2: opencode.json has instructions entry -------------------

    def test_opencode_json_has_instructions_entry(
        self, tmp_path: Path
    ) -> None:
        """Given a clean project,
        When activate_domain is called,
        Then opencode.json instructions contain the domain glob."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "dcc/blender")

        cfg = _read_opencode(pr)
        assert "instructions" in cfg
        assert ".opencode/rules/dcc_blender/*.md" in cfg["instructions"]

    def test_opencode_json_has_skills_paths_entry(
        self, tmp_path: Path
    ) -> None:
        """Given a clean project,
        When activate_domain is called,
        Then opencode.json skills.paths contain the domain skills path."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "dcc/blender")

        cfg = _read_opencode(pr)
        assert "skills" in cfg
        assert "paths" in cfg["skills"]
        assert ".opencode/skills/dcc_blender" in cfg["skills"]["paths"]

    # -- scenario 3: state file records activation -------------------------

    def test_vibe_stack_state_json_records_active_domain(
        self, tmp_path: Path
    ) -> None:
        """Given a clean project,
        When activate_domain is called,
        Then .vibe-stack-state.json records the domain as active."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "dcc/blender")

        state = read_state(pr)
        assert "dcc/blender" in state.domains
        ds = state.domains["dcc/blender"]
        assert ds.domain_key == "dcc/blender"
        assert ds.namespace == "dcc_blender"

    def test_state_file_tracks_files_and_directories(
        self, tmp_path: Path
    ) -> None:
        """Given a domain with rules and skills,
        When activate_domain is called,
        Then DomainState tracks exact files and directories."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "dcc/blender")

        state = read_state(pr)
        ds = state.domains["dcc/blender"]
        assert "rules/dcc_blender/blender.md" in ds.files
        assert "skills/dcc_blender/blender-tool" in ds.directories

    def test_state_tracks_opencode_entries(
        self, tmp_path: Path
    ) -> None:
        """Given an activated domain,
        When read_state is called,
        Then DomainState.opencode_entries has instructions and skills.paths."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "dcc/blender")

        state = read_state(pr)
        ds = state.domains["dcc/blender"]
        oe = ds.opencode_entries
        assert "instructions" in oe
        assert ".opencode/rules/dcc_blender/*.md" in oe["instructions"]
        assert "skills.paths" in oe
        assert ".opencode/skills/dcc_blender" in oe["skills.paths"]

    # -- scenario 4: user content is untouched ------------------------------

    def test_user_project_file_survives_activation(
        self, tmp_path: Path
    ) -> None:
        """Given a project with a user .opencode/rules/my-project-rule.md,
        When activate_domain is called,
        Then the user file is still present and unmodified."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        user_file = pr / ".opencode" / "rules" / "my-project-rule.md"
        assert user_file.is_file()  # pre-condition

        activate_domain(vh, pr, "dcc/blender")

        assert user_file.is_file()
        assert user_file.read_text(encoding="utf-8") == "# My Project Rule"

    # -- scenario 5: multiple activations work ------------------------------

    def test_activate_two_domains_side_by_side(
        self, tmp_path: Path
    ) -> None:
        """Given a project with two domains,
        When both are activated,
        Then files for both are present and state records both."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        # Add second domain: ai/tooling
        ai_dir = vh / "domains" / "ai" / "tooling"
        _touch(ai_dir / "domain.json", json.dumps({
            "name": "tooling",
            "description": "AI tooling",
            "version": "1.0.0",
        }))
        _touch(ai_dir / "rules" / "tooling.md", "# AI Tooling Rules")

        activate_domain(vh, pr, "dcc/blender")
        activate_domain(vh, pr, "ai/tooling")

        # Both rule files exist
        assert (pr / ".opencode" / "rules" / "dcc_blender" / "blender.md").is_file()
        assert (pr / ".opencode" / "rules" / "ai_tooling" / "tooling.md").is_file()

        # State records both
        state = read_state(pr)
        assert "dcc/blender" in state.domains
        assert "ai/tooling" in state.domains

        # opencode.json has entries for both
        cfg = _read_opencode(pr)
        assert ".opencode/rules/dcc_blender/*.md" in cfg["instructions"]
        assert ".opencode/rules/ai_tooling/*.md" in cfg["instructions"]
