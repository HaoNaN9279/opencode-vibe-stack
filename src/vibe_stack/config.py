"""JSON/JSONC configuration file operations for vibe-stack.

Pure Python — no awk, sed, or third-party JSONC libraries.
Provides reading JSONC (with comment stripping), writing JSON,
MCP block merging, and text-based array manipulation on JSON config files.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


# ── Internal helpers ──────────────────────────────────────────────

def _strip_jsonc_comments(text: str) -> str:
    """Strip ``//`` line comments and ``/* */`` block comments from JSONC
    text, while **preserving** them inside JSON strings.
    """
    result: list[str] = []
    i = 0
    n = len(text)
    in_string = False
    escape = False

    while i < n:
        ch = text[i]

        if escape:
            result.append(ch)
            escape = False
            i += 1
            continue

        if ch == "\\" and in_string:
            result.append(ch)
            escape = True
            i += 1
            continue

        if ch == '"':
            in_string = not in_string
            result.append(ch)
            i += 1
            continue

        if not in_string:
            # Line comment: // …
            if ch == "/" and i + 1 < n and text[i + 1] == "/":
                i += 2
                while i < n and text[i] != "\n":
                    i += 1
                continue

            # Block comment: /* … */
            if ch == "/" and i + 1 < n and text[i + 1] == "*":
                i += 2
                while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                    i += 1
                i += 2  # skip closing */
                continue

        result.append(ch)
        i += 1

    return "".join(result)


def _clean_jsonc(text: str) -> str:
    """Strip comments and fix trailing commas, returning valid JSON text."""
    text = _strip_jsonc_comments(text)
    text = fix_trailing_commas(text)
    return text


def _brace_count(line: str) -> int:
    """Return net brace change in *line* (``{`` adds 1, ``}`` subtracts 1)."""
    return line.count("{") - line.count("}")


def _bracket_count(line: str) -> int:
    """Return net bracket change in *line* (``[`` adds 1, ``]`` subtracts 1)."""
    return line.count("[") - line.count("]")


_RX_CLOSING_BRACKET = re.compile(r"^[\s]*\][\s]*,?[\s]*$")


def _is_array_close_line(line: str) -> bool:
    """Return ``True`` if *line* is a line that only contains ``]``
    (with optional whitespace and trailing comma)."""
    return bool(_RX_CLOSING_BRACKET.match(line))


# ── Public API: comment / trailing comma cleanup ──────────────────


def fix_trailing_commas(text: str) -> str:
    """Remove trailing commas appearing immediately before ``]`` or ``}``
    in JSON text, producing valid JSON.

    Handles both:
    * Inline cases: ``[1, ]`` → ``[1 ]``, ``{"a": 1, }`` → ``{"a": 1 }``
    * Cross-line cases where a comma-terminated line is followed by a
      closing-bracket line.

    Examples::

        >>> fix_trailing_commas('[1, 2,]')
        '[1, 2]'
        >>> fix_trailing_commas('{\\n  "a": 1,\\n}')
        '{\\n  "a": 1\\n}'
    """
    # Pass 1 — cross-line: comma at end of line N, bracket at start of N+1
    lines = text.splitlines(keepends=True)
    if len(lines) < 2:
        return _fix_inline_trailing_commas(text)

    result: list[str] = []
    for i, line in enumerate(lines):
        if i > 0:
            prev = result[-1]
            if prev.rstrip().endswith(",") and line.lstrip().startswith(("]", "}")):
                result[-1] = _strip_trailing_comma(prev)
        result.append(line)

    merged = "".join(result)
    return _fix_inline_trailing_commas(merged)


def _fix_inline_trailing_commas(text: str) -> str:
    """Remove trailing commas immediately before ``]`` or ``}`` on the same
    line or across lines (greedy)."""
    return re.sub(r",(\s*[\]}])", r"\1", text)


def _strip_trailing_comma(line: str) -> str:
    """Remove the last trailing comma (and whitespace after it) from *line*."""
    # Find last comma, then everything after it (whitespace + newline)
    idx = line.rfind(",")
    if idx == -1:
        return line
    before = line[:idx]
    after = line[idx + 1 :]
    # Keep only whitespace that is NOT part of the comma-removed suffix
    # i.e. keep the newline but strip spaces before it
    stripped_after = after.lstrip(" ")
    return before + stripped_after


# ── Public API: JSONC read / write ─────────────────────────────────


def read_jsonc_text(text: str) -> dict[str, Any]:
    """Parse JSONC text (which may contain comments) into a :class:`dict`.

    Comments (``//`` and ``/* */``) are stripped and trailing commas are
    fixed before parsing with :func:`json.loads`.

    Examples::

        >>> read_jsonc_text('{ "a": 1 /* block */, "b": 2 // line\\n}')
        {'a': 1, 'b': 2}
        >>> read_jsonc_text('{ "url": "https://example.com/path" }')
        {'url': 'https://example.com/path'}
    """
    cleaned = _clean_jsonc(text)
    return json.loads(cleaned)


def read_jsonc(path: Path) -> dict[str, Any]:
    """Read a JSONC file from *path*, strip comments, and return its
    contents as a :class:`dict`.

    Raises :class:`FileNotFoundError` if the file does not exist.
    """
    text = path.read_text(encoding="utf-8")
    return read_jsonc_text(text)


def write_jsonc(path: Path, data: dict[str, Any]) -> None:
    """Write *data* as formatted JSON to *path*.

    Uses :func:`json.dumps` with ``indent=2`` and a trailing newline.
    Creates parent directories if they do not exist.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, indent=2, ensure_ascii=False)
    path.write_text(content + "\n", encoding="utf-8")


# ── Public API: MCP block merge ───────────────────────────────────


def merge_mcp_block(
    config: dict[str, Any],
    new_entries: dict[str, Any],
    prefix: str = "vibe:",
) -> dict[str, Any]:
    """Merge *new_entries* into the ``mcp`` field of *config*.

    Entries in *config["mcp"]* whose key starts with *prefix* are
    **replaced**; all other (non-prefixed) entries are preserved.

    Returns the updated *config* dict (mutated in place).

    Examples::

        >>> cfg = {"mcp": {"user-srv": {"type": "remote"}}}
        >>> new = {"vibe:data-forge": {"type": "local", "command": ["df.exe"]}}
        >>> merge_mcp_block(cfg, new)
        {'mcp': {'user-srv': {'type': 'remote'}, 'vibe:data-forge': {'type': 'local', 'command': ['df.exe']}}}

        >>> cfg2 = {"mcp": {"vibe:old": {}, "custom": {}}}
        >>> merge_mcp_block(cfg2, {"vibe:new": {}})
        {'mcp': {'custom': {}, 'vibe:new': {}}}
    """
    if "mcp" not in config:
        config["mcp"] = {}

    mcp = config["mcp"]
    if not isinstance(mcp, dict):
        mcp = {}  # type: ignore[unreachable]

    # Remove all existing prefix entries
    filtered = {k: v for k, v in mcp.items() if not k.startswith(prefix)}
    # Add new entries
    filtered.update(new_entries)
    config["mcp"] = filtered
    return config


# ── Internal: text-based array manipulation primitives ────────────

# Decorator to ensure consistent return semantics
# All array ops return int: 0=success, 1=not-found, 2=already-exists (add only)


def _array_value_exists(text: str, value: str) -> bool:
    """Check whether *value* appears anywhere in *text* (literal match)."""
    return value in text


def _key_in_text(text: str, key: str) -> bool:
    """Check whether ``"<key>"`` appears in *text*."""
    return f'"{key}"' in text


# ── Public API: simple array add / remove ─────────────────────────


def array_add(file: Path, key: str, value: str) -> int:
    """Add *value* to a JSON array identified by *key* in *file*.

    Inserts the value just before the closing ``]`` of the first array
    found after the key line.  Automatically adds a trailing comma to
    the preceding array element when needed.  Trailing commas are fixed
    afterwards.

    Returns:
        | 0 — value was added
        | 1 — file does not exist or *key* was not found
        | 2 — *value* already exists in the file
    """
    if not file.is_file():
        return 1

    text = file.read_text(encoding="utf-8")

    if _array_value_exists(text, value):
        return 2

    if not _key_in_text(text, key):
        return 1

    lines = text.splitlines(keepends=True)
    result: list[str] = []
    in_key = False
    done = False
    prev_content: str | None = None
    prev_content_idx: int | None = None

    for i, line in enumerate(lines):
        if not done:
            if f'"{key}"' in line:
                in_key = True
            if in_key:
                stripped = line.strip()
                if stripped and not _is_array_close_line(line):
                    prev_content = line
                    prev_content_idx = len(result)
                if _is_array_close_line(line):
                    # Add comma to previous content line if it lacks one
                    insertion = f"{value}\n"
                    if prev_content is not None and prev_content_idx is not None:
                        if not prev_content.rstrip().endswith(","):
                            result[prev_content_idx] = _append_comma(prev_content)
                        # Insert value with comma
                        insertion = f"{value},\n"
                    result.append(insertion)
                    done = True
        result.append(line)

    new_text = "".join(result)
    new_text = fix_trailing_commas(new_text)
    file.write_text(new_text, encoding="utf-8")
    return 0


def _append_comma(line: str) -> str:
    """Append a comma to the last non-whitespace position of *line*,
    preserving the trailing whitespace/newline."""
    stripped = line.rstrip()
    suffix = line[len(stripped):]
    return stripped + "," + suffix


def array_remove(file: Path, key: str, value: str) -> int:
    """Remove *value* from a JSON array identified by *key* in *file*.

    Removes every line that contains *value*.  Trailing commas are fixed
    afterwards.

    Returns:
        | 0 — value was removed
        | 1 — file does not exist or *value* was not found
    """
    if not file.is_file():
        return 1

    text = file.read_text(encoding="utf-8")

    if not _array_value_exists(text, value):
        return 1

    if not _key_in_text(text, key):
        return 1

    lines = text.splitlines(keepends=True)
    result = [line for line in lines if value not in line]

    new_text = "".join(result)
    new_text = fix_trailing_commas(new_text)
    file.write_text(new_text, encoding="utf-8")
    return 0


# ── Public API: nested array add / remove ─────────────────────────


def nested_array_add(
    file: Path,
    parent_key: str,
    child_key: str,
    value: str,
) -> int:
    r"""Add *value* to a nested JSON array ``parent_key → child_key``.

    The JSON shape is expected to be::

        "parent_key": {
            …
            "child_key": [ … ],
            …
        }

    If ``child_key`` already exists the value is inserted just before the
    closing ``]`` of its array.  If ``child_key`` does **not** exist it is
    created at the end of the parent block.

    Returns:
        | 0 — value was added
        | 1 — file does not exist or *parent_key* was not found
        | 2 — *value* already exists in the child array
    """
    if not file.is_file():
        return 1

    text = file.read_text(encoding="utf-8")

    if not _key_in_text(text, parent_key):
        return 1

    if _array_value_exists(text, value):
        return 2

    lines = text.splitlines(keepends=True)
    result: list[str] = []
    state = 0  # 0=before-parent, 1=inside-parent, 2=inside-child-key
    depth = 0  # brace depth within parent block
    prev_depth = 0  # depth before processing current line
    has_child = False
    array_level = 0  # bracket depth state BEFORE processing current line
    inserted = False
    value_already_exists = False
    prev_content: str | None = None  # last content line inside child array
    prev_content_idx: int | None = None
    last_sibling: str | None = None  # last content line inside parent block
    last_sibling_idx: int | None = None

    for i, line in enumerate(lines):
        if not inserted and not value_already_exists:
            # ---- Track parent ----
            if state == 0 and f'"{parent_key}"' in line:
                state = 1
                depth = 0
                prev_depth = 0

            if state >= 1:
                prev_depth = depth
                depth += _brace_count(line)

                # Track sibling content in parent block (for comma insertion later)
                if state == 1:
                    stripped = line.strip()
                    if stripped and stripped not in ("{", "}"):
                        last_sibling = line
                        last_sibling_idx = len(result)

                # ---- Track child_key ----
                if state == 1 and f'"{child_key}"' in line:
                    state = 2
                    has_child = True

                if state == 2:
                    delta = _bracket_count(line)
                    was_in_array = array_level > 0
                    array_level += delta

                    if array_level > 0:
                        stripped = line.strip()
                        if stripped and value in line:
                            value_already_exists = True
                        if stripped and stripped not in ("[", "]"):
                            prev_content = line
                            prev_content_idx = len(result)

                    if not inserted and was_in_array and "]" in line:
                        if _is_array_close_line(line):
                            insertion = f"{value},\n"
                            if prev_content is not None and prev_content_idx is not None:
                                if not prev_content.rstrip().endswith(","):
                                    result[prev_content_idx] = _append_comma(prev_content)
                            result.append(insertion)
                            inserted = True
                        else:
                            if re.match(r".*\[[\s]*\]", line):
                                line = re.sub(r"\[([\s]*)\]", f"[{value}\\1]", line, count=1)
                            else:
                                line = line.replace("]", f", {value}]", 1)
                            inserted = True

                # ---- Parent block ended, child_key was missing ----
                if state == 1 and depth == 0 and not has_child:
                    if prev_depth > 0:
                        # Multi-line parent: insert child before closing brace
                        indent = "    "
                        m = re.match(r"^([\s]*)", line)
                        if m:
                            indent = m.group(1) + "  "
                        # Add comma to last sibling if needed
                        if last_sibling is not None and last_sibling_idx is not None:
                            if not last_sibling.rstrip().endswith(","):
                                result[last_sibling_idx] = _append_comma(last_sibling)
                        result.append(f'{indent}"{child_key}": [\n')
                        result.append(f"  {indent}{value}\n")
                        result.append(f"{indent}]\n")
                        inserted = True
                    elif "{" in line and "}" in line:
                        # Single-line parent: expand inline {} → multi-line block
                        indent_match = re.match(r"^([\s]*)", line)
                        parent_indent = indent_match.group(1) if indent_match else ""
                        child_indent = parent_indent + "  "
                        brace_pos = line.index("{")
                        before_brace = line[:brace_pos]
                        after_brace = line[brace_pos + 1 :].lstrip()
                        if after_brace.startswith("}"):
                            rest = after_brace[1:]
                            line = (
                                f'{before_brace}{{\n'
                                f'{child_indent}"{child_key}": [\n'
                                f'{child_indent}  {value}\n'
                                f'{child_indent}]\n'
                                f'{parent_indent}}}{rest}'
                            )
                            inserted = True

        result.append(line)

    if value_already_exists:
        return 2

    if not inserted:
        return 1

    new_text = "".join(result)
    new_text = fix_trailing_commas(new_text)
    file.write_text(new_text, encoding="utf-8")
    return 0


def nested_array_remove(
    file: Path,
    parent_key: str,
    child_key: str,
    value: str,
) -> int:
    r"""Remove *value* from a nested JSON array ``parent_key → child_key``.

    Removes every line containing *value* while in the child array
    context.  Trailing commas are fixed afterwards.

    Returns:
        | 0 — value was removed
        | 1 — file does not exist or *value* was not found
    """
    if not file.is_file():
        return 1

    text = file.read_text(encoding="utf-8")

    if not _key_in_text(text, parent_key):
        return 1

    if not _array_value_exists(text, value):
        return 1

    lines = text.splitlines(keepends=True)
    result: list[str] = []
    state = 0  # 0=before-parent, 1=inside-parent, 2=inside-child-key, 3=done
    depth = 0  # brace depth within parent block
    array_level = 0  # bracket depth within child array
    found = False

    for line in lines:
        if state < 3:
            # ---- Track parent ----
            if state == 0 and f'"{parent_key}"' in line:
                state = 1
                depth = 0

            if state >= 1:
                depth += _brace_count(line)

                # ---- Track child_key ----
                if state == 1 and f'"{child_key}"' in line:
                    state = 2
                    array_level = 0

                if state == 2:
                    array_level += _bracket_count(line)

                    # Only skip lines when we're inside the array (array_level>0)
                    if array_level > 0 and value in line:
                        found = True
                        continue  # skip this line

                    if array_level <= 0:
                        # We've left the child's array — but might still be
                        # inside the parent (e.g. more sibling keys).
                        # Revert to state 1 so we don't skip sibling entries.
                        state = 1

                # ---- Parent block ended ----
                if state == 1 and depth == 0:
                    state = 3

        result.append(line)

    if not found:
        return 1

    new_text = "".join(result)
    new_text = fix_trailing_commas(new_text)
    file.write_text(new_text, encoding="utf-8")
    return 0
