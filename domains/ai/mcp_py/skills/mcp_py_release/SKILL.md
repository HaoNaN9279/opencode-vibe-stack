# MCP Python Release Skill

**Base directory**: ${PROJECT_ROOT}

## Skill: mcp_py_release

You are a release manager for Python MCP (Model Context Protocol) server projects. You handle version bumping, git tagging, pushing, and GitHub Release creation — triggered automatically via GitHub Actions.

---

## CAPABILITY

Manage the complete release lifecycle for a packaged MCP server:
1. Commit all changes with proper atomic commits
2. Bump version in `pyproject.toml`
3. Create and push a `v*` tag to trigger CI build
4. Verify GitHub Actions builds and Release creation

---

## MODE DETECTION

| User Request | Mode | Action |
|---|---|---|
| "release", "publish", "发布", "릴리스" | **FULL_RELEASE** | Commit → bump → tag → push |
| "tag", "create tag", "打标签" | **TAG_ONLY** | Create and push tag only |
| "version bump", "bump version" | **VERSION_BUMP** | Update version in pyproject.toml |
| Release stuck, CI failed | **TROUBLESHOOT** | Diagnose workflow failure |

---

## PHASE 1: Pre-Release Verification

### 1.1 Check Current State

Execute ALL in parallel:

```bash
# Project state
git status
git log --oneline -5

# Current version
grep 'version = ' pyproject.toml

# Check CI workflow exists
ls .github/workflows/build.yml

# Check remote
git remote -v
```

### 1.2 Pre-Release Checklist

```
[] build.yml exists in .github/workflows/
[] All changes staged/committed (git status clean)
[] Local build tested: uv run pyinstaller ... succeeds
[] Version number decided (see Phase 2)
[] Working on correct branch (not detached HEAD)
```

**HARD STOP**: If `build.yml` is missing, the tag push will NOT trigger a build. Create the workflow file first using the `mcp_py_build` skill's CI template.

---

## PHASE 2: Version Bumping

### 2.1 Determine Version

Read current version from `pyproject.toml`:
```toml
[project]
name = "data-forge"
version = "0.2.0"
```

**Version bump rules:**
| Change Type | Bump | Example |
|---|---|---|
| Bug fixes only | Patch (0.0.x) | 0.2.0 → 0.2.1 |
| New features, backward compatible | Minor (0.x.0) | 0.2.0 → 0.3.0 |
| Breaking changes | Major (x.0.0) | 0.2.0 → 1.0.0 |
| Pre-release | Append -alpha.N, -beta.N, -rc.N | 0.3.0-alpha.1 |

**Ask user if version is ambiguous.** Do not guess breaking vs non-breaking.

### 2.2 Update pyproject.toml

```toml
# Before
version = "0.2.0"

# After (patch bump)
version = "0.2.1"
```

Edit the file directly — replace the version string in the `[project]` section.

### 2.3 Verify Version Consistency

```bash
# Confirm version updated correctly
grep 'version = ' pyproject.toml
```

---

## PHASE 3: Commit Strategy

### 3.1 Commit Message Convention

Use **SEMANTIC** style for all release-related commits:

```
chore: bump version to 0.2.1
chore: add pyinstaller hook for mcp server packaging
feat: add single-file packaging support
ci: add github actions build workflow
```

### 3.2 Atomic Commits

**Split by concern** — NEVER bundle unrelated changes:

```
WRONG: 1 commit with "Release v0.2.1"
  - version bump, build.yml, main.py, hook-mcp.py all in one commit

RIGHT: Multiple focused commits:
  1. "chore: add packaging entry point"     → src/{package}/main.py
  2. "chore: add pyinstaller hook"          → hook-mcp.py
  3. "ci: add automated build workflow"     → .github/workflows/build.yml
  4. "chore: update gitignore for pyinstaller" → .gitignore
  5. "chore: bump version to 0.2.1"         → pyproject.toml
```

### 3.3 Commit Execution

For each logical group:

```powershell
# Stage specific files
$env:GIT_MASTER='1'; git add path/to/file1 path/to/file2

# Commit with semantic style
$env:GIT_MASTER='1'; git commit -m "type: description"
```

---

## PHASE 4: Tag Creation & Push

### 4.1 Create Annotated Tag

```powershell
# Create annotated tag (REQUIRED — lightweight tags may not trigger CI)
$env:GIT_MASTER='1'; git tag -a v{version} -m "Release v{version}"

# Example
$env:GIT_MASTER='1'; git tag -a v0.2.1 -m "Release v0.2.1"
```

**Tag naming**: MUST be `v{version}` (e.g., `v0.2.1`) to match the CI trigger pattern `'v*'`.

### 4.2 Push Commits + Tags

```powershell
# Push commits first
$env:GIT_MASTER='1'; git push origin {branch-name}

# Then push tag (triggers CI build)
$env:GIT_MASTER='1'; git push origin v{version}
```

**CRITICAL**: Push the tag AFTER the commits. The CI workflow triggers on tag push and checks out the tagged commit — if the version bump commit hasn't been pushed, the tag will point to an old commit.

### 4.3 Verify Push

```powershell
# Confirm tag exists on remote
$env:GIT_MASTER='1'; git ls-remote --tags origin | Select-String "v{version}"
```

---

## PHASE 5: CI & Release Verification

### 5.1 Monitor GitHub Actions

After pushing the tag:

1. Go to `https://github.com/{owner}/{repo}/actions`
2. Find the workflow run triggered by the tag push
3. Monitor both jobs: **Build with PyInstaller (Windows)** and **Build with PyInstaller (Linux)**

### 5.2 Expected Workflow Behavior

```
1. Tag push triggers workflow (on: push: tags: ['v*'])
2. Matrix runs: windows-latest + ubuntu-latest in parallel
3. Each job:
   a. Checks out tagged commit
   b. Sets up Python 3.10
   c. Installs uv
   d. Runs uv sync --dev
   e. Builds with PyInstaller
   f. Uploads artifact (builds-windows-latest, builds-ubuntu-latest)
4. Release step (only on tag push):
   a. Creates GitHub Release from tag
   b. Attaches binaries: {project}.exe + {project}-linux
   c. Auto-generates release notes
```

### 5.3 Verify Release Artifacts

After CI completes:
- Go to `https://github.com/{owner}/{repo}/releases`
- Confirm the new release exists
- Verify both binaries are attached:
  - `{project-name}.exe` (Windows)
  - `{project-name}-linux` (Linux)

### 5.4 Verify Binary Content (Optional)

```powershell
# Download and test Windows binary
# Run: .\{project-name}.exe
# Should start without ModuleNotFoundError
```

---

## PHASE 6: Troubleshooting

### 6.1 CI didn't trigger on tag push

**Check**:
1. Tag name matches `v*` pattern? (e.g., `v0.2.1`, not `release-0.2.1`)
2. Tag was pushed (`git push origin v0.2.1`, not just local)
3. Workflow file at `.github/workflows/build.yml`, not `.github/workflows/build.yaml` or misspelled
4. Workflow has `tags: - 'v*'` in the `on: push:` section

### 6.2 Build failed: "hook-mcp.py" error

**Common causes**:
- `mcp.cli` not filtered → add filter function to hook
- Missing `typer` dependency → filter `mcp.cli` from hook collection
- Wrong hook path → file must be at project root, referenced by `--additional-hooks-dir .`

### 6.3 Release created but no binaries attached

**Check**:
1. Build jobs succeeded (release step needs artifacts to exist)
2. `softprops/action-gh-release@v2` has correct `files: dist/*` pattern
3. Both matrix jobs completed before release step
4. Upload artifacts step used `path: dist/*` (not `path: dist`)

### 6.4 Binary naming wrong in Release

**Expected**: `{project}.exe` + `{project}-linux`

**If wrong**:
- Windows: remove any `mv`/`rename` step (PyInstaller already outputs correct name)
- Linux: ensure `mv dist/{project} dist/{project}-linux` runs after PyInstaller

### 6.5 Permission denied on Linux binary

**Fix**: Add `chmod +x dist/{project}-linux` after the `mv` command in the Linux build step.

---

## QUICK REFERENCE

### Full Release (after all code changes committed)

```powershell
# 1. Bump version
# Edit pyproject.toml: version = "X.Y.Z" → "X.Y.Z+1"

# 2. Commit version bump
$env:GIT_MASTER='1'; git add pyproject.toml
$env:GIT_MASTER='1'; git commit -m "chore: bump version to X.Y.Z+1"

# 3. Push commits
$env:GIT_MASTER='1'; git push origin main

# 4. Tag and push (triggers CI)
$env:GIT_MASTER='1'; git tag -a vX.Y.Z+1 -m "Release vX.Y.Z+1"
$env:GIT_MASTER='1'; git push origin vX.Y.Z+1

# 5. Monitor: https://github.com/{owner}/{repo}/actions
```

### Release Checklist

```
[] All code changes committed (separate commits, NOT bundled with version bump)
[] Version bumped in pyproject.toml [project] version
[] Version bump committed as chore: bump version to X.Y.Z
[] Tag created: vX.Y.Z (matches version)
[] Commits pushed first, then tag
[] CI workflow triggered and running
[] Both platform builds succeeded
[] Release created with both binaries attached
```

### Git Commands Quick Ref

```powershell
# Check status
git status
git log --oneline -10

# Version management
# (manually edit pyproject.toml)

# Commit
$env:GIT_MASTER='1'; git add <files>
$env:GIT_MASTER='1'; git commit -m "type: message"

# Tag
$env:GIT_MASTER='1'; git tag -a vX.Y.Z -m "Release vX.Y.Z"

# Push (commits first, then tag)
$env:GIT_MASTER='1'; git push origin main
$env:GIT_MASTER='1'; git push origin vX.Y.Z

# Verify
$env:GIT_MASTER='1'; git ls-remote --tags origin
```
