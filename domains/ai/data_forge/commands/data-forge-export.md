# `/data-forge-export` — Export and Format Conversion

> **This is a guidance document, not an automated execution tool.**
> It instructs AI agents on how to export and import datasets, captions, and workflow configurations using Data Forge MCP tools. No file I/O or format conversion is performed by this command directly.

---

## 1. Purpose

Export and import AI training data across formats: captions as JSON/CSV, ComfyUI workflow configurations, and batch format conversion. Each sub-command maps to specific Data Forge MCP export/import tools.

| Sub-command | Description |
|---|---|
| `captions` | Export or import captions as JSON or CSV |
| `workflow` | Export ComfyUI workflow configurations |
| `batch` | Batch export with format conversion for pipeline integration |

---

## 2. Usage

```
/data-forge-export captions --action export|import --input-path <path> [--output-path <path>] [--format json|csv|jsonl]
/data-forge-export workflow --action export [--input-path <path>] [--output-path <path>]
/data-forge-export batch --input-dir <path> --output-dir <path> [--format json|csv|jsonl] [--include all|captions|workflows]
```

### Aliases

```
/df-export captions --action export --input-path ./captions --output-path ./exports/captions.json
/df-export workflow --action export --output-path ./exports/workflow.json
/df-export batch --input-dir ./dataset --output-dir ./exports --format json
```

---

## 3. Parameters

### `captions` parameters

| Parameter | Required | Description |
|---|---|---|
| `--action` | Yes | Operation: `export` (captions → file) or `import` (file → captions). |
| `--input-path` | Yes | For `export`: directory containing caption files. For `import`: path to JSON/CSV file. |
| `--output-path` | Conditional | For `export`: output file path. For `import`: target directory for generated caption files. Required unless using defaults. |
| `--format` | No | File format: `json`, `csv`, or `jsonl`. Default: `json`. |

### `workflow` parameters

| Parameter | Required | Description |
|---|---|---|
| `--action` | Yes | Operation: `export` only (workflow configuration export). |
| `--input-path` | No | Path to ComfyUI workflow JSON. If omitted, references the most recently used workflow. |
| `--output-path` | No | Output file path. Default: `./exports/workflow_<timestamp>.json`. |

### `batch` parameters

| Parameter | Required | Description |
|---|---|---|
| `--input-dir` | Yes | Directory containing the dataset (images, captions, workflows). |
| `--output-dir` | Yes | Directory for exported files. Created if it does not exist. |
| `--format` | No | Export format: `json`, `csv`, or `jsonl`. Default: `json`. |
| `--include` | No | What to export: `all` (captions + workflows), `captions`, or `workflows`. Default: `all`. |

---

## 4. Execution Steps

### 4.1 `captions` — Export/Import Captions

**Export:**
1. **Validate input** — Confirm `--input-path` is a directory containing caption files. Run `caption_read_all` to verify data integrity.
2. **Invoke `caption_export`** — Pass `input_dir` and `output_path` (or derive from defaults) with the specified `--format`.
3. **Validate response** — Check `{"status": "ok"}`. On error, `message` may indicate file permission issues or invalid directory.
4. **Verify output** — Confirm the export file exists and contains the expected number of records. For JSON: validate structure. For CSV: verify column headers.

**Import:**
1. **Validate input** — Confirm `--input-path` is a JSON/CSV file. Verify structure: for JSON, array of objects with required fields; for CSV, check headers include caption text and image reference columns.
2. **Invoke `caption_import`** — Pass `input_file` and `output_dir` with the specified `--format`.
3. **Validate response** — Check `{"status": "ok"}`. On error, `message` may indicate format validation failures.
4. **Post-import validation** — Run `caption_stats` on the output directory to verify import quality. Check for encoding issues, field mismatches, orphaned files.

### 4.2 `workflow` — Export ComfyUI Workflow

1. **Locate workflow** — If `--input-path` provided, use that; otherwise reference the most recent workflow JSON.
2. **Validate workflow** — Confirm the JSON is a valid ComfyUI API-format workflow (contains node definitions with class types and inputs).
3. **Export** — Copy or serialize the workflow JSON to `--output-path`.
4. **Report** — Output file path, workflow node count, and key parameters (model, resolution, seed range).

### 4.3 `batch` — Batch Export

**Stage 1: Caption Export**
1. Locate captions in `--input-dir/captions/` (or detect from directory structure).
2. Invoke `caption_export` with detected input directory and `--output-dir/captions_export.<format>`.
3. Validate `{"status": "ok"}`.

**Stage 2: Workflow Export (if `--include all` or `workflows`)**
1. Locate workflow JSONs in `--input-dir/workflows/` or similar.
2. Copy workflow files to `--output-dir/workflows/`.
3. Report exported workflow count.

**Stage 3: Format Conversion**
1. If `--format jsonl`, convert any JSON exports to JSONL (one record per line) for streaming pipeline compatibility.
2. Validate all output files.

**Stage 4: Summary Report**
1. List all exported files with record counts.
2. Verify cross-references: exported caption count matches source caption count.

---

## 5. Output

**Example output (`captions export`):**

```
Caption Export Complete
├── Source:       ./captions/ (1,248 files)
├── Output:       ./exports/captions.json
├── Format:       json
├── Records:      1,248
├── Fields:       image, caption, timestamp
└── Status:       ok
```

**Example output (`captions import`):**

```
Caption Import Complete
├── Source:       ./external/captions.csv
├── Output:       ./captions/ (1,000 files created)
├── Format:       csv
├── Records:      1,000 imported
├── Warnings:     3 rows skipped (missing image field)
└── Status:       ok
```

**Example output (`batch`):**

```
Batch Export Complete
├── Captions:     ./exports/captions.json (1,248 records) [ok]
├── Workflows:    ./exports/workflows/ (3 files) [ok]
├── Format:       json
├── Output Dir:   ./exports/
└── Status:       ok
```

---

## 6. Format Specifications

### JSON Export (`caption_export --format json`)

```json
[
  {
    "image": "image_001.png",
    "caption": "A red car parked on a city street under cloudy skies.",
    "timestamp": "2026-05-26T12:00:00Z"
  }
]
```

### CSV Export (`caption_export --format csv`)

```csv
image,caption,timestamp
image_001.png,"A red car parked on a city street under cloudy skies.",2026-05-26T12:00:00Z
```

### JSONL Export (`caption_export --format jsonl`)

```jsonl
{"image": "image_001.png", "caption": "A red car parked on a city street under cloudy skies.", "timestamp": "2026-05-26T12:00:00Z"}
{"image": "image_002.png", "caption": "A woman reading a book in a sunlit cafe.", "timestamp": "2026-05-26T12:00:01Z"}
```

---

## 7. Notes

- **No file I/O execution.** This command provides guidance only. All read/write operations are performed by Data Forge MCP tools.
- **Format validation is critical for import.** Always inspect CSV headers and JSON structure before importing. Mismatched schemas cause `caption_import` to fail with `{"status": "error"}`.
- **JSONL is recommended for large datasets.** Streaming-compatible format avoids loading entire dataset into memory.
- **Export does not modify source data.** All export operations are read-only on the source. Import operations write new files without modifying source.
- **Workflow export is informational.** ComfyUI workflow JSONs are copied as-is; no validation of workflow executability is performed.
