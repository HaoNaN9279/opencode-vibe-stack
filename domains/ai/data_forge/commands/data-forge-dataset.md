# `/data-forge-dataset` — Dataset Management

> **This is a guidance document, not an automated execution tool.**
> It instructs AI agents on how to manage AI training datasets using the Data Forge MCP tools. No software installation, runtime invocation, or automated execution is performed.

---

## 1. Purpose

Manage AI training datasets through the full lifecycle: listing, inspecting, creating, and cleaning. Each sub-command maps to specific Data Forge MCP tools.

| Sub-command | Description |
|---|---|
| `list` | List datasets in a directory, showing image and caption counts |
| `inspect` | Show dataset profile with statistics (word counts, distribution, quality metrics) |
| `create` | Scaffold a new dataset directory structure with conventional layout |
| `clean` | Deduplicate captions and validate dataset integrity |

---

## 2. Usage

```
/data-forge-dataset list --directory <path> [--recursive]
/data-forge-dataset inspect --directory <path> [--format json|csv]
/data-forge-dataset create --directory <path> [--name <dataset-name>]
/data-forge-dataset clean --directory <path> [--strategy keep-first|keep-last]
```

### Aliases

```
/df-dataset list --directory ./input
/df-dataset inspect --directory ./my-dataset
/df-dataset create --directory ./projects --name v1-captions
/df-dataset clean --directory ./my-dataset --strategy keep-first
```

---

## 3. Parameters

### Global parameters

| Parameter | Required | Description |
|---|---|---|
| `--directory` | Yes | Path to the dataset directory. Must exist for `list`, `inspect`, `clean`; will be created for `create`. |

### `list` parameters

| Parameter | Required | Description |
|---|---|---|
| `--recursive` | No | Recursively list subdirectories. Default: `false` (top-level only). |
| `--format` | No | Output format: `json` or `csv`. Default: terminal table. |

### `inspect` parameters

| Parameter | Required | Description |
|---|---|---|
| `--format` | No | Profile output format: `json` or `csv`. Default: `json`. |

### `create` parameters

| Parameter | Required | Description |
|---|---|---|
| `--name` | No | Dataset name. Used for the directory name if different from `--directory`. Default: basename of `--directory`. |

### `clean` parameters

| Parameter | Required | Description |
|---|---|---|
| `--strategy` | No | Deduplication keep strategy: `keep-first` or `keep-last`. Default: `keep-first`. |

---

## 4. Execution Steps

### 4.1 `list` — List Datasets

1. **Validate directory** — Confirm `--directory` exists and is accessible.
2. **Enumerate contents with `caption_list`** — Call `caption_list` on the target directory to retrieve all caption files and associated metadata.
3. **Report** — Present image count, caption count, and any orphaned files (captions without images, images without captions). If `--recursive`, enumerate subdirectories.
4. **Format output** — Table format by default; JSON/CSV if `--format` specified.

### 4.2 `inspect` — Dataset Profiling

1. **Run `caption_stats`** — Call `caption_stats` on the target directory to compute:
   - Total captions
   - Word count distribution (min, max, mean, median, stddev)
   - Character distribution
   - Empty caption count
   - Vocabulary diversity metrics
2. **Run `caption_search` for anomalies** — Search for empty files, encoding issues, and format violations with appropriate regex patterns.
3. **Cross-reference with `caption_read_all`** — Read all captions to verify every image has a caption and vice versa.
4. **Generate quality scorecard** — Compile metrics into a structured report: format compliance, deduplication estimate, vocabulary coverage.

### 4.3 `create` — Scaffold New Dataset

1. **Create directory structure:**
   ```
   <dataset-name>/
   ├── images/            # Source images
   ├── captions/          # Caption files (.txt, .json, .csv)
   ├── output/            # Processed output (resized, bg-removed)
   ├── exports/           # Export artifacts (JSON/CSV dumps)
   └── workflow/          # ComfyUI workflow JSONs (optional)
   ```
2. **Initialize with `caption_import`** — If the user provides initial captions (JSON/CSV), import them into the `captions/` directory.
3. **Report** — List created directories and their intended purpose.

### 4.4 `clean` — Deduplicate and Validate

1. **Backup recommendation** — ALWAYS recommend the user back up the dataset before running destructive operations.
2. **Run `caption_deduplicate`** — Execute deduplication with the specified `--strategy`:
   - `keep-first`: Retain the first occurrence of each caption, remove subsequent duplicates.
   - `keep-last`: Retain the last occurrence, remove earlier duplicates.
3. **Run `caption_stats` post-clean** — Verify deduplication results: reduced count, unchanged distribution profile for retained captions.
4. **Validate format consistency** — Check all remaining captions have consistent file extensions, encoding, and structure.
5. **Report** — Present before/after statistics: captions removed, captions retained, deduplication rate.

---

## 5. Output

The command produces a structured report at each stage. Reports include tool call results with `{"status": "ok"|"error", "message": "..."}` responses.

**Example output (`list`):**

```
Dataset: ./my-dataset
├── images/     — 1,250 files (.png, .jpg)
├── captions/   — 1,248 files (.txt)
└── ORPHANS:    — 2 images without captions, 0 captions without images
```

**Example output (`inspect`):**

```
Dataset Profile: ./my-dataset
├── Total Captions:     1,248
├── Word Count:         mean=12.4, median=11, stddev=5.2, min=3, max=47
├── Character Count:    mean=78.2, median=72, min=18, max=312
├── Empty Captions:     3
├── Format Compliance:  98.6% (17 files with encoding issues)
└── Vocabulary Size:    2,847 unique words
```

**Example output (`clean`):**

```
Clean Report: ./my-dataset
├── Before:             1,248 captions
├── Duplicates Found:   42
├── After:              1,206 captions
├── Deduplication Rate: 3.4%
└── Strategy:           keep-first
```

---

## 6. Notes

- **No automated execution.** This command provides guidance only. The AI agent instructs the user on which MCP tools to invoke and interprets their output.
- **Tool dependency order.** `inspect` must precede `clean` — never clean without profiling first.
- **`caption_deduplicate` is destructive.** Always recommend backup before execution. The Data Curator agent enforces this rule.
- **Directory validation.** All `--directory` values must be absolute paths or relative to the current working directory. Paths are passed directly to MCP tools.
