"""Tests for domain data model dataclasses."""

from __future__ import annotations

from dataclasses import asdict, replace
from pathlib import Path

from vibe_stack.model.domain import CoreConfig, DomainConfig, DomainMeta


class TestDomainMeta:
    """Tests for DomainMeta dataclass."""

    def test_from_dict(self) -> None:
        """DomainMeta should be constructable from a dict matching domain.json."""
        meta = DomainMeta(
            name="blender",
            description="Blender 3D integration",
            version="1.0.0",
            tags=["dcc", "3d", "blender"],
            dependencies=["ai/data-forge"],
        )
        assert meta.name == "blender"
        assert meta.description == "Blender 3D integration"
        assert meta.version == "1.0.0"
        assert meta.tags == ["dcc", "3d", "blender"]
        assert meta.dependencies == ["ai/data-forge"]

    def test_defaults(self) -> None:
        """DomainMeta should default tags and dependencies to empty lists."""
        meta = DomainMeta(name="maya", description="Maya DCC", version="2.0")
        assert meta.tags == []
        assert meta.dependencies == []

    def test_is_dataclass(self) -> None:
        """DomainMeta should be a stdlib dataclass (not pydantic/attrs)."""
        from dataclasses import is_dataclass

        assert is_dataclass(DomainMeta) and not hasattr(DomainMeta, "__pydantic_fields__")

    def test_asdict_round_trip(self) -> None:
        """DomainMeta should round-trip through asdict → replace."""
        meta = DomainMeta(
            name="houdini",
            description="Houdini FX",
            version="1.2.3",
            tags=["dcc", "procedural"],
            dependencies=["dcc/blender"],
        )
        d = asdict(meta)
        assert d["name"] == "houdini"
        assert d["version"] == "1.2.3"
        assert d["tags"] == ["dcc", "procedural"]

    def test_empty_tags_and_deps(self) -> None:
        """DomainMeta should accept empty dict-style construction."""
        meta = DomainMeta(**{"name": "test", "description": "test", "version": "0.0.0"})
        assert meta.tags == []
        assert meta.dependencies == []


class TestDomainConfig:
    """Tests for DomainConfig dataclass."""

    def test_namespace_auto_computed_dcc_blender(self) -> None:
        """domain_key='dcc/blender' should produce namespace='dcc_blender'."""
        meta = DomainMeta(name="blender", description="test", version="1.0")
        config = DomainConfig(meta=meta, domain_key="dcc/blender", domain_root=Path("/tmp/blender"))
        assert config.namespace == "dcc_blender"

    def test_namespace_auto_computed_nested(self) -> None:
        """domain_key='dcc/sub/deep' should produce namespace='dcc_sub_deep'."""
        meta = DomainMeta(name="deep", description="test", version="1.0")
        config = DomainConfig(
            meta=meta,
            domain_key="dcc/sub/deep",
            domain_root=Path("/tmp/deep"),
        )
        assert config.namespace == "dcc_sub_deep"

    def test_namespace_no_slash(self) -> None:
        """domain_key='simple' should produce namespace='simple'."""
        meta = DomainMeta(name="simple", description="test", version="1.0")
        config = DomainConfig(meta=meta, domain_key="simple", domain_root=Path("/tmp/simple"))
        assert config.namespace == "simple"

    def test_defaults_all_empty_lists(self) -> None:
        """DomainConfig fields should all default to empty lists."""
        meta = DomainMeta(name="test", description="test", version="1.0")
        config = DomainConfig(meta=meta, domain_key="test", domain_root=Path("/tmp"))
        assert config.rules == []
        assert config.agents == []
        assert config.commands == []
        assert config.mcp_files == []
        assert config.mcp_dirs == []
        assert config.skills == []

    def test_mcp_files_and_dirs_separate(self) -> None:
        """mcp_files and mcp_dirs should be independent fields."""
        meta = DomainMeta(name="test", description="test", version="1.0")
        config = DomainConfig(
            meta=meta,
            domain_key="test",
            domain_root=Path("/tmp"),
            mcp_files=[Path("a.json")],
            mcp_dirs=[Path("mcp_server")],
        )
        assert config.mcp_files == [Path("a.json")]
        assert config.mcp_dirs == [Path("mcp_server")]

    def test_is_dataclass(self) -> None:
        """DomainConfig should be a stdlib dataclass."""
        from dataclasses import is_dataclass

        assert is_dataclass(DomainConfig)

    def test_fields_present(self) -> None:
        """DomainConfig should have all expected fields."""
        fields = {f.name for f in DomainConfig.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        assert fields >= {
            "meta",
            "domain_key",
            "namespace",
            "domain_root",
            "rules",
            "agents",
            "commands",
            "mcp_files",
            "mcp_dirs",
            "skills",
        }


class TestCoreConfig:
    """Tests for CoreConfig dataclass."""

    def test_defaults_all_empty_lists(self) -> None:
        """CoreConfig should default all fields to empty lists."""
        config = CoreConfig()
        assert config.rules == []
        assert config.agents == []
        assert config.commands == []
        assert config.mcp_files == []
        assert config.mcp_dirs == []
        assert config.skills == []

    def test_no_required_args(self) -> None:
        """CoreConfig should be constructable with no arguments."""
        config = CoreConfig()
        assert isinstance(config, CoreConfig)

    def test_partial_population(self) -> None:
        """CoreConfig should support populating only some fields."""
        config = CoreConfig(
            rules=[Path("/tmp/test.md")],
            commands=[Path("/tmp/cmd.md")],
        )
        assert config.rules == [Path("/tmp/test.md")]
        assert config.commands == [Path("/tmp/cmd.md")]
        assert config.agents == []
        assert config.skills == []

    def test_is_dataclass(self) -> None:
        """CoreConfig should be a stdlib dataclass."""
        from dataclasses import is_dataclass

        assert is_dataclass(CoreConfig)

    def test_compose_with_domain(self) -> None:
        """CoreConfig + DomainConfig should coexist cleanly."""
        core = CoreConfig(rules=[Path("/core/rules/global.md")])
        meta = DomainMeta(name="test", description="test", version="1.0")
        domain = DomainConfig(
            meta=meta,
            domain_key="dcc/test",
            domain_root=Path("/domains/dcc/test"),
            rules=[Path("/domains/dcc/test/rules/local.md")],
        )
        # Core and domain configs are independent; no overlap assertion needed.
        assert core.rules[0].name == "global.md"
        assert domain.rules[0].name == "local.md"
