# ---- Path/Platform Helpers ----

# Convert a POSIX path to Windows format (/c/Users/... -> C:\Users\...)
posix_to_win() {
    local path="$1"
    if command -v cygpath &>/dev/null; then
        cygpath -wa "$path" 2>/dev/null && return
    fi
    echo "$path" | sed 's|^/\([a-zA-Z]\)/|\1:\\|; s|/|\\|g'
}

# Create a directory link: symlink on Linux/macOS, junction on Windows.
# On MSYS2/Cygwin, uses PowerShell junction FIRST to avoid ln -s silently
# copying large directory trees. NEVER falls back to copying.
# Returns 0 on success, 1 on failure.
create_dir_link() {
    local src="$1"
    local dest="$2"

    # Remove existing safely (handles junctions on Windows)
    if [ -e "$dest" ] || [ -L "$dest" ]; then
        case "$OSTYPE" in
            msys|cygwin)
                # rm (without -r) removes symlinks/junctions without following them
                rm -f "$dest" 2>/dev/null || true
                ;;
            *)
                rm -rf "$dest" 2>/dev/null || true
                ;;
        esac
    fi

    # MSYS2/Cygwin: try junction first (no admin, no Developer Mode needed).
    # ln -s on MSYS2 without Developer Mode silently COPIES directories —
    # we skip it entirely to avoid wasteful copy+delete for large trees.
    case "$OSTYPE" in
        msys|cygwin)
            local win_src win_dest
            win_src="$(posix_to_win "$src")"
            win_dest="$(posix_to_win "$dest")"
            if [ -n "$win_src" ] && [ -n "$win_dest" ]; then
                if powershell -NoProfile -Command \
                    "New-Item -ItemType Junction -Path '$win_dest' -Target '$win_src' -Force | Out-Null" \
                    2>/dev/null; then
                    return 0
                fi
            fi
            # Junction failed — fall through to ln -s as last resort
            ;;
    esac

    # Native symlink (Linux/macOS primary, Windows fallback)
    if ln -s "$src" "$dest" 2>/dev/null; then
        if [ -L "$dest" ]; then
            return 0
        fi
        # MSYS2 silently copied — undo the copy
        case "$OSTYPE" in
            msys|cygwin)
                rm -rf "$dest" 2>/dev/null || true
                ;;
        esac
    fi

    return 1
}

# Create a symlink for any item (file or directory).
# Directories delegate to create_dir_link; files use ln -s.
# Returns 0 on success, 1 on failure.
create_item_link() {
    local src="$1"
    local dest="$2"

    if [ -d "$src" ]; then
        create_dir_link "$src" "$dest"
        return $?
    fi

    rm -f "$dest" 2>/dev/null || true
    if ln -s "$src" "$dest" 2>/dev/null; then
        if [ -L "$dest" ]; then
            return 0
        fi
        # MSYS2 silently copied — symlink capability not available (needs admin on Windows)
        rm -f "$dest" 2>/dev/null || true
        return 1
    fi

    return 1
}

# Create per-item symlinks from src_dir into dest_dir.
# Removes an old directory-level symlink at dest_dir if present.
# Optional prefix is prepended to each item name with a hyphen.
# Returns 0 on success, 1 on failure.
link_directory_contents() {
    local src_dir="$1"
    local dest_dir="$2"
    local prefix="${3:-}"

    if [ -L "$dest_dir" ]; then
        rm -f "$dest_dir" 2>/dev/null || true
    fi

    mkdir -p "$dest_dir" || return 1

    local item item_name final_name
    shopt -s nullglob
    for item in "$src_dir"/*; do
        item_name="$(basename "$item")"
        if [ -n "$prefix" ]; then
            final_name="${prefix}-${item_name}"
        else
            final_name="$item_name"
        fi
        create_item_link "$item" "$dest_dir/$final_name" || return 1
    done
    shopt -u nullglob

    return 0
}
