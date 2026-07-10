"""Tests for sync engine orchestration (RED phase — TDD).

Tests the five functions of engine.py:
    activate_domain, deactivate_domain, sync_core,
    sync_all_active, sync.

Covering all 15 required test scenarios.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from vibe_stack.errors import (
    DomainAlreadyActiveError,
    DomainNotFoundError,
    DomainNotActiveError,
)
from vibe_stack.model.domain import DomainConfig, DomainMeta
from vibe_stack.model.state import ActivationState, DomainState
from vibe_stack.sync.engine import (
    activate_domain,
    deactivate_domain,
    sync,
    sync_all_active,
    sync_core,
)
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
    """Create a fake vibe-stack repo with core/ and domains/ structures."""
    vh = tmp / "vibe-home"

    # -- core/ --
    core = vh / "core"
    _touch(core / "rules" / "00-global.md", "# Global Rules")
    _touch(core / "agents" / "runner.md", "# Runner")
    _touch(core / "skills" / "caveman" / "SKILL.md", "# Caveman Skill")
    _touch(core / "mcp" / "playwright.json", json.dumps({
        "mcpServers": {
            "playwright": {
                "type": "local",
                "command": ["playwright-server"],
                "enabled": True,
            }
        }
    }))
    _touch(core / "mcp" / "pw-server" / "server.js", "// fake")

    # -- domains/ai/data-forge --
    domain = vh / "domains" / "ai" / "data-forge"
    _touch(domain / "domain.json", json.dumps({
        "name": "data-forge",
        "description": "Data transformation MCP",
        "version": "1.0.0",
    }))
    _touch(domain / "rules" / "data-forge.md", "# Data Forge Rules")
    _touch(domain / "agents" / "forge-agent.md", "# Forge Agent")
    _touch(domain / "skills" / "data-skill" / "SKILL.md", "# Data Skill")
    _touch(domain / "mcp" / "data-forge.json", json.dumps({
        "mcpServers": {
            "data-forge": {
                "type": "local",
                "command": ["data-forge-server"],
                "enabled": True,
            }
        }
    }))

    return vh


def _make_project_root(tmp: Path) -> Path:
    """Create a fake project root with .opencode/ dir."""
    pr = tmp / "project"
    (pr / ".opencode").mkdir(parents=True, exist_ok=True)
    return pr


def _make_opencode_json(project_root: Path, content: dict | None = None) -> Path:
    """Create opencode.json under project .opencode/, return its path."""
    p = project_root / ".opencode" / "opencode.json"
    if content is None:
        content = {}
    p.write_text(json.dumps(content, indent=2), encoding="utf-8")
    return p


def _read_opencode(project_root: Path) -> dict:
    """Read opencode.json from project, return {} if missing."""
    p = project_root / ".opencode" / "opencode.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def _opencode_path(project_root: Path) -> Path:
    """Return path to project's opencode.json."""
    return project_root / ".opencode" / "opencode.json"


# ============================================================================
# activate_domain
# ============================================================================


class TestActivateDomain:
    """Tests for activate_domain()."""

    # -- scenario 1: creates namespace subdirectories with copied files ---

    def test_creates_namespace_subdirectories_with_copied_files(
        self, tmp_path: Path
    ) -> None:
        """Given a domain config with rules/agents/skills,
        When activate_domain is called,
        Then files land under .opencode/{type}/{namespace}/."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "ai/data-forge")

        ns = "ai_data-forge"
        dot = pr / ".opencode"
        assert (dot / "rules" / ns / "data-forge.md").is_file()
        assert (dot / "agents" / ns / "forge-agent.md").is_file()
        assert (dot / "skills" / ns / "data-skill" / "SKILL.md").is_file()

    # -- scenario 2: merges instructions into opencode.json ---------------

    def test_merges_instructions_into_opencode_json(
        self, tmp_path: Path
    ) -> None:
        """Given a project with existing opencode.json instructions,
        When activate_domain is called,
        Then the domain's instruction glob is appended."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)
        _make_opencode_json(pr, {"instructions": ["user-rule.md"]})

        activate_domain(vh, pr, "ai/data-forge")

        cfg = _read_opencode(pr)
        assert "user-rule.md" in cfg["instructions"]
        assert ".opencode/rules/ai_data-forge/*.md" in cfg["instructions"]

    # -- scenario 3: merges skills.paths into opencode.json ---------------

    def test_merges_skills_paths_into_opencode_json(
        self, tmp_path: Path
    ) -> None:
        """Given a project with existing skills.paths,
        When activate_domain is called,
        Then the domain's skills path is appended."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)
        _make_opencode_json(pr, {
            "skills": {"paths": ["/user/skill"]}
        })

        activate_domain(vh, pr, "ai/data-forge")

        cfg = _read_opencode(pr)
        assert "/user/skill" in cfg["skills"]["paths"]
        assert ".opencode/skills/ai_data-forge" in cfg["skills"]["paths"]

    # -- scenario 4: resolves and adds MCP servers to opencode.json -------

    def test_resolves_and_adds_mcp_servers_to_opencode_json(
        self, tmp_path: Path
    ) -> None:
        """Given a domain with MCP config,
        When activate_domain is called,
        Then MCP server is added to opencode.json with vibe: prefix."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)
        _make_opencode_json(pr)

        activate_domain(vh, pr, "ai/data-forge")

        cfg = _read_opencode(pr)
        assert "mcp" in cfg
        mcp_key = "vibe:ai_data-forge_data-forge"
        assert mcp_key in cfg["mcp"]
        assert cfg["mcp"][mcp_key]["type"] == "local"

    def test_preserves_user_mcp_servers_on_activate(
        self, tmp_path: Path
    ) -> None:
        """Given opencode.json with user MCP servers,
        When activate_domain is called,
        Then user MCP servers are preserved."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)
        _make_opencode_json(pr, {
            "mcp": {"my-server": {"command": "node"}}
        })

        activate_domain(vh, pr, "ai/data-forge")

        cfg = _read_opencode(pr)
        assert cfg["mcp"]["my-server"] == {"command": "node"}
        assert "vibe:ai_data-forge_data-forge" in cfg["mcp"]

    # -- scenario 5: records activation in state file --------------------

    def test_records_activation_in_state_file(
        self, tmp_path: Path
    ) -> None:
        """Given a fresh project,
        When activate_domain is called,
        Then the state file records the domain activation."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "ai/data-forge")

        state = read_state(pr)
        assert "ai/data-forge" in state.domains
        ds = state.domains["ai/data-forge"]
        assert ds.domain_key == "ai/data-forge"
        assert ds.namespace == "ai_data-forge"

    def test_state_tracks_files_and_directories(
        self, tmp_path: Path
    ) -> None:
        """Given a domain with rules and skills,
        When activate_domain is called,
        Then DomainState tracks the copied files and directories."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "ai/data-forge")

        state = read_state(pr)
        ds = state.domains["ai/data-forge"]
        # Files should include rule and agent files
        assert "rules/ai_data-forge/data-forge.md" in ds.files
        assert "agents/ai_data-forge/forge-agent.md" in ds.files
        # Directories should include skill dir
        assert "skills/ai_data-forge/data-skill" in ds.directories

    # -- scenario 6: raises DomainNotFoundError for bad domain key --------

    def test_raises_domain_not_found_for_bad_key(
        self, tmp_path: Path
    ) -> None:
        """Given a non-existent domain key,
        When activate_domain is called,
        Then DomainNotFoundError is raised."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        with pytest.raises(DomainNotFoundError):
            activate_domain(vh, pr, "no/such-domain")

    # -- scenario 7: raises DomainAlreadyActiveError for active domain ---

    def test_raises_domain_already_active_for_active_domain(
        self, tmp_path: Path
    ) -> None:
        """Given an already-activated domain,
        When activate_domain is called again,
        Then DomainAlreadyActiveError is raised."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "ai/data-forge")

        with pytest.raises(DomainAlreadyActiveError):
            activate_domain(vh, pr, "ai/data-forge")

    def test_activate_is_idempotent_wrt_user_files(
        self, tmp_path: Path
    ) -> None:
        """Given a project with user files in .opencode/,
        When activate_domain is called,
        Then user files are not touched."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)
        user_file = pr / ".opencode" / "user-note.md"
        _touch(user_file, "# my note")
        _make_opencode_json(pr, {"instructions": ["user-rule.md"]})

        activate_domain(vh, pr, "ai/data-forge")

        assert user_file.is_file()
        assert user_file.read_text(encoding="utf-8") == "# my note"


# ============================================================================
# deactivate_domain
# ============================================================================


class TestDeactivateDomain:
    """Tests for deactivate_domain()."""

    # -- scenario 8: removes files from .opencode/ -----------------------

    def test_removes_domain_files_from_opencode(
        self, tmp_path: Path
    ) -> None:
        """Given an activated domain,
        When deactivate_domain is called,
        Then tracked files are removed from .opencode/."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "ai/data-forge")
        ns = "ai_data-forge"
        rule_file = pr / ".opencode" / "rules" / ns / "data-forge.md"
        assert rule_file.is_file()  # pre-condition

        deactivate_domain(vh, pr, "ai/data-forge")

        assert not rule_file.exists()

    def test_removes_domain_directories_from_opencode(
        self, tmp_path: Path
    ) -> None:
        """Given an activated domain with skill directories,
        When deactivate_domain is called,
        Then tracked directories are removed."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "ai/data-forge")
        skill_dir = pr / ".opencode" / "skills" / "ai_data-forge" / "data-skill"
        assert skill_dir.is_dir()  # pre-condition

        deactivate_domain(vh, pr, "ai/data-forge")

        assert not skill_dir.exists()

    # -- scenario 9: removes entries from opencode.json -------------------

    def test_removes_instructions_entry_from_opencode_json(
        self, tmp_path: Path
    ) -> None:
        """Given an activated domain with instructions entry,
        When deactivate_domain is called,
        Then the instructions entry is removed from opencode.json."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)
        _make_opencode_json(pr, {"instructions": ["user-rule.md"]})

        activate_domain(vh, pr, "ai/data-forge")
        cfg_before = _read_opencode(pr)
        assert ".opencode/rules/ai_data-forge/*.md" in cfg_before["instructions"]

        deactivate_domain(vh, pr, "ai/data-forge")

        cfg_after = _read_opencode(pr)
        assert ".opencode/rules/ai_data-forge/*.md" not in cfg_after["instructions"]
        assert "user-rule.md" in cfg_after["instructions"]  # preserved

    def test_removes_skills_paths_entry_from_opencode_json(
        self, tmp_path: Path
    ) -> None:
        """Given an activated domain with skills.paths entry,
        When deactivate_domain is called,
        Then the skills.paths entry is removed."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)
        _make_opencode_json(pr, {"skills": {"paths": ["/user/skill"]}})

        activate_domain(vh, pr, "ai/data-forge")
        deactivate_domain(vh, pr, "ai/data-forge")

        cfg = _read_opencode(pr)
        assert ".opencode/skills/ai_data-forge" not in cfg["skills"]["paths"]
        assert "/user/skill" in cfg["skills"]["paths"]

    def test_removes_mcp_servers_from_opencode_json(
        self, tmp_path: Path
    ) -> None:
        """Given an activated domain with MCP servers,
        When deactivate_domain is called,
        Then MCP server entries are removed."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)
        _make_opencode_json(pr, {"mcp": {"my-server": {"command": "node"}}})

        activate_domain(vh, pr, "ai/data-forge")
        deactivate_domain(vh, pr, "ai/data-forge")

        cfg = _read_opencode(pr)
        assert "vibe:ai_data-forge_data-forge" not in cfg["mcp"]
        assert "my-server" in cfg["mcp"]

    # -- scenario 10: removes domain from state file ----------------------

    def test_removes_domain_from_state_file(
        self, tmp_path: Path
    ) -> None:
        """Given an activated domain,
        When deactivate_domain is called,
        Then the domain is removed from the state file."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "ai/data-forge")
        assert "ai/data-forge" in read_state(pr).domains

        deactivate_domain(vh, pr, "ai/data-forge")

        assert "ai/data-forge" not in read_state(pr).domains

    # -- scenario 11: raises DomainNotActiveError for non-active domain ---

    def test_raises_domain_not_active_for_non_active_domain(
        self, tmp_path: Path
    ) -> None:
        """Given a project with no activated domains,
        When deactivate_domain is called,
        Then DomainNotActiveError is raised."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        with pytest.raises(DomainNotActiveError):
            deactivate_domain(vh, pr, "ai/data-forge")

    def test_raises_domain_not_active_after_deactivation(
        self, tmp_path: Path
    ) -> None:
        """Given a deactivated domain,
        When deactivate_domain is called again,
        Then DomainNotActiveError is raised."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        activate_domain(vh, pr, "ai/data-forge")
        deactivate_domain(vh, pr, "ai/data-forge")

        with pytest.raises(DomainNotActiveError):
            deactivate_domain(vh, pr, "ai/data-forge")

    # -- scenario 15: user's own files preserved --------------------------

    def test_preserves_user_files_on_deactivate(
        self, tmp_path: Path
    ) -> None:
        """Given activated domain + user files in .opencode/,
        When deactivate_domain is called,
        Then user files are preserved."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        user_rules = pr / ".opencode" / "rules" / "my-local-rule.md"
        _touch(user_rules, "# local rule")
        user_skill = pr / ".opencode" / "skills" / "my-skill" / "SKILL.md"
        _touch(user_skill, "# my skill")
        _make_opencode_json(pr, {
            "instructions": ["user-rule.md"],
            "skills": {"paths": ["/user/skill"]},
            "mcp": {"my-server": {"command": "node"}},
        })

        activate_domain(vh, pr, "ai/data-forge")
        deactivate_domain(vh, pr, "ai/data-forge")

        # User files still exist
        assert user_rules.is_file()
        assert user_skill.is_file()

        # User entries in opencode.json preserved
        cfg = _read_opencode(pr)
        assert "user-rule.md" in cfg["instructions"]
        assert "/user/skill" in cfg["skills"]["paths"]
        assert cfg["mcp"]["my-server"] == {"command": "node"}

        # Domain entries removed
        assert ".opencode/rules/ai_data-forge/*.md" not in cfg["instructions"]
        assert ".opencode/skills/ai_data-forge" not in cfg["skills"]["paths"]
        assert "vibe:ai_data-forge_data-forge" not in cfg["mcp"]


# ============================================================================
# sync_core
# ============================================================================


class TestSyncCore:
    """Tests for sync_core()."""

    # -- scenario 12: copies core files to user config -------------------

    def test_copies_core_files_to_user_config_dir(
        self, tmp_path: Path
    ) -> None:
        """Given a vibe home with core/ config,
        When sync_core is called,
        Then core files are copied to user_config_dir."""
        vh = _make_vibe_home(tmp_path)
        user_config = tmp_path / "config" / "opencode"
        user_config.mkdir(parents=True, exist_ok=True)

        sync_core(vh, user_config)

        assert (user_config / "rules" / "00-global.md").is_file()
        assert (user_config / "agents" / "runner.md").is_file()
        assert (user_config / "skills" / "caveman" / "SKILL.md").is_file()

    def test_copies_core_mcp_files_to_user_config(
        self, tmp_path: Path
    ) -> None:
        """Given core MCP config files,
        When sync_core is called,
        Then MCP files are copied."""
        vh = _make_vibe_home(tmp_path)
        user_config = tmp_path / "config" / "opencode"
        user_config.mkdir(parents=True, exist_ok=True)

        sync_core(vh, user_config)

        assert (user_config / "mcp" / "playwright.json").is_file()

    # -- scenario 13: writes core entries to opencode.json ----------------

    def test_writes_core_instructions_to_opencode_json(
        self, tmp_path: Path
    ) -> None:
        """Given a user config dir,
        When sync_core is called,
        Then opencode.json has core rules instructions entry."""
        vh = _make_vibe_home(tmp_path)
        user_config = tmp_path / "config" / "opencode"
        user_config.mkdir(parents=True, exist_ok=True)
        _touch(user_config / "opencode.json", "{}")

        sync_core(vh, user_config)

        cfg = json.loads((user_config / "opencode.json").read_text(encoding="utf-8"))
        instructions = cfg.get("instructions", [])
        assert "~/.config/opencode/rules/*.md" in instructions

    def test_writes_core_skills_paths_to_opencode_json(
        self, tmp_path: Path
    ) -> None:
        """Given a user config dir,
        When sync_core is called,
        Then opencode.json has skills.paths entry."""
        vh = _make_vibe_home(tmp_path)
        user_config = tmp_path / "config" / "opencode"
        user_config.mkdir(parents=True, exist_ok=True)
        _touch(user_config / "opencode.json", "{}")

        sync_core(vh, user_config)

        cfg = json.loads((user_config / "opencode.json").read_text(encoding="utf-8"))
        skills_paths = cfg.get("skills", {}).get("paths", [])
        assert "skills" in skills_paths

    def test_writes_core_mcp_servers_to_opencode_json(
        self, tmp_path: Path
    ) -> None:
        """Given core MCP config,
        When sync_core is called,
        Then resolved MCP servers are written to opencode.json."""
        vh = _make_vibe_home(tmp_path)
        user_config = tmp_path / "config" / "opencode"
        user_config.mkdir(parents=True, exist_ok=True)
        _touch(user_config / "opencode.json", "{}")

        sync_core(vh, user_config)

        cfg = json.loads((user_config / "opencode.json").read_text(encoding="utf-8"))
        assert "mcp" in cfg
        # Core MCP gets vibe:core- prefix
        mcp_keys = [k for k in cfg["mcp"] if k.startswith("vibe:core-")]
        assert len(mcp_keys) > 0

    def test_core_sync_preserves_existing_user_config(
        self, tmp_path: Path
    ) -> None:
        """Given user config with existing entries,
        When sync_core is called,
        Then user entries are preserved."""
        vh = _make_vibe_home(tmp_path)
        user_config = tmp_path / "config" / "opencode"
        user_config.mkdir(parents=True, exist_ok=True)
        _touch(user_config / "opencode.json", json.dumps({
            "instructions": ["my-local.md"],
            "skills": {"paths": ["/my/custom/skill"]},
            "mcp": {"my-server": {"command": "node"}},
        }))

        sync_core(vh, user_config)

        cfg = json.loads((user_config / "opencode.json").read_text(encoding="utf-8"))
        assert "my-local.md" in cfg["instructions"]
        assert "/my/custom/skill" in cfg["skills"]["paths"]
        assert cfg["mcp"]["my-server"] == {"command": "node"}

    def test_sync_core_defaults_to_home_config_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given no explicit user_config_dir,
        When sync_core is called,
        Then it defaults to ~/.config/opencode/."""
        vh = _make_vibe_home(tmp_path)
        fake_home = tmp_path / "mock-home"
        fake_config = fake_home / ".config" / "opencode"
        fake_config.mkdir(parents=True, exist_ok=True)
        _touch(fake_config / "opencode.json", "{}")
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        sync_core(vh)

        cfg = json.loads((fake_config / "opencode.json").read_text(encoding="utf-8"))
        assert "~/.config/opencode/rules/*.md" in cfg.get("instructions", [])


# ============================================================================
# sync_all_active
# ============================================================================


class TestSyncAllActive:
    """Tests for sync_all_active()."""

    # -- scenario 14: re-syncs all active domains ------------------------

    def test_resyncs_all_active_domains(
        self, tmp_path: Path
    ) -> None:
        """Given multiple active domains,
        When sync_all_active is called,
        Then all domains' files and config entries are re-synced."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        # Add a second domain: dcc/blender (minimal setup)
        blender_dir = vh / "domains" / "dcc" / "blender"
        _touch(blender_dir / "domain.json", json.dumps({
            "name": "blender",
            "description": "Blender 3D integration",
            "version": "1.0.0",
        }))
        _touch(blender_dir / "rules" / "blender.md", "# Blender Rules")

        activate_domain(vh, pr, "ai/data-forge")
        activate_domain(vh, pr, "dcc/blender")

        # Simulate config drift: manually remove a file
        ns_df = "ai_data-forge"
        rule_to_delete = pr / ".opencode" / "rules" / ns_df / "data-forge.md"
        rule_to_delete.unlink()
        assert not rule_to_delete.exists()

        # Re-sync
        sync_all_active(vh, pr)

        # File is restored
        assert rule_to_delete.is_file()
        assert rule_to_delete.read_text(encoding="utf-8") == "# Data Forge Rules"

        # Both domains' entries in opencode.json
        cfg = _read_opencode(pr)
        assert ".opencode/rules/ai_data-forge/*.md" in cfg["instructions"]
        assert ".opencode/rules/dcc_blender/*.md" in cfg["instructions"]

    def test_resync_preserves_state_file(
        self, tmp_path: Path
    ) -> None:
        """Given active domains,
        When sync_all_active is called,
        Then the state file still lists all active domains."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)

        # Add second domain
        blender_dir = vh / "domains" / "dcc" / "blender"
        _touch(blender_dir / "domain.json", json.dumps({
            "name": "blender",
            "description": "Blender 3D integration",
            "version": "1.0.0",
        }))
        _touch(blender_dir / "rules" / "blender.md", "# Blender Rules")

        activate_domain(vh, pr, "ai/data-forge")
        activate_domain(vh, pr, "dcc/blender")

        sync_all_active(vh, pr)

        state = read_state(pr)
        assert set(state.domains.keys()) == {"ai/data-forge", "dcc/blender"}

    def test_sync_all_active_handles_empty_state(
        self, tmp_path: Path
    ) -> None:
        """Given a project with no active domains,
        When sync_all_active is called,
        Then no error is raised and nothing changes."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)
        _make_opencode_json(pr, {"instructions": ["user.md"]})

        sync_all_active(vh, pr)

        cfg = _read_opencode(pr)
        assert cfg["instructions"] == ["user.md"]


# ============================================================================
# sync (full flow)
# ============================================================================


class TestSync:
    """Tests for sync() — combined core + all active domains."""

    def test_full_sync_syncs_core_and_all_active_domains(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given a project with active domains,
        When sync() is called,
        Then both core and domain configs are synced."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)
        _make_opencode_json(pr)

        # Fake home for core config
        fake_home = tmp_path / "mock-home"
        fake_config = fake_home / ".config" / "opencode"
        fake_config.mkdir(parents=True, exist_ok=True)
        _touch(fake_config / "opencode.json", "{}")
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Activate a domain first
        activate_domain(vh, pr, "ai/data-forge")

        # Then run full sync
        sync(vh, pr)

        # Core entries in user config
        user_cfg = json.loads((fake_config / "opencode.json").read_text(encoding="utf-8"))
        assert "~/.config/opencode/rules/*.md" in user_cfg.get("instructions", [])
        assert (fake_config / "rules" / "00-global.md").is_file()

        # Domain still active
        cfg = _read_opencode(pr)
        assert ".opencode/rules/ai_data-forge/*.md" in cfg["instructions"]

    def test_sync_creates_opencode_json_if_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given no opencode.json in project,
        When sync() is called,
        Then one is created with all entries."""
        vh = _make_vibe_home(tmp_path)
        pr = _make_project_root(tmp_path)
        # No opencode.json yet

        fake_home = tmp_path / "mock-home"
        fake_config = fake_home / ".config" / "opencode"
        fake_config.mkdir(parents=True, exist_ok=True)
        _touch(fake_config / "opencode.json", "{}")
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        activate_domain(vh, pr, "ai/data-forge")
        sync(vh, pr)

        assert _opencode_path(pr).is_file()
        cfg = _read_opencode(pr)
        assert ".opencode/rules/ai_data-forge/*.md" in cfg["instructions"]
