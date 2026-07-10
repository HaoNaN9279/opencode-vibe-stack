"""Integration tests for sync (refresh) end-to-end workflows.

Tests the activate → modify source → sync → verify update pipeline using
real engine calls against a temporary filesystem.
"""

from __future__ import annotations

import json
from pathlib import Path

from vibe_stack.sync.engine import activate_domain, sync_all_active


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
    """Create a fake project root with .opencode/ dir."""
    pr = tmp / "project"
    (pr / ".opencode").mkdir(parents=True, exist_ok=True)
    return pr


# ============================================================================
# Test: sync/refresh end-to-end
# ============================================================================


class TestSyncRefresh:
    """End-to-end sync (refresh) integration tests."""

    # -- scenario 1: modified source rule is reflected after sync -----------

    def test_modified_source_rule_is_copied_on_sync(
        self, tmp_path: Path
    ) -> None:
        """Given an activated domain with a source rule modified after activation,
        When sync_all_active is called,
        Then the target file content matches the updated source."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "dcc/blender")

        # Verify original content
        target_rule = pr / ".opencode" / "rules" / "dcc_blender" / "blender.md"
        assert target_rule.read_text(encoding="utf-8") == "# Blender Rules"

        # Modify the source file
        source_rule = vh / "domains" / "dcc" / "blender" / "rules" / "blender.md"
        source_rule.write_text("# Blender Rules v2 — Updated!", encoding="utf-8")

        # Run sync
        sync_all_active(vh, pr)

        # Target file should now reflect the updated source
        assert target_rule.is_file()
        assert target_rule.read_text(encoding="utf-8") == "# Blender Rules v2 — Updated!"

    def test_modified_source_skill_is_updated_on_sync(
        self, tmp_path: Path
    ) -> None:
        """Given an activated domain with a source skill modified after activation,
        When sync_all_active is called,
        Then the target skill content matches the updated source."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "dcc/blender")

        target_skill = pr / ".opencode" / "skills" / "dcc_blender" / "blender-tool" / "SKILL.md"
        assert target_skill.read_text(encoding="utf-8") == "# Blender Tool Skill"

        # Modify the source skill file
        source_skill = vh / "domains" / "dcc" / "blender" / "skills" / "blender-tool" / "SKILL.md"
        source_skill.write_text("# Blender Tool Skill v2 — Enhanced!", encoding="utf-8")

        sync_all_active(vh, pr)

        assert target_skill.read_text(encoding="utf-8") == "# Blender Tool Skill v2 — Enhanced!"

    # -- scenario 2: new source file is picked up after sync ----------------

    def test_new_source_file_is_copied_on_sync(
        self, tmp_path: Path
    ) -> None:
        """Given an activated domain where a new rule file is added after activation,
        When sync_all_active is called,
        Then the new file appears in the target."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "dcc/blender")

        # Add a new rule file to the source
        source_new = vh / "domains" / "dcc" / "blender" / "rules" / "new-rule.md"
        _touch(source_new, "# New Rule Content")

        sync_all_active(vh, pr)

        target_new = pr / ".opencode" / "rules" / "dcc_blender" / "new-rule.md"
        assert target_new.is_file()
        assert target_new.read_text(encoding="utf-8") == "# New Rule Content"

        # Original file still present
        target_original = pr / ".opencode" / "rules" / "dcc_blender" / "blender.md"
        assert target_original.is_file()

    # -- scenario 3: deleted target file is restored on sync ----------------

    def test_deleted_target_file_is_restored_on_sync(
        self, tmp_path: Path
    ) -> None:
        """Given an activated domain where a target file is manually deleted,
        When sync_all_active is called,
        Then the file is restored."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "dcc/blender")

        # Manually delete target file (simulate accidental deletion)
        target_rule = pr / ".opencode" / "rules" / "dcc_blender" / "blender.md"
        target_rule.unlink()
        assert not target_rule.exists()

        sync_all_active(vh, pr)

        assert target_rule.is_file()
        assert target_rule.read_text(encoding="utf-8") == "# Blender Rules"

    # -- scenario 4: sync with multiple active domains ----------------------

    def test_sync_multiple_active_domains(
        self, tmp_path: Path
    ) -> None:
        """Given two active domains,
        When sync_all_active is called after modifying both sources,
        Then both targets are updated."""
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

        # Modify both sources
        (vh / "domains" / "dcc" / "blender" / "rules" / "blender.md").write_text(
            "# Updated Blender", encoding="utf-8"
        )
        (vh / "domains" / "ai" / "tooling" / "rules" / "tooling.md").write_text(
            "# Updated Tooling", encoding="utf-8"
        )

        sync_all_active(vh, pr)

        target_a = pr / ".opencode" / "rules" / "dcc_blender" / "blender.md"
        target_b = pr / ".opencode" / "rules" / "ai_tooling" / "tooling.md"
        assert target_a.read_text(encoding="utf-8") == "# Updated Blender"
        assert target_b.read_text(encoding="utf-8") == "# Updated Tooling"

    # -- scenario 5: sync on empty state is a no-op -------------------------

    def test_sync_on_empty_state_is_noop(
        self, tmp_path: Path
    ) -> None:
        """Given a project with no active domains,
        When sync_all_active is called,
        Then no error is raised and nothing changes."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        # No exception
        sync_all_active(vh, pr)

        # Verify nothing was created under .opencode/
        items = list((pr / ".opencode").iterdir())
        # Should only have the directory itself (no domain files)
        assert all(not (item.is_dir() and item.name in ("rules", "skills", "agents"))
                   for item in items)
