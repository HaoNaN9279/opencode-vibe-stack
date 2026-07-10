"""Tests for CLI output formatters.

RED → GREEN: tests define expected output, then implementation matches.
"""

from __future__ import annotations

import json

import pytest

from vibe_stack.cli.formatter import (
    format_domain_info,
    format_domain_list,
    format_status,
    format_sync_result,
)
from vibe_stack.model.domain import DomainMeta


class TestFormatDomainList:
    """Tests for format_domain_list."""

    def test_empty_list(self) -> None:
        """Should return appropriate message for empty list."""
        result = format_domain_list([])
        assert "No domains" in result or result == ""

    def test_single_domain(self) -> None:
        """Should format a single domain correctly."""
        domains = [("ai/data-forge", "Data Forge", "Data transformation MCP server")]
        result = format_domain_list(domains)
        assert "AI" in result  # category header
        assert "data-forge" in result
        assert "Data Forge" in result
        assert "Data transformation" in result

    def test_multiple_categories(self) -> None:
        """Should group domains by category and sort."""
        domains = [
            ("dcc/blender", "Blender", "Blender 3D integration"),
            ("ai/data-forge", "Data Forge", "Data transformation MCP server"),
            ("dcc/maya", "Maya", "Autodesk Maya integration"),
        ]
        result = format_domain_list(domains)
        # Category headers
        assert "AI" in result
        assert "DCC" in result
        # Domain names
        assert "data-forge" in result
        assert "blender" in result
        assert "maya" in result

    def test_same_category_together(self) -> None:
        """Should group same-category domains under one header."""
        domains = [
            ("dcc/blender", "Blender", "Blender"),
            ("dcc/maya", "Maya", "Maya"),
            ("dcc/houdini", "Houdini", "Houdini"),
        ]
        result = format_domain_list(domains)
        assert result.count("DCC") == 1  # one header
        assert "blender" in result
        assert "maya" in result
        assert "houdini" in result

    def test_domain_key_as_name(self) -> None:
        """Should use domain key fragment (after '/') when name and description empty."""
        domains = [("dcc/blender", "", "")]
        result = format_domain_list(domains)
        assert "blender" in result

    # --- JSON output ---

    def test_json_output(self) -> None:
        """Should return valid JSON with expected structure."""
        domains = [("ai/data-forge", "Data Forge", "Data transformation MCP server")]
        result = format_domain_list(domains, json_output=True)
        data = json.loads(result)
        assert "domains" in data
        assert len(data["domains"]) == 1
        assert data["domains"][0]["key"] == "ai/data-forge"
        assert data["domains"][0]["name"] == "Data Forge"
        assert data["domains"][0]["description"] == "Data transformation MCP server"

    def test_json_empty(self) -> None:
        """JSON output with empty list should have empty domains array."""
        result = format_domain_list([], json_output=True)
        data = json.loads(result)
        assert data["domains"] == []


class TestFormatDomainInfo:
    """Tests for format_domain_info."""

    def test_basic_info(self) -> None:
        """Should format domain metadata."""
        meta = DomainMeta(
            name="blender",
            description="Blender 3D integration",
            version="1.0.0",
            tags=["dcc", "3d"],
        )
        result = format_domain_info(meta, "dcc/blender", "dcc_blender")
        assert "dcc/blender" in result
        assert "Blender" in result
        assert "Blender 3D integration" in result
        assert "1.0.0" in result
        assert "dcc, 3d" in result or "dcc_blender" in result

    def test_no_tags(self) -> None:
        """Should handle domain with no tags."""
        meta = DomainMeta(name="simple", description="Simple domain", version="0.1.0")
        result = format_domain_info(meta, "simple", "simple")
        assert "simple" in result
        assert "Simple domain" in result

    def test_with_dependencies(self) -> None:
        """Should show dependencies if present."""
        meta = DomainMeta(
            name="test",
            description="Domain with deps",
            version="1.0",
            dependencies=["ai/data-forge"],
        )
        result = format_domain_info(meta, "cat/test", "cat_test")
        assert "ai/data-forge" in result

    def test_json_output(self) -> None:
        """Should return valid JSON with metadata."""
        meta = DomainMeta(name="blender", description="Blender 3D", version="1.0.0", tags=["dcc"])
        result = format_domain_info(meta, "dcc/blender", "dcc_blender", json_output=True)
        data = json.loads(result)
        assert data["key"] == "dcc/blender"
        assert data["name"] == "blender"
        assert data["description"] == "Blender 3D"
        assert data["version"] == "1.0.0"
        assert data["tags"] == ["dcc"]
        assert data["namespace"] == "dcc_blender"
        assert data["dependencies"] == []

    def test_json_with_deps(self) -> None:
        """JSON output should include dependencies."""
        meta = DomainMeta(
            name="test", description="test", version="1.0", dependencies=["ai/data-forge"]
        )
        result = format_domain_info(meta, "x/y", "x_y", json_output=True)
        data = json.loads(result)
        assert data["dependencies"] == ["ai/data-forge"]


class TestFormatStatus:
    """Tests for format_status."""

    def test_no_active(self) -> None:
        """Should show no active domains message."""
        result = format_status([])
        assert "No active domains" in result

    def test_single_active(self) -> None:
        """Should list a single active domain."""
        result = format_status(["ai/data-forge"])
        assert "ai/data-forge" in result

    def test_multiple_active(self) -> None:
        """Should list all active domains."""
        result = format_status(["ai/data-forge", "dcc/blender", "dcc/maya"])
        assert "ai/data-forge" in result
        assert "dcc/blender" in result
        assert "dcc/maya" in result

    def test_json_output(self) -> None:
        """JSON output with active domains."""
        result = format_status(["ai/data-forge", "dcc/blender"], json_output=True)
        data = json.loads(result)
        assert "active_domains" in data
        assert data["active_domains"] == ["ai/data-forge", "dcc/blender"]

    def test_json_empty(self) -> None:
        """JSON output with no active domains."""
        result = format_status([], json_output=True)
        data = json.loads(result)
        assert data["active_domains"] == []


class TestFormatSyncResult:
    """Tests for format_sync_result."""

    def test_all_zero(self) -> None:
        """Should handle all-zero counts."""
        result = format_sync_result(0, 0, 0)
        assert "0" in result

    def test_positive_counts(self) -> None:
        """Should show all counts."""
        result = format_sync_result(2, 1, 3)
        assert "2" in result
        assert "1" in result
        assert "3" in result
        # Labels
        assert "created" in result.lower() or "Created" in result
        assert "updated" in result.lower() or "Updated" in result
        assert "deleted" in result.lower() or "Deleted" in result

    def test_large_numbers(self) -> None:
        """Should handle large counts."""
        result = format_sync_result(1000, 0, 50)
        assert "1000" in result
        assert "50" in result

    def test_json_output(self) -> None:
        """JSON output with counts."""
        result = format_sync_result(2, 1, 3, json_output=True)
        data = json.loads(result)
        assert data["created"] == 2
        assert data["updated"] == 1
        assert data["deleted"] == 3

    def test_json_all_zero(self) -> None:
        """JSON output with zero counts."""
        result = format_sync_result(0, 0, 0, json_output=True)
        data = json.loads(result)
        assert data["created"] == 0
        assert data["updated"] == 0
        assert data["deleted"] == 0
