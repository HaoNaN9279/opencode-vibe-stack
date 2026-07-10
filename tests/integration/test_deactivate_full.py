"""Integration tests for domain deactivation end-to-end workflows.

Tests the full activate → deactivate pipeline using real engine calls against
a temporary filesystem created via tmp_path.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vibe_stack.errors import DomainNotActiveError
from vibe_stack.sync.engine import activate_domain, deactivate_domain
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
    """Create a fake vibe-stack repo with core/ and domains/dcc/blender/."""
    vh = tmp / "vibe-home"

    _touch(vh / "core" / "rules" / "00-global.md", "# Global Rules")
    _touch(vh / "core" / "skills" / "caveman" / "SKILL.md", "# Caveman Skill")

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
    _touch(pr / ".opencode" / "rules" / "my-project-rule.md", "# My Project Rule")
    return pr


def _read_opencode(project_root: Path) -> dict:
    """Read opencode.json from project, return {} if missing."""
    p = project_root / ".opencode" / "opencode.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


# ============================================================================
# Test: deactivation end-to-end
# ============================================================================


class TestDeactivateFull:
    """End-to-end deactivation integration tests."""

    # -- scenario 1: files removed ------------------------------------------

    def test_removes_rule_file_after_deactivation(
        self, tmp_path: Path
    ) -> None:
        """Given an activated domain,
        When deactivate_domain is called,
        Then the rule file is removed."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "dcc/blender")
        rule_file = pr / ".opencode" / "rules" / "dcc_blender" / "blender.md"
        assert rule_file.is_file()  # pre-condition

        deactivate_domain(vh, pr, "dcc/blender")

        assert not rule_file.exists()

    def test_removes_namespace_file_leaving_empty_parent(
        self, tmp_path: Path
    ) -> None:
        """Given an activated domain,
        When deactivate_domain is called,
        Then tracked files are removed; empty parent dir may remain."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "dcc/blender")
        rule_file = pr / ".opencode" / "rules" / "dcc_blender" / "blender.md"
        assert rule_file.is_file()  # pre-condition

        deactivate_domain(vh, pr, "dcc/blender")

        # The file is removed
        assert not rule_file.exists()
        # The namespace parent dir may still exist (empty) — that's fine

    def test_removes_skill_subdirectory_leaving_empty_parent(
        self, tmp_path: Path
    ) -> None:
        """Given an activated domain with skills,
        When deactivate_domain is called,
        Then tracked skill subdirectory is removed; empty parent may remain."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "dcc/blender")
        skill_subdir = pr / ".opencode" / "skills" / "dcc_blender" / "blender-tool"
        assert skill_subdir.is_dir()  # pre-condition

        deactivate_domain(vh, pr, "dcc/blender")

        # The tracked subdirectory is removed
        assert not skill_subdir.exists()
        # The namespace parent dir may still exist (empty) — that's fine

    # -- scenario 2: opencode.json entries removed -------------------------

    def test_removes_instructions_entry_from_opencode_json(
        self, tmp_path: Path
    ) -> None:
        """Given an activated domain,
        When deactivate_domain is called,
        Then the instructions entry is removed from opencode.json."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "dcc/blender")
        cfg_before = _read_opencode(pr)
        assert ".opencode/rules/dcc_blender/*.md" in cfg_before["instructions"]

        deactivate_domain(vh, pr, "dcc/blender")

        cfg_after = _read_opencode(pr)
        assert ".opencode/rules/dcc_blender/*.md" not in cfg_after.get(
            "instructions", []
        )

    def test_removes_skills_paths_entry_from_opencode_json(
        self, tmp_path: Path
    ) -> None:
        """Given an activated domain,
        When deactivate_domain is called,
        Then the skills.paths entry is removed from opencode.json."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "dcc/blender")
        cfg_before = _read_opencode(pr)
        assert ".opencode/skills/dcc_blender" in cfg_before["skills"]["paths"]

        deactivate_domain(vh, pr, "dcc/blender")

        cfg_after = _read_opencode(pr)
        assert ".opencode/skills/dcc_blender" not in cfg_after.get(
            "skills", {}
        ).get("paths", [])

    # -- scenario 3: state file cleaned ------------------------------------

    def test_removes_domain_from_state_file(
        self, tmp_path: Path
    ) -> None:
        """Given an activated domain,
        When deactivate_domain is called,
        Then the domain is removed from .vibe-stack-state.json."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "dcc/blender")
        assert "dcc/blender" in read_state(pr).domains  # pre-condition

        deactivate_domain(vh, pr, "dcc/blender")

        assert "dcc/blender" not in read_state(pr).domains

    def test_state_file_returns_to_default_after_full_deactivation(
        self, tmp_path: Path
    ) -> None:
        """Given an activated and then deactivated domain,
        When read_state is called,
        Then state is effectively empty."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "dcc/blender")
        deactivate_domain(vh, pr, "dcc/blender")

        state = read_state(pr)
        assert state.domains == {}
        assert state.version == 2

    # -- scenario 4: error on double deactivation --------------------------

    def test_raises_domain_not_active_on_double_deactivation(
        self, tmp_path: Path
    ) -> None:
        """Given a deactivated domain,
        When deactivate_domain is called again,
        Then DomainNotActiveError is raised."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "dcc/blender")
        deactivate_domain(vh, pr, "dcc/blender")

        with pytest.raises(DomainNotActiveError):
            deactivate_domain(vh, pr, "dcc/blender")

    # -- scenario 5: one domain deactivated, another remains ---------------

    def test_deactivate_one_domain_leaves_other_active(
        self, tmp_path: Path
    ) -> None:
        """Given two active domains,
        When one is deactivated,
        Then the other domain's files and state remain intact."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        # Add second domain
        ai_dir = vh / "domains" / "ai" / "tooling"
        _touch(ai_dir / "domain.json", json.dumps({
            "name": "tooling",
            "description": "AI tooling",
            "version": "1.0.0",
        }))
        _touch(ai_dir / "rules" / "tooling.md", "# AI Tooling Rules")

        activate_domain(vh, pr, "dcc/blender")
        activate_domain(vh, pr, "ai/tooling")

        deactivate_domain(vh, pr, "dcc/blender")

        # dcc/blender files gone
        assert not (pr / ".opencode" / "rules" / "dcc_blender" / "blender.md").exists()

        # ai/tooling files still present
        assert (pr / ".opencode" / "rules" / "ai_tooling" / "tooling.md").is_file()

        # State: only ai/tooling
        state = read_state(pr)
        assert "dcc/blender" not in state.domains
        assert "ai/tooling" in state.domains

        # opencode.json: only ai/tooling
        cfg = _read_opencode(pr)
        assert ".opencode/rules/dcc_blender/*.md" not in cfg.get("instructions", [])
        assert ".opencode/rules/ai_tooling/*.md" in cfg["instructions"]
