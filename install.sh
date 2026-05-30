#!/usr/bin/env bash
# ============================================================================
# install.sh - OpenCode Vibe Stack One-Click Deploy (Linux / macOS)
#
# Deploys the opencode-vibe-stack configuration management system.
# Creates core symlinks in ~/.config/opencode/ and installs the CLI tool.
#
# Usage:
#   ./install.sh
#
# VIBE_STACK_HOME is auto-detected as the directory containing this script
# (i.e. the repo root). Override with:
#   VIBE_STACK_HOME=/custom/path ./install.sh
#
# Environment:
#   VIBE_STACK_HOME     Override install directory (default: script directory)
# ============================================================================
set -euo pipefail

# ---- Colors (safe for non-TTY) ----
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    NC='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; CYAN=''; BOLD=''; NC=''
fi

# ---- Banner ----
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     OpenCode Vibe Stack - One-Click Installer       ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# ---- Determine VIBE_STACK_HOME ----
# Default to the directory containing this script (the repo root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
VIBE_STACK_HOME="${VIBE_STACK_HOME:-$SCRIPT_DIR}"

# Verify we're in the repo
if [ ! -f "$VIBE_STACK_HOME/core/rules/00-global.md" ] || [ ! -d "$VIBE_STACK_HOME/domains" ]; then
    echo -e "${RED}[✗]${NC} VIBE_STACK_HOME does not appear to be a valid vibe-stack repo: $VIBE_STACK_HOME"
    echo "       Run this script from within the opencode-vibe-stack repository."
    exit 1
fi

echo -e "${GREEN}[✓]${NC} Repo root: ${BOLD}$VIBE_STACK_HOME${NC}"
echo ""

# ---- Create Core Symlinks ----
echo -e "${BOLD}[1/4] Creating core symlinks...${NC}"

OPENCODE_CONFIG="$HOME/.config/opencode"
mkdir -p "$OPENCODE_CONFIG"

SYMLINK_TYPES=("rules" "agents" "commands" "skills" "mcp")

for type in "${SYMLINK_TYPES[@]}"; do
    src_dir="$VIBE_STACK_HOME/core/$type"
    dest_dir="$OPENCODE_CONFIG/$type"

    # Check if source exists
    if [ ! -d "$src_dir" ]; then
        echo -e "  ${YELLOW}[skip]${NC} $type/ - source not found (empty core dir - ok)"
        continue
    fi

    # Check if already correctly linked
    if [ -L "$dest_dir" ]; then
        current_target="$(readlink "$dest_dir")"
        if [ "$current_target" = "$src_dir" ]; then
            echo -e "  ${GREEN}[OK]${NC} $type/ -> already linked"
            continue
        fi
    fi

    # Remove existing (file, dir, or wrong symlink)
    if [ -e "$dest_dir" ] || [ -L "$dest_dir" ]; then
        echo -e "  ${YELLOW}[!]${NC} Removing existing $type/ ..."
        rm -rf "$dest_dir"
    fi

    # Create symlink
    ln -sf "$src_dir" "$dest_dir"
    echo -e "  ${GREEN}[OK]${NC} $type/ -> $src_dir"
done

echo ""

# ---- Update configuration files ----
echo -e "${BOLD}[2/4] Updating configuration files...${NC}"

OPENCODE_JSON="$OPENCODE_CONFIG/opencode.json"
RULES_GLOB="rules/*.md"

# ---- JSONC Config Helpers (pure bash, no python required) ----

# Append a value to a JSON array before its closing bracket.
# Usage: _jsonc_array_add <file> <key> <value_line>
# Returns 0 if added, 1 if already present.
_jsonc_array_add() {
    local file="$1" key="$2" val="$3"
    local tmp="${file}.tmp" in_key=false done=false

    [ ! -f "$file" ] && return 1

    while IFS= read -r line || [ -n "$line" ]; do
        if ! $done; then
            if echo "$line" | grep -q "\"$key\""; then
                in_key=true
            fi
            if $in_key && echo "$line" | grep -qE '^[[:space:]]*\][[:space:]]*,?[[:space:]]*$'; then
                echo "$val" >> "$tmp"
                done=true
            fi
        fi
        echo "$line" >> "$tmp"
    done < "$file"

    mv "$tmp" "$file"
    return 0
}

# 2a. Update opencode.json with core rules as instructions
if [ ! -f "$OPENCODE_JSON" ]; then
    printf '{\n  "$schema": "https://opencode.ai/config.json",\n  "instructions": [\n    "%s"\n  ]\n}\n' "$RULES_GLOB" > "$OPENCODE_JSON"
    echo -e "  ${GREEN}[OK]${NC} Created $OPENCODE_JSON with instructions: $RULES_GLOB"
elif ! grep -qF "\"$RULES_GLOB\"" "$OPENCODE_JSON"; then
    if _jsonc_array_add "$OPENCODE_JSON" "instructions" "    \"$RULES_GLOB\""; then
        echo -e "  ${GREEN}[OK]${NC} Added instructions: $RULES_GLOB"
    else
        echo -e "  ${YELLOW}[!]${NC} Could not auto-update $OPENCODE_JSON — please add \"$RULES_GLOB\" to the instructions array manually"
    fi
else
    echo -e "  ${GREEN}[OK]${NC} instructions already has: $RULES_GLOB"
fi

echo ""

# ---- Install MCP Binaries ----
#
# Scans domains/*/mcp/*.json for MCP configs with "release" metadata,
# and downloads the pre-built binary from GitHub Releases.
# Configs without "release" are skipped (binary expected to be already present).
install_mcp_binaries() {
    local vibe_home="$1"

    local plat_key
    case "$(uname -s)" in
        Linux)  plat_key="linux" ;;
        Darwin) plat_key="darwin" ;;
        *)      plat_key="linux" ;;
    esac

    echo ""
    local found_any=false

    for json_file in $(find "$vibe_home/domains" -path "*/mcp/*.json" ! -name "README.md" 2>/dev/null | sort); do
        [ ! -f "$json_file" ] && continue

        # Skip files without release metadata
        grep -q '"release"' "$json_file" 2>/dev/null || continue

        # Strip // comments from JSONC
        local content
        content=$(sed 's/[[:space:]]*\/\/.*$//' "$json_file")

        # Extract MCP servers with release metadata (tab-separated: name \t cmd \t repo \t asset)
        echo "$content" | awk -v plat="$plat_key" -v home="$vibe_home" '
        BEGIN { OFS="\t"; srv=""; cmd=""; repo=""; asset=""; in_release=0; in_cmd=0 }

        { gsub(/^[[:space:]]+/, ""); gsub(/,[[:space:]]*$/, "") }

        # Server entry: "name": {
        /^"[^"]+"[[:space:]]*:[[:space:]]*\{$/ {
            flush()
            srv = $0; gsub(/[[:space:]]*:.*/, "", srv); gsub(/"/, "", srv)
            cmd = ""; repo = ""; asset = ""; in_release = 0; in_cmd = 0
            next
        }

        # Command array on single line: "command": ["path"]
        /"command"/ {
            in_cmd = 1
            if (match($0, /\[[[:space:]]*"([^"]+)"/)) {
                cmd = substr($0, RSTART+1, RLENGTH-1)
                gsub(/^\[[[:space:]]*"/, "", cmd); gsub(/"[[:space:]]*\]?.*$/, "", cmd)
                gsub(/\$\{VIBE_STACK_HOME\}/, home, cmd)
                in_cmd = 0
            }
            next
        }

        # Multi-line command array: "path" on next line
        in_cmd && /^[[:space:]]*"/ {
            gsub(/^[[:space:]]*"/, ""); gsub(/".*/, "")
            cmd = $0
            gsub(/\$\{VIBE_STACK_HOME\}/, home, cmd)
            in_cmd = 0
        }

        in_cmd && /\]/ { in_cmd = 0 }

        # Release block
        /"release"/ { in_release = 1 }

        # Repo inside release
        in_release && /"repo"/ {
            gsub(/.*"repo"[[:space:]]*:[[:space:]]*"/, "")
            gsub(/".*/, "")
            repo = $0
        }

        # Platform asset inside release
        in_release && repo != "" {
            re = "\"" plat "\""
            if (index($0, re) > 0) {
                gsub(/.*"'"$plat_key"'"[[:space:]]*:[[:space:]]*"/, "")
                gsub(/".*/, "")
                asset = $0
            }
        }

        # End of blocks
        /^\}[[:space:]]*,?[[:space:]]*$/ {
            if (in_release) { in_release = 0 }
            else { flush(); srv = "" }
        }

        function flush() {
            if (srv && cmd && repo && asset)
                print srv, cmd, repo, asset
        }

        END { flush() }
        ' | while IFS=$'\t' read -r srv cmd repo asset; do
            [ -z "$srv" ] && continue
            found_any=true

            if [ -f "$cmd" ]; then
                echo "  ✅ $srv — binary already installed at $cmd"
                continue
            fi

            local url="https://github.com/$repo/releases/latest/download/$asset"
            echo "  ⬇  $srv: downloading $asset …"
            mkdir -p "$(dirname "$cmd")" 2>/dev/null

            if command -v curl &>/dev/null; then
                if curl -fsSL -o "$cmd" "$url" 2>/dev/null; then
                    chmod +x "$cmd" 2>/dev/null
                    echo "    ✅ $asset installed → $cmd"
                else
                    echo "    ⚠  Download failed: $url"
                    rm -f "$cmd" 2>/dev/null
                fi
            elif command -v wget &>/dev/null; then
                if wget -q -O "$cmd" "$url" 2>/dev/null; then
                    chmod +x "$cmd" 2>/dev/null
                    echo "    ✅ $asset installed → $cmd"
                else
                    echo "    ⚠  Download failed: $url"
                    rm -f "$cmd" 2>/dev/null
                fi
            else
                echo "    ⚠  No curl or wget found — cannot download: $url"
            fi
        done
    done

    if ! $found_any; then
        echo "  ℹ  No MCP binaries to download (all already installed or no release metadata)."
    fi
    echo ""
}

echo -e "${BOLD}[3/4] Installing MCP binaries...${NC}"
install_mcp_binaries "$VIBE_STACK_HOME"

# ---- Install CLI Tool ----
echo -e "${BOLD}[4/4] Installing CLI tool...${NC}"

# Determine bin directory (prefer ~/.local/bin, fall back to ~/bin)
if [ -d "$HOME/.local/bin" ] || mkdir -p "$HOME/.local/bin" 2>/dev/null; then
    BIN_DIR="$HOME/.local/bin"
elif [ -d "$HOME/bin" ] || mkdir -p "$HOME/bin" 2>/dev/null; then
    BIN_DIR="$HOME/bin"
else
    echo -e "  ${RED}[✗]${NC} Could not find/create a bin directory in HOME"
    echo "       Manually add bin/vibe-stack to your PATH"
    BIN_DIR=""
fi

if [ -n "$BIN_DIR" ]; then
    CLI_SRC="$VIBE_STACK_HOME/bin/vibe-stack"
    CLI_DEST="$BIN_DIR/vibe-stack"

    if [ ! -f "$CLI_SRC" ]; then
        echo -e "  ${YELLOW}[warn]${NC} CLI script not found at $CLI_SRC"
        echo "       Make sure you have the latest version of opencode-vibe-stack."
    else
        # Make executable
        chmod +x "$CLI_SRC"

        # Create symlink
        if [ -L "$CLI_DEST" ]; then
            rm -f "$CLI_DEST"
        fi
        ln -sf "$CLI_SRC" "$CLI_DEST"
        echo -e "  ${GREEN}[OK]${NC} CLI installed: $CLI_DEST -> $CLI_SRC"

        # Check if BIN_DIR is in PATH
        if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
            echo ""
            echo -e "  ${YELLOW}[!]${NC} ${BOLD}$BIN_DIR${NC} is not in your PATH."
            echo "       Add this to your shell config (~/.bashrc, ~/.zshrc, etc.):"
            echo -e "       ${CYAN}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
        fi
    fi
fi

echo ""

# ---- Success ----
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          ✓ Installation Complete!                   ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}Next Steps:${NC}"
echo ""
echo -e "  1. Verify installation:"
echo -e "     ${CYAN}vibe-stack list${NC}"
echo ""
echo -e "  2. Activate domains in a project:"
echo -e "     ${CYAN}cd your-project/${NC}"
echo -e "     ${CYAN}vibe-stack activate game-dev/unity${NC}"
echo ""
echo -e "  3. Check active domains:"
echo -e "     ${CYAN}vibe-stack status${NC}"
echo ""
echo -e "  4. Update the stack later:"
echo -e "     ${CYAN}cd $VIBE_STACK_HOME && git pull${NC}"
echo -e "     ${CYAN}vibe-stack core-update${NC}"
echo ""
echo -e "  ${BOLD}Location:${NC}    $VIBE_STACK_HOME"
echo -e "  ${BOLD}CLI Tool:${NC}    $BIN_DIR/vibe-stack"
echo ""
