#!/usr/bin/env bash
# install.sh - Vibe Stack installer (thin Python wrapper)
# Usage: ./install.sh
# Env: VIBE_STACK_HOME    Override install directory (default: script dir)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VIBE_STACK_HOME="${VIBE_STACK_HOME:-$SCRIPT_DIR}"

# Validate repo
if [ ! -f "$VIBE_STACK_HOME/core/rules/00-global.md" ] || [ ! -d "$VIBE_STACK_HOME/domains" ]; then
    echo "[ERROR] Invalid vibe-stack repo: $VIBE_STACK_HOME" >&2
    exit 1
fi

# Check uv
if ! command -v uv &>/dev/null; then
    echo "[ERROR] uv not found. Install: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
fi

cd "$VIBE_STACK_HOME"
uv sync
uv run python -m vibe_stack.install
