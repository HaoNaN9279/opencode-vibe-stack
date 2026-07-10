"""Tests for JSONC (JSON with Comments) parsing utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vibe_stack.writer.jsonc_utils import parse_jsonc, strip_jsonc_comments


class TestStripJsoncComments:
    """Tests for the strip_jsonc_comments function."""

    # --- Line comments (//) ---

    def test_strips_line_comment_at_end_of_line(self) -> None:
        """// comment at end of line is stripped, preceding JSON kept."""
        result = strip_jsonc_comments('{ "a": 1 // comment\n}')
        assert json.loads(result) == {"a": 1}

    def test_strips_line_comment_whole_line(self) -> None:
        """A line that is entirely a // comment becomes empty."""
        result = strip_jsonc_comments("// this is a comment\n42")
        assert json.loads(result) == 42

    def test_strips_multiple_line_comments(self) -> None:
        """Multiple // comments on different lines are all stripped."""
        result = strip_jsonc_comments('{\n  "a": 1, // first\n  "b": 2 // second\n}')
        assert json.loads(result) == {"a": 1, "b": 2}

    def test_strips_multiple_line_comments_same_line(self) -> None:
        """Multiple // comments on the same line."""
        result = strip_jsonc_comments('{ "a": 1 // first\n, "b": 2 // second\n}')
        assert json.loads(result) == {"a": 1, "b": 2}

    # --- Block comments (/* */) ---

    def test_strips_block_comment_inline(self) -> None:
        """/* */ comment inside a line is stripped."""
        result = strip_jsonc_comments('{ "a": /* x */ 1 }')
        assert json.loads(result) == {"a": 1}

    def test_strips_block_comment_multiline(self) -> None:
        """/* */ comment spanning multiple lines is stripped."""
        result = strip_jsonc_comments('{ "a": /* multi\nline\ncomment */ 1 }')
        assert json.loads(result) == {"a": 1}

    def test_strips_block_comment_at_end_of_file(self) -> None:
        """Empty block comment at end of file is stripped."""
        result = strip_jsonc_comments('{ "a": 1 }/**/')
        assert json.loads(result) == {"a": 1}

    def test_strips_block_comment_only(self) -> None:
        """File with only a block comment becomes empty."""
        result = strip_jsonc_comments("/* nothing here */")
        assert result.strip() == ""

    # --- Mixed comments ---

    def test_mixed_comments(self) -> None:
        """Mixed // and /* */ comments in nested JSON."""
        result = strip_jsonc_comments(
            '{\n'
            '  "outer": { // outer comment\n'
            '    "inner": /* inner block */ 42\n'
            '  }\n'
            '}'
        )
        assert json.loads(result) == {"outer": {"inner": 42}}

    # --- Strings containing comment-like sequences ---

    def test_preserves_double_slash_inside_string(self) -> None:
        """// inside a string value (e.g., URL) is preserved."""
        result = strip_jsonc_comments('{ "url": "https://example.com/path" }')
        assert json.loads(result) == {"url": "https://example.com/path"}

    def test_preserves_block_comment_like_inside_string(self) -> None:
        """/* inside a string value is preserved."""
        result = strip_jsonc_comments('{ "pattern": "a /* b */ c" }')
        assert json.loads(result) == {"pattern": "a /* b */ c"}

    def test_handles_escaped_quotes_inside_string(self) -> None:
        """Escaped quotes inside strings are handled correctly."""
        result = strip_jsonc_comments(r'{ "key": "va\"lue" }')
        assert json.loads(result) == {"key": 'va"lue'}

    def test_handles_escaped_backslash_before_quote(self) -> None:
        """Escaped backslash followed by escaped quote: \\\" in JSON."""
        # JSON "a\\\"b" parses as: a + literal backslash + literal quote + b
        result = strip_jsonc_comments(r'{ "key": "a\\\"b" }')
        parsed = json.loads(result)
        assert parsed == {"key": 'a\\"b'}

    # --- Edge cases ---

    def test_empty_string_returns_empty(self) -> None:
        """Empty input returns empty string."""
        assert strip_jsonc_comments("") == ""

    def test_whitespace_only(self) -> None:
        """Whitespace-only input is returned as-is."""
        result = strip_jsonc_comments("  \n  \t  ")
        assert result == "  \n  \t  "

    def test_newline_at_end_of_line_comment_is_preserved(self) -> None:
        """The newline after a // comment is preserved for line counting."""
        result = strip_jsonc_comments('1\n// comment\n2')
        assert "2" in result

    # --- Windows line endings (CRLF) ---

    def test_handles_crlf_line_endings(self) -> None:
        """CRLF line endings are handled correctly."""
        result = strip_jsonc_comments('{\r\n  "a": 1 // comment\r\n}')
        assert json.loads(result) == {"a": 1}

    def test_crlf_with_block_comments(self) -> None:
        """CRLF with block comments."""
        result = strip_jsonc_comments('{\r\n  "a": /* block */ 1\r\n}')
        assert json.loads(result) == {"a": 1}

    # --- Preserves valid JSON types ---

    def test_preserves_numbers(self) -> None:
        """Numbers (int, float, negative, scientific) are preserved."""
        result = strip_jsonc_comments('[1, -2, 3.14, 1e10]')
        assert json.loads(result) == [1, -2, 3.14, 1e10]

    def test_preserves_booleans_and_null(self) -> None:
        """Booleans and null are preserved."""
        result = strip_jsonc_comments('{ "t": true, "f": false, "n": null }')
        assert json.loads(result) == {"t": True, "f": False, "n": None}

    def test_preserves_unicode(self) -> None:
        """Unicode characters are preserved."""
        result = strip_jsonc_comments('{ "greeting": "你好世界" }')
        assert json.loads(result) == {"greeting": "你好世界"}

    def test_handles_deeply_nested_json(self) -> None:
        """Deeply nested JSON is handled without recursion errors."""
        # Build a deeply nested object as a string
        inner = "42"
        for _ in range(100):
            inner = f'{{ "nested": {inner} }}'
        result = strip_jsonc_comments(inner)
        parsed = json.loads(result)
        # Verify depth
        d = parsed
        depth = 0
        while isinstance(d, dict) and "nested" in d:
            depth += 1
            d = d["nested"]
        assert depth == 100


class TestParseJsonc:
    """Tests for the parse_jsonc function using real files."""

    def test_parses_simple_jsonc_file(self, tmp_path: Path) -> None:
        """Basic JSONC file with line comments."""
        filepath = tmp_path / "config.jsonc"
        filepath.write_text('{\n  "name": "test", // app name\n  "port": 8080\n}\n')
        result = parse_jsonc(filepath)
        assert result == {"name": "test", "port": 8080}

    def test_parses_with_block_comments(self, tmp_path: Path) -> None:
        """JSONC file with block comments."""
        filepath = tmp_path / "config.jsonc"
        filepath.write_text('{\n  /* database config */\n  "host": "localhost",\n  "port": 5432\n}\n')
        result = parse_jsonc(filepath)
        assert result == {"host": "localhost", "port": 5432}

    def test_parses_empty_file(self, tmp_path: Path) -> None:
        """Empty file returns empty dict."""
        filepath = tmp_path / "empty.jsonc"
        filepath.write_text("")
        result = parse_jsonc(filepath)
        assert result == {}

    def test_parses_comments_only_file(self, tmp_path: Path) -> None:
        """File with only comments returns empty dict."""
        filepath = tmp_path / "comments.jsonc"
        filepath.write_text("// all comments\n/* and blocks */\n")
        result = parse_jsonc(filepath)
        assert result == {}

    def test_file_not_found_returns_empty_dict(self, tmp_path: Path) -> None:
        """Missing file returns empty dict instead of raising."""
        missing = tmp_path / "nonexistent.jsonc"
        result = parse_jsonc(missing)
        assert result == {}

    def test_fixes_trailing_comma_in_array(self, tmp_path: Path) -> None:
        """Trailing comma in array is fixed."""
        filepath = tmp_path / "config.jsonc"
        filepath.write_text("""{
  "items": [1, 2, 3,]
}""")
        result = parse_jsonc(filepath)
        assert result == {"items": [1, 2, 3]}

    def test_fixes_trailing_comma_in_object(self, tmp_path: Path) -> None:
        """Trailing comma before closing brace is fixed."""
        filepath = tmp_path / "config.jsonc"
        filepath.write_text("""{
  "a": 1,
  "b": 2,
}""")
        result = parse_jsonc(filepath)
        assert result == {"a": 1, "b": 2}

    def test_fixes_multiple_trailing_commas(self, tmp_path: Path) -> None:
        """Multiple trailing commas in nested structures."""
        filepath = tmp_path / "config.jsonc"
        filepath.write_text("""{
  "arr": [1, 2,],
  "obj": {"x": 1,},
}""")
        result = parse_jsonc(filepath)
        assert result == {"arr": [1, 2], "obj": {"x": 1}}

    def test_preserves_urls_with_comments(self, tmp_path: Path) -> None:
        """URLs containing // are preserved when comments are stripped."""
        filepath = tmp_path / "config.jsonc"
        filepath.write_text("""{
  // API endpoint
  "endpoint": "https://api.example.com/v1/"
}""")
        result = parse_jsonc(filepath)
        assert result == {"endpoint": "https://api.example.com/v1/"}

    def test_handles_mcp_registry_style_file(self, tmp_path: Path) -> None:
        """Simulates a real vibe-stack MCP registry JSONC file."""
        content = """{
  // MCP server registry version
  "version": 1,
  "mcp_registry": {
    /*
      Each entry maps a server name to its executable configuration.
      Edit the "command" field to point to the actual executable path.
    */
    "data-forge": {
      "command": "C:\\\\Program Files\\\\data-forge\\\\data-forge.exe",
      "args": ["--port", "8080"]
    },
    "blender-mcp": {
      "command": "/usr/local/bin/blender-mcp",  // macOS/Linux path
      "args": []
    }
  }
}"""
        filepath = tmp_path / "vibe-stack-mcp.jsonc"
        filepath.write_text(content)
        result = parse_jsonc(filepath)
        assert result["version"] == 1
        assert result["mcp_registry"]["data-forge"]["command"] == (
            "C:\\Program Files\\data-forge\\data-forge.exe"
        )
        assert result["mcp_registry"]["data-forge"]["args"] == ["--port", "8080"]
        assert result["mcp_registry"]["blender-mcp"]["command"] == "/usr/local/bin/blender-mcp"

    def test_handles_crlf_file(self, tmp_path: Path) -> None:
        """File with CRLF line endings."""
        filepath = tmp_path / "config.jsonc"
        filepath.write_text("{\r\n  \"a\": 1, // comment\r\n  \"b\": 2\r\n}\r\n")
        result = parse_jsonc(filepath)
        assert result == {"a": 1, "b": 2}

    def test_parses_complex_nested_structure(self, tmp_path: Path) -> None:
        """Complex nested JSONC with mixed comment types."""
        content = """{
  // Application settings
  "app": {
    "name": "VibeStack" /* display name */,
    "debug": false
  },
  /*
   * Database configuration
   * Modify as needed.
   */
  "database": {
    "host": "localhost",  // dev server
    "port": 5432,
    "credentials": { "user": "admin", "pass": "secret" }
  },
  "features": [
    "auto-sync",  // sync on save
    "live-reload"
  ]
}"""
        filepath = tmp_path / "config.jsonc"
        filepath.write_text(content)
        result = parse_jsonc(filepath)
        assert result["app"]["name"] == "VibeStack"
        assert result["app"]["debug"] is False
        assert result["database"]["host"] == "localhost"
        assert result["features"] == ["auto-sync", "live-reload"]

    def test_invalid_json_still_raises(self, tmp_path: Path) -> None:
        """Truly invalid JSON (not just comments) raises json.JSONDecodeError."""
        filepath = tmp_path / "bad.jsonc"
        filepath.write_text("{ invalid }")
        with pytest.raises(json.JSONDecodeError):
            parse_jsonc(filepath)
