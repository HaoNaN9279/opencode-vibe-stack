"""JSONC (JSON with Comments) parsing utilities.

Provides functions to strip comments from JSONC text and parse JSONC files
into Python dictionaries. Handles // line comments, /* */ block comments,
trailing commas, and edge cases like comments appearing inside string values.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# Regex to remove trailing commas before closing brackets/braces.
# Matches a comma followed by optional whitespace and a ] or }.
_TRAILING_COMMA_RE = re.compile(r",\s*(\]|\})")


def strip_jsonc_comments(text: str) -> str:
    """Strip JSONC-style comments from text while preserving string contents.

    Uses a state machine to correctly handle // line comments and /* */
    block comments. Comments inside string values (e.g., URLs containing
    "//") are preserved. Escaped quotes inside strings are also handled.

    Args:
        text: The raw JSONC text with comments.

    Returns:
        The text with all comments removed, preserving JSON structure
        and string values intact.

    State machine states:
        NORMAL          — outside strings and comments
        IN_STRING       — inside a double-quoted string
        IN_LINE_COMMENT — inside a // comment (to end of line)
        IN_BLOCK_COMMENT— inside a /* */ comment (to closing */
    """
    result: list[str] = []
    i = 0
    n = len(text)
    state = "NORMAL"

    while i < n:
        ch = text[i]

        if state == "NORMAL":
            if ch == '"':
                result.append(ch)
                state = "IN_STRING"
            elif ch == "/" and i + 1 < n:
                next_ch = text[i + 1]
                if next_ch == "/":
                    state = "IN_LINE_COMMENT"
                    i += 1  # skip the second slash
                elif next_ch == "*":
                    state = "IN_BLOCK_COMMENT"
                    i += 1  # skip the asterisk
                else:
                    result.append(ch)
            else:
                result.append(ch)

        elif state == "IN_STRING":
            if ch == "\\" and i + 1 < n:
                # Escape sequence — keep the backslash and the escaped char
                result.append(ch)
                i += 1
                result.append(text[i])
            elif ch == '"':
                result.append(ch)
                state = "NORMAL"
            else:
                result.append(ch)

        elif state == "IN_LINE_COMMENT":
            if ch == "\n":
                result.append(ch)  # preserve newline for line numbering
                state = "NORMAL"
            # CR part of CRLF: skip \r, let next iteration handle \n
            # else: skip comment character

        elif state == "IN_BLOCK_COMMENT":
            if ch == "*" and i + 1 < n and text[i + 1] == "/":
                state = "NORMAL"
                i += 1  # skip the closing slash
            # else: skip comment character

        i += 1

    return "".join(result)


def parse_jsonc(path: Path) -> dict[object, object]:
    """Parse a JSONC configuration file into a Python dictionary.

    Reads the file, strips comments, fixes trailing commas, and parses
    the resulting JSON. Gracefully handles missing files and empty content.

    Args:
        path: Path to the .jsonc file.

    Returns:
        Parsed JSON content as a dictionary. Returns an empty dict for
        missing or empty files.

    Raises:
        json.JSONDecodeError: If the file contains invalid JSON after
            comment stripping.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}

    # Handle empty or comments-only files
    cleaned = strip_jsonc_comments(text)
    cleaned = cleaned.strip()
    if not cleaned:
        return {}

    # Fix trailing commas (valid in JSONC but not in standard JSON)
    cleaned = _TRAILING_COMMA_RE.sub(r"\1", cleaned)

    return json.loads(cleaned)
