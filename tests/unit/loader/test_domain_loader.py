"""Tests for the domain loader module: discover_domains() + load_domain().

TDD RED phase — all tests expect the functions to exist in
``vibe_stack.loader.domain_loader``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vibe_stack.errors import DomainNotFoundError, VibeStackError
from vibe_stack.loader.domain_loader import discover_domains, load_domain
from vibe_stack.model.domain import DomainConfig, DomainMeta


# ── file-system helpers (no mocks — real tmp_path) ──────────────────


def _make_domain_json(
    root: Path,
    name: str,
    description: str = "test domain",
    version: str = "1.0.0",
    tags: list[str] | None = None,
    dependencies: list[str] | None = None,
) -> Path:
    """Write a minimal ``domain.json`` into *root* and return its path."""
    data: dict[str, object] = {
        "name": name,
        "description": description,
        "version": version,
        "tags": tags or [],
        "dependencies": dependencies or [],
    }
    root.mkdir(parents=True, exist_ok=True)
    config_path = root / "domain.json"
    config_path.write_text(json.dumps(data), encoding="utf-8")
    return config_path


def _make_domain_in_vibe(
    vibe_home: Path,
    domain_key: str,
    name: str | None = None,
    description: str = "test domain",
    version: str = "1.0.0",
    tags: list[str] | None = None,
    dependencies: list[str] | None = None,
) -> Path:
    """Create a domain under ``vibe_home/domains/<domain_key>/``."""
    domain_root = vibe_home / "domains" / domain_key
    return _make_domain_json(
        domain_root,
        name=name or domain_key.rsplit("/", 1)[-1],
        description=description,
        version=version,
        tags=tags,
        dependencies=dependencies,
    )


def _touch(path: Path, content: str = "") -> Path:
    """Create a file (and its parent directories) at *path*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


# ── discover_domains ─────────────────────────────────────────────────


class TestDiscoverDomains:
    """Tests for :func:`discover_domains`."""

    # -- happy paths ---------------------------------------------------

    def test_finds_all_domain_json_recursively(self, tmp_path: Path) -> None:
        """Given a vibe_home with multiple domain.json files at various
        levels, When discover_domains is called, Then all of them are
        returned."""
        # Given
        vibe_home = tmp_path / "vibe"
        _make_domain_in_vibe(vibe_home, "dcc/blender", name="blender")
        _make_domain_in_vibe(vibe_home, "ai/data-forge", name="data-forge")
        _make_domain_in_vibe(vibe_home, "game-dev/unity", name="unity")

        # When
        results = discover_domains(vibe_home)

        # Then
        keys = [k for k, _meta, _root in results]
        assert len(results) == 3
        assert "ai/data-forge" in keys
        assert "dcc/blender" in keys
        assert "game-dev/unity" in keys

    def test_returns_sorted_deterministic_list(self, tmp_path: Path) -> None:
        """Given multiple domains, When discover_domains is called, Then
        results are sorted alphabetically by domain_key (as a deterministic
        contract, not an implementation assumption)."""
        # Given
        vibe_home = tmp_path / "vibe"
        _make_domain_in_vibe(vibe_home, "dcc/blender")
        _make_domain_in_vibe(vibe_home, "ai/data-forge")
        _make_domain_in_vibe(vibe_home, "game-dev/unity")

        # When
        results = discover_domains(vibe_home)

        # Then
        keys = [k for k, _meta, _root in results]
        assert keys == sorted(keys)

    def test_returns_empty_list_when_no_domain_json(self, tmp_path: Path) -> None:
        """Given a vibe_home with no domain.json files anywhere, When
        discover_domains is called, Then an empty list is returned."""
        # Given
        vibe_home = tmp_path / "vibe"
        (vibe_home / "domains").mkdir(parents=True)
        (vibe_home / "domains" / "empty-category").mkdir()

        # When
        results = discover_domains(vibe_home)

        # Then
        assert results == []

    def test_handles_deeply_nested_domains(self, tmp_path: Path) -> None:
        """Given a deeply nested domain (3+ levels), When
        discover_domains is called, Then the domain is found with the
        correct key."""
        # Given
        vibe_home = tmp_path / "vibe"
        _make_domain_in_vibe(vibe_home, "dcc/sub/deep/nested/domain")

        # When
        results = discover_domains(vibe_home)

        # Then
        assert len(results) == 1
        key, _meta, root = results[0]
        assert key == "dcc/sub/deep/nested/domain"
        assert root == vibe_home / "domains" / "dcc" / "sub" / "deep" / "nested" / "domain"

    def test_returns_correct_domain_meta(self, tmp_path: Path) -> None:
        """Given a domain.json with known metadata, When
        discover_domains returns it, Then the DomainMeta match the
        JSON content."""
        # Given
        vibe_home = tmp_path / "vibe"
        _make_domain_in_vibe(
            vibe_home,
            "dcc/blender",
            name="blender",
            description="Blender 3D",
            version="2.3.1",
            tags=["dcc", "3d"],
            dependencies=["ai/data-forge"],
        )

        # When
        results = discover_domains(vibe_home)

        # Then
        _key, meta, _root = results[0]
        assert meta.name == "blender"
        assert meta.description == "Blender 3D"
        assert meta.version == "2.3.1"
        assert meta.tags == ["dcc", "3d"]
        assert meta.dependencies == ["ai/data-forge"]

    # -- edge cases ----------------------------------------------------

    def test_skips_non_domain_json_files(self, tmp_path: Path) -> None:
        """Given a domains/ tree with other .json files that are NOT
        domain.json, When discover_domains is called, Then only the
        actual domain.json files are returned."""
        # Given
        vibe_home = tmp_path / "vibe"
        _make_domain_in_vibe(vibe_home, "dcc/blender")
        # Noise file — should be ignored.
        noise_file = vibe_home / "domains" / "dcc" / "not-a-domain.json"
        noise_file.parent.mkdir(parents=True, exist_ok=True)
        noise_file.write_text('{"not": "a domain"}', encoding="utf-8")

        # When
        results = discover_domains(vibe_home)

        # Then
        assert len(results) == 1
        assert results[0][0] == "dcc/blender"

    def test_domain_json_in_root_ignored(self, tmp_path: Path) -> None:
        """Given a domain.json directly inside domains/ (i.e. no
        subdirectory), When discover_domains is called, Then it is
        ignored (domains must live in a subdirectory)."""
        # Given
        vibe_home = tmp_path / "vibe"
        _make_domain_in_vibe(vibe_home, "dcc/blender")
        # Place a domain.json at domains/ level — not inside a named dir.
        (vibe_home / "domains" / "domain.json").write_text(
            json.dumps({"name": "orphan", "description": "bad", "version": "1.0"}),
            encoding="utf-8",
        )

        # When
        results = discover_domains(vibe_home)

        # Then
        assert len(results) == 1
        assert results[0][0] == "dcc/blender"

    def test_ignores_domain_json_outside_domains(self, tmp_path: Path) -> None:
        """Given a domain.json placed somewhere outside domains/,
        When discover_domains is called, Then it is ignored."""
        # Given
        vibe_home = tmp_path / "vibe"
        (vibe_home / "extra").mkdir(parents=True)
        (vibe_home / "extra" / "domain.json").write_text(
            json.dumps({"name": "outside", "description": "nope", "version": "1.0"}),
            encoding="utf-8",
        )

        # When
        results = discover_domains(vibe_home)

        # Then
        assert results == []

    def test_domain_key_uses_forward_slash_on_windows(self, tmp_path: Path) -> None:
        """Given a domain on Windows, When discover_domains computes
        the domain_key, Then it always uses forward slashes regardless
        of the OS path separator."""
        # Given
        vibe_home = tmp_path / "vibe"
        _make_domain_in_vibe(vibe_home, "dcc/blender")

        # When
        results = discover_domains(vibe_home)

        # Then
        key = results[0][0]
        assert "/" in key
        assert "\\" not in key


# ── load_domain ──────────────────────────────────────────────────────


class TestLoadDomain:
    """Tests for :func:`load_domain`."""

    # -- happy paths ---------------------------------------------------

    def test_returns_full_domain_config_with_correct_namespace(
        self, tmp_path: Path
    ) -> None:
        """Given an existing domain, When load_domain is called,
        Then the returned DomainConfig has the correct namespace."""
        # Given
        vibe_home = tmp_path / "vibe"
        _make_domain_in_vibe(vibe_home, "dcc/blender")

        # When
        config = load_domain(vibe_home, "dcc/blender")

        # Then
        assert isinstance(config, DomainConfig)
        assert config.namespace == "dcc_blender"
        assert config.domain_key == "dcc/blender"
        assert config.domain_root == vibe_home / "domains" / "dcc" / "blender"

    def test_scans_rules_directory(self, tmp_path: Path) -> None:
        """Given a domain with .md files in rules/, When load_domain
        is called, Then those files are in config.rules."""
        # Given
        vibe_home = tmp_path / "vibe"
        key = "dcc/blender"
        root = vibe_home / "domains" / key
        _make_domain_json(root, name="blender")
        r1 = _touch(root / "rules" / "01-style.md")
        r2 = _touch(root / "rules" / "02-security.md")
        # Non-.md files should be excluded.
        _touch(root / "rules" / ".gitkeep", "")
        _touch(root / "rules" / "notes.txt")

        # When
        config = load_domain(vibe_home, key)

        # Then
        rule_names = {p.name for p in config.rules}
        assert rule_names == {"01-style.md", "02-security.md"}

    def test_scans_agents_directory(self, tmp_path: Path) -> None:
        """Given a domain with .md files in agents/, When load_domain
        is called, Then those files are in config.agents."""
        # Given
        vibe_home = tmp_path / "vibe"
        key = "dcc/blender"
        root = vibe_home / "domains" / key
        _make_domain_json(root, name="blender")
        _touch(root / "agents" / "render-agent.md")

        # When
        config = load_domain(vibe_home, key)

        # Then
        assert len(config.agents) == 1
        assert config.agents[0].name == "render-agent.md"

    def test_scans_commands_directory(self, tmp_path: Path) -> None:
        """Given a domain with .md files in commands/, When load_domain
        is called, Then those files are in config.commands."""
        # Given
        vibe_home = tmp_path / "vibe"
        key = "dcc/blender"
        root = vibe_home / "domains" / key
        _make_domain_json(root, name="blender")
        _touch(root / "commands" / "render.md")

        # When
        config = load_domain(vibe_home, key)

        # Then
        assert len(config.commands) == 1
        assert config.commands[0].name == "render.md"

    def test_scans_mcp_directory_json_files_and_subdirs(
        self, tmp_path: Path
    ) -> None:
        """Given a domain with .json files AND subdirectories in mcp/,
        When load_domain is called, Then .json files go into
        config.mcp_files and subdirectories go into config.mcp_dirs."""
        # Given
        vibe_home = tmp_path / "vibe"
        key = "dcc/blender"
        root = vibe_home / "domains" / key
        _make_domain_json(root, name="blender")
        mcp_dir = root / "mcp"
        _touch(mcp_dir / "server.json")
        _touch(mcp_dir / "tool.json")
        # Subdirectories (MCP executable dirs).
        (mcp_dir / "my-server").mkdir(parents=True)
        (mcp_dir / "another-server").mkdir(parents=True)
        # Non-.json files in mcp/ root should be ignored for mcp_files.
        _touch(mcp_dir / "README.md")

        # When
        config = load_domain(vibe_home, key)

        # Then
        mcp_file_names = {p.name for p in config.mcp_files}
        assert mcp_file_names == {"server.json", "tool.json"}
        mcp_dir_names = {p.name for p in config.mcp_dirs}
        assert mcp_dir_names == {"my-server", "another-server"}

    def test_scans_skills_directory_skil_md_subdirs(
        self, tmp_path: Path
    ) -> None:
        """Given a domain with subdirectories containing SKILL.md in
        skills/, When load_domain is called, Then those subdirs are in
        config.skills."""
        # Given
        vibe_home = tmp_path / "vibe"
        key = "dcc/blender"
        root = vibe_home / "domains" / key
        _make_domain_json(root, name="blender")
        skill_a = root / "skills" / "render-skill"
        _touch(skill_a / "SKILL.md")
        skill_b = root / "skills" / "animate-skill"
        _touch(skill_b / "SKILL.md")
        # Subdir without SKILL.md should be excluded.
        (root / "skills" / "not-a-skill").mkdir(parents=True)
        # Files directly in skills/ should be excluded.
        _touch(root / "skills" / "orphan.md")

        # When
        config = load_domain(vibe_home, key)

        # Then
        skill_names = {p.name for p in config.skills}
        assert skill_names == {"render-skill", "animate-skill"}

    def test_returns_empty_lists_for_missing_optional_directories(
        self, tmp_path: Path
    ) -> None:
        """Given a domain with NONE of the optional subdirectories,
        When load_domain is called, Then every list field is empty."""
        # Given
        vibe_home = tmp_path / "vibe"
        key = "dcc/minimal"
        root = vibe_home / "domains" / key
        _make_domain_json(root, name="minimal")

        # When
        config = load_domain(vibe_home, key)

        # Then
        assert config.rules == []
        assert config.agents == []
        assert config.commands == []
        assert config.mcp_files == []
        assert config.mcp_dirs == []
        assert config.skills == []

    # -- error paths ---------------------------------------------------

    def test_raises_domain_not_found_for_nonexistent_domain(
        self, tmp_path: Path
    ) -> None:
        """Given a domain_key that does not exist, When load_domain is
        called, Then DomainNotFoundError is raised."""
        # Given
        vibe_home = tmp_path / "vibe"
        (vibe_home / "domains").mkdir(parents=True)

        # When / Then
        with pytest.raises(DomainNotFoundError):
            load_domain(vibe_home, "ghost/nonexistent")

    def test_domain_json_missing_required_fields_raises_vibe_stack_error(
        self, tmp_path: Path
    ) -> None:
        """Given a domain.json that lacks a required field (e.g. name),
        When load_domain is called, Then VibeStackError is raised."""
        # Given
        vibe_home = tmp_path / "vibe"
        root = vibe_home / "domains" / "bad-domain"
        root.mkdir(parents=True)
        (root / "domain.json").write_text(
            json.dumps({"description": "no name field", "version": "1.0"}),
            encoding="utf-8",
        )

        # When / Then
        with pytest.raises(VibeStackError):
            load_domain(vibe_home, "bad-domain")

    # -- namespace variants --------------------------------------------

    def test_namespace_computed_dcc_blender(self, tmp_path: Path) -> None:
        """domain_key='dcc/blender' → namespace='dcc_blender'."""
        vibe_home = tmp_path / "vibe"
        _make_domain_in_vibe(vibe_home, "dcc/blender")
        config = load_domain(vibe_home, "dcc/blender")
        assert config.namespace == "dcc_blender"

    def test_namespace_computed_dcc_sub_deep(self, tmp_path: Path) -> None:
        """domain_key='dcc/sub/deep' → namespace='dcc_sub_deep'."""
        vibe_home = tmp_path / "vibe"
        _make_domain_in_vibe(vibe_home, "dcc/sub/deep")
        config = load_domain(vibe_home, "dcc/sub/deep")
        assert config.namespace == "dcc_sub_deep"

    def test_namespace_computed_simple(self, tmp_path: Path) -> None:
        """domain_key='simple' → namespace='simple'."""
        vibe_home = tmp_path / "vibe"
        name = "simple"
        root = vibe_home / "domains" / name
        root.mkdir(parents=True)
        _make_domain_json(root, name=name)
        config = load_domain(vibe_home, name)
        assert config.namespace == "simple"
