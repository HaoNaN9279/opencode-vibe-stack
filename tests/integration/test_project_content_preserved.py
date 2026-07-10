"""Integration tests verifying that user project content is preserved
through activate/deactivate cycles.

Tests that the engine never touches user-owned files in .opencode/.
"""

from __future__ import annotations

import json
from pathlib import Path

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


def _make_project_root(tmp: Path, *, with_user_files: bool = True) -> Path:
    """Create a fake project root with .opencode/ dir.

    If *with_user_files* is True, add user-owned content.
    """
    pr = tmp / "project"
    (pr / ".opencode").mkdir(parents=True, exist_ok=True)
    if with_user_files:
        _touch(pr / ".opencode" / "rules" / "my-project-rule.md",
               "USER CONTENT — Do Not Delete")
        _touch(pr / ".opencode" / "README.md",
               "# Project-specific notes")
    return pr


def _read_opencode(project_root: Path) -> dict:
    """Read opencode.json from project, return {} if missing."""
    p = project_root / ".opencode" / "opencode.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


# ============================================================================
# Test: user content preservation
# ============================================================================


class TestProjectContentPreserved:
    """Tests verifying user files survive activate/deactivate cycles."""

    # -- scenario 1: user file survives activate → deactivate cycle --------

    def test_user_rule_file_survives_full_cycle(
        self, tmp_path: Path
    ) -> None:
        """Given a project with a user .opencode/rules/my-project-rule.md,
        When activate_domain then deactivate_domain are called,
        Then the user rule file still exists with its original content."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path, with_user_files=True)

        user_file = pr / ".opencode" / "rules" / "my-project-rule.md"
        original_content = "USER CONTENT — Do Not Delete"

        # Pre-condition: user file exists
        assert user_file.is_file()
        assert user_file.read_text(encoding="utf-8") == original_content

        activate_domain(vh, pr, "dcc/blender")
        deactivate_domain(vh, pr, "dcc/blender")

        # Post-condition: user file still exists, unmodified
        assert user_file.is_file()
        assert user_file.read_text(encoding="utf-8") == original_content

    def test_user_readme_survives_full_cycle(
        self, tmp_path: Path
    ) -> None:
        """Given a project with a user .opencode/README.md,
        When activate_domain then deactivate_domain are called,
        Then the README still exists unmodified."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path, with_user_files=True)

        readme = pr / ".opencode" / "README.md"
        original_content = "# Project-specific notes"

        assert readme.is_file()
        assert readme.read_text(encoding="utf-8") == original_content

        activate_domain(vh, pr, "dcc/blender")
        deactivate_domain(vh, pr, "dcc/blender")

        assert readme.is_file()
        assert readme.read_text(encoding="utf-8") == original_content

    # -- scenario 2: .opencode/ is not empty after deactivation --------------

    def test_opencode_dir_is_not_empty_after_deactivation(
        self, tmp_path: Path
    ) -> None:
        """Given a project with user files,
        When activate then deactivate a domain,
        Then .opencode/ directory is NOT empty (user files remain)."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path, with_user_files=True)

        activate_domain(vh, pr, "dcc/blender")
        deactivate_domain(vh, pr, "dcc/blender")

        dot = pr / ".opencode"
        entries = list(dot.iterdir())
        assert len(entries) > 0, ".opencode/ should not be empty"

        # User files should be present
        entry_names = {e.name for e in entries}
        assert "README.md" in entry_names, "user README.md should still be present"

    def test_domain_directory_is_removed_but_user_dirs_remain(
        self, tmp_path: Path
    ) -> None:
        """Given a project with user rules,
        When activate then deactivate a domain,
        Then the domain namespace dir is removed but user file remains."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path, with_user_files=True)

        activate_domain(vh, pr, "dcc/blender")
        deactivate_domain(vh, pr, "dcc/blender")

        rules_dir = pr / ".opencode" / "rules"

        # Domain namespace file is gone (tracked files removed)
        assert not (rules_dir / "dcc_blender" / "blender.md").exists()

        # User file still in rules/
        assert (rules_dir / "my-project-rule.md").is_file()

        # rules/ directory itself is not deleted
        assert rules_dir.is_dir()

    # -- scenario 3: user opencode.json entries preserved -------------------

    def test_user_opencode_json_entries_preserved(
        self, tmp_path: Path
    ) -> None:
        """Given a project with user entries in opencode.json,
        When activate then deactivate a domain,
        Then user entries are preserved and domain entries removed."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path, with_user_files=False)

        # Write user opencode.json
        user_cfg = {
            "instructions": ["local-instruction.md"],
            "skills": {"paths": ["my-custom-skill"]},
            "mcp": {"my-server": {"command": "node", "args": ["server.js"]}},
        }
        oc_path = pr / ".opencode" / "opencode.json"
        oc_path.parent.mkdir(parents=True, exist_ok=True)
        oc_path.write_text(json.dumps(user_cfg, indent=2), encoding="utf-8")

        activate_domain(vh, pr, "dcc/blender")
        deactivate_domain(vh, pr, "dcc/blender")

        cfg = _read_opencode(pr)

        # User entries preserved
        assert "local-instruction.md" in cfg.get("instructions", [])
        assert "my-custom-skill" in cfg.get("skills", {}).get("paths", [])
        assert cfg["mcp"]["my-server"] == {"command": "node", "args": ["server.js"]}

        # Domain entries removed
        assert ".opencode/rules/dcc_blender/*.md" not in cfg.get("instructions", [])
        assert ".opencode/skills/dcc_blender" not in cfg.get("skills", {}).get(
            "paths", []
        )

    # -- scenario 4: user content survives multiple activate/deactivate ------

    def test_user_content_survives_multiple_cycles(
        self, tmp_path: Path
    ) -> None:
        """Given a project with user files,
        When activate/deactivate is called twice,
        Then user files survive all cycles."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path, with_user_files=True)

        user_file = pr / ".opencode" / "rules" / "my-project-rule.md"
        original_content = "USER CONTENT — Do Not Delete"

        # Cycle 1
        activate_domain(vh, pr, "dcc/blender")
        deactivate_domain(vh, pr, "dcc/blender")
        assert user_file.read_text(encoding="utf-8") == original_content

        # Cycle 2 — same domain again
        activate_domain(vh, pr, "dcc/blender")
        deactivate_domain(vh, pr, "dcc/blender")
        assert user_file.read_text(encoding="utf-8") == original_content

        # State should be clean
        state = read_state(pr)
        assert state.domains == {}

    # -- scenario 5: user file in .opencode/ root is untouched ---------------

    def test_user_file_in_opencode_root_is_untouched(
        self, tmp_path: Path
    ) -> None:
        """Given a user file directly in .opencode/ (not in a subdir),
        When activate then deactivate a domain,
        Then the file is completely untouched."""
        vh = _make_vibe_home(tmp_path)
        pr = tmp_path / "project"
        (pr / ".opencode").mkdir(parents=True, exist_ok=True)

        user_file = pr / ".opencode" / "my-notes.txt"
        _touch(user_file, "These are my personal notes")

        activate_domain(vh, pr, "dcc/blender")
        deactivate_domain(vh, pr, "dcc/blender")

        assert user_file.is_file()
        assert user_file.read_text(encoding="utf-8") == "These are my personal notes"

    # -- scenario 6: empty project (no user files) works fine ---------------

    def test_clean_project_with_no_user_files_works(
        self, tmp_path: Path
    ) -> None:
        """Given a clean project with no user files,
        When activate then deactivate a domain,
        Then no errors and state is clean."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path, with_user_files=False)

        activate_domain(vh, pr, "dcc/blender")
        deactivate_domain(vh, pr, "dcc/blender")

        # State should be empty
        state = read_state(pr)
        assert state.domains == {}
