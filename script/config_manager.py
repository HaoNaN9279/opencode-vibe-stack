#!/usr/bin/env python3
"""
OpenCode Vibe Stack configuration manager.

Shared JSONC configuration helper used by install.sh / install.ps1.
Not meant to be run directly by users.

Usage:
  python config_manager.py add-instructions <config_path> <rules_glob>
  python config_manager.py add-skills-source <config_path> <skills_path>
  python config_manager.py add-agent-defs <config_path> <agents_path>
"""

import json
import sys
import os


# ---------------------------------------------------------------------------
# JSONC helpers
# ---------------------------------------------------------------------------

def strip_jsonc_comments(text: str) -> str:
    """Strip // style comments from a JSONC string so it can be parsed as JSON."""
    lines = []
    for line in text.split('\n'):
        in_str = False
        comment_start = -1
        i = 0
        while i < len(line):
            if not in_str and line[i] == '"':
                in_str = True
            elif in_str and line[i] == '\\':
                i += 1  # skip escaped char
            elif in_str and line[i] == '"':
                in_str = False
            elif not in_str and i + 1 < len(line) and line[i:i+2] == '//':
                comment_start = i
                break
            i += 1
        stripped = line[:comment_start] if comment_start >= 0 else line
        if stripped.strip():
            lines.append(stripped)
    return '\n'.join(lines)


def read_jsonc(path: str) -> dict:
    """Read a JSONC file, strip comments, return parsed dict."""
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        original = f.read()
    try:
        return json.loads(strip_jsonc_comments(original))
    except json.JSONDecodeError:
        return {}


def write_json(path: str, data: dict) -> None:
    """Write data as formatted JSON (no trailing commas, safe for JSONC tools)."""
    output = json.dumps(data, indent=2, ensure_ascii=False)
    with open(path, 'w') as f:
        f.write(output + '\n')


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_add_instructions(config_path: str, rules_glob: str) -> None:
    """Add rules_glob to the 'instructions' array in an opencode.json config."""
    data = read_jsonc(config_path)

    if '$schema' not in data:
        data['$schema'] = 'https://opencode.ai/config.json'

    if 'instructions' not in data:
        data['instructions'] = []

    if rules_glob not in data['instructions']:
        data['instructions'].append(rules_glob)
        print(f'    Added instructions: {rules_glob}')
    else:
        print(f'    instructions already has: {rules_glob}')

    write_json(config_path, data)


def cmd_add_skills_source(config_path: str, skills_path: str) -> None:
    """Add a skills.sources entry to oh-my-openagent.jsonc."""
    data = read_jsonc(config_path)

    if 'skills' not in data:
        data['skills'] = {}
    if 'sources' not in data['skills']:
        data['skills']['sources'] = []

    sources = data['skills']['sources']
    entry = {'path': skills_path, 'recursive': True}

    if not any(s.get('path') == skills_path for s in sources):
        sources.append(entry)
        print(f'    Added skills.sources entry: {skills_path}')
    else:
        print(f'    skills.sources already has: {skills_path}')

    write_json(config_path, data)


def cmd_add_agent_defs(config_path: str, agents_path: str) -> None:
    """Add an agent_definitions path entry to oh-my-openagent.jsonc."""
    data = read_jsonc(config_path)

    if 'agent_definitions' not in data:
        data['agent_definitions'] = []

    if agents_path not in data['agent_definitions']:
        data['agent_definitions'].append(agents_path)
        print(f'    Added agent_definitions: {agents_path}')
    else:
        print(f'    agent_definitions already has: {agents_path}')

    write_json(config_path, data)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python config_manager.py <subcommand> [args...]", file=sys.stderr)
        print("  add-instructions    <config_path> <rules_glob>", file=sys.stderr)
        print("  add-skills-source   <config_path> <skills_path>", file=sys.stderr)
        print("  add-agent-defs      <config_path> <agents_path>", file=sys.stderr)
        sys.exit(1)

    subcommand = sys.argv[1]

    if subcommand == 'add-instructions':
        if len(sys.argv) != 4:
            print("Usage: python config_manager.py add-instructions <config_path> <rules_glob>", file=sys.stderr)
            sys.exit(1)
        cmd_add_instructions(sys.argv[2], sys.argv[3])

    elif subcommand == 'add-skills-source':
        if len(sys.argv) != 4:
            print("Usage: python config_manager.py add-skills-source <config_path> <skills_path>", file=sys.stderr)
            sys.exit(1)
        cmd_add_skills_source(sys.argv[2], sys.argv[3])

    elif subcommand == 'add-agent-defs':
        if len(sys.argv) != 4:
            print("Usage: python config_manager.py add-agent-defs <config_path> <agents_path>", file=sys.stderr)
            sys.exit(1)
        cmd_add_agent_defs(sys.argv[2], sys.argv[3])

    else:
        print(f"Unknown subcommand: {subcommand}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
