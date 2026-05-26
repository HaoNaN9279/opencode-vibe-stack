# `/data-forge-process` — Image Processing Pipeline

> **This is a guidance document, not an automated execution tool.**
> It instructs AI agents on how to execute image processing pipelines using Data Forge MCP tools. No image processing, GPU operations, or model inference is performed directly by this command.

---

## 1. Purpose

Execute image processing operations on AI training datasets: resizing, background removal, and full batch pipelines. Each sub-command represents a processing stage that can be run independently or chained.

| Sub-command | Description |
|---|---|
| `resize` | Batch resize images to target dimensions with fit/pad modes |
| `remove-bg` | Remove backgrounds from images using BiRefNet models |
| `batch` | Execute full pipeline: resize → background removal → caption → describe → export |

---

## 2. Usage

```
/data-forge-process resize --input-dir <path> --output-dir <path> --width <px> --height <px> [--mode fit|pad]
/data-forge-process remove-bg --input-dir <path> --output-dir <path> [--model <model-name>]
/data-forge-process batch --input-dir <path> --output-dir <path> [--width <px>] [--height <px>] [--bg-model <model-name>] [--caption-provider openai|deepseek|ollama] [--export-format json|csv]
```

### Aliases

```
/df-process resize --input-dir ./images --output-dir ./resized --width 512 --height 512
/df-process remove-bg --input-dir ./images --output-dir ./no-bg
/df-process batch --input-dir ./raw --output-dir ./processed
```

---

## 3. Parameters

### `resize` parameters

| Parameter | Required | Description |
|---|---|---|
| `--input-dir` | Yes | Directory containing source images. |
| `--output-dir` | Yes | Directory for resized output images. Created if it does not exist. |
| `--width` | Yes | Target width in pixels. |
| `--height` | Yes | Target height in pixels. |
| `--mode` | No | Resize mode: `fit` (scale to fit within dimensions, preserving aspect ratio) or `pad` (scale and pad to exact dimensions). Default: `fit`. |

### `remove-bg` parameters

| Parameter | Required | Description |
|---|---|---|
| `--input-dir` | Yes | Directory containing source images. |
| `--output-dir` | Yes | Directory for background-removed output images. |
| `--model` | No | BiRefNet model variant. Options depend on installed `rembg` version. Default: latest available. |

### `batch` parameters

| Parameter | Required | Description |
|---|---|---|
| `--input-dir` | Yes | Directory containing source images. |
| `--output-dir` | Yes | Root output directory. Subdirectories created per stage. |
| `--width` | No | Resize target width. Default: `512`. |
| `--height` | No | Resize target height. Default: `512`. |
| `--bg-model` | No | BiRefNet model for background removal. Default: latest available. |
| `--caption-provider` | No | LLM provider for image description: `openai`, `deepseek`, or `ollama`. Default: `ollama`. |
| `--export-format` | No | Final export format: `json` or `csv`. Default: `json`. |

---

## 4. Execution Steps

### 4.1 `resize` — Batch Image Resize

1. **Validate input** — Confirm `--input-dir` exists and contains image files. Report file count and formats detected.
2. **Invoke `resize_images`** — Pass `input_dir`, `output_dir`, `width`, `height`, and `mode` parameters.
3. **Validate response** — Check `{"status": "ok"}` before proceeding. On error, report `message` and halt.
4. **Report** — Output resized count, dimensions applied, mode used, output location.

### 4.2 `remove-bg` — Background Removal

1. **Validate input** — Confirm `--input-dir` contains images (preferably pre-resized). Verify `rembg` package with BiRefNet models is installed.
2. **Choose tool** — `remove_background` for single images; `remove_background_batch` for directories. Prefer batch.
3. **Invoke `remove_background_batch`** — Pass `input_dir`, `output_dir`, and optionally `model`.
4. **Validate response** — Check `{"status": "ok"}`. Background removal is GPU-intensive; errors often indicate missing models or CUDA issues.
5. **Report** — Output processed count, model used, output location.

### 4.3 `batch` — Full Pipeline

The batch pipeline executes five stages sequentially, validating each before proceeding.

**Stage 1: Resize**
1. Create `output-dir/resized/` subdirectory.
2. Invoke `resize_images` with `--width` and `--height` parameters.
3. Validate `{"status": "ok"}`. Halt on failure.

**Stage 2: Background Removal**
1. Create `output-dir/no-bg/` subdirectory.
2. Invoke `remove_background_batch` using resized images as input, with `--bg-model` if specified.
3. Validate `{"status": "ok"}`. Halt on failure.

**Stage 3: Caption Generation**
1. Determine caption tool based on `--caption-provider`:
   - `openai` / `deepseek`: Use `llm_batch_describe_images` with appropriate keyfile.
   - `ollama`: Use `ollama_batch_describe_images` (verify server is running via `ollama_list_models` first).
2. Invoke the selected tool on background-removed images.
3. Validate `{"status": "ok"}`. Halt on failure.

**Stage 4: Caption Quality Check**
1. Run `caption_stats` on generated captions.
2. Run `caption_search` for anomalies (empty captions, encoding issues).
3. If quality metrics are unacceptable, recommend prompt refinement (see `/data-forge-prompt`) and re-run Stage 3.

**Stage 5: Export**
1. Create `output-dir/exports/` subdirectory.
2. Invoke `caption_export` with the specified `--export-format` (json/csv).
3. Validate `{"status": "ok"}`.
4. Report final pipeline summary.

---

## 5. Output

Each stage produces a status report with tool response data.

**Example output (`resize`):**

```
Resize Complete
├── Input:        ./images (250 files)
├── Output:       ./resized
├── Dimensions:   512 x 512
├── Mode:         fit
├── Processed:    250/250
└── Status:       ok
```

**Example output (`batch`):**

```
Batch Pipeline Complete
├── Stage 1: Resize         [ok] — 250/250 → ./processed/resized/
├── Stage 2: Background     [ok] — 250/250 → ./processed/no-bg/
├── Stage 3: Captions       [ok] — 250/250 via ollama/llava
├── Stage 4: Quality Check  [ok] — mean words=14.2, empty=2
├── Stage 5: Export         [ok] — ./processed/exports/captions.json
└── Total Time:             ~12 minutes (estimated)
```

---

## 6. Pipeline Stage Dependencies

```
resize ──→ remove-bg ──→ caption ──→ export
  │            │             │
  └─ optional standalone    └─ requires prior stages
```

- `resize`: Standalone — can run independently on raw images.
- `remove-bg`: Standalone — can run independently, but optimal when preceded by `resize` for consistent input dimensions.
- `batch`: All-in-one — executes all stages sequentially with dependency validation.

---

## 7. Notes

- **No GPU execution.** This command provides guidance only. Actual image processing runs on the user's machine via Data Forge MCP tools.
- **Background removal requires `rembg`** with BiRefNet models. Verify installation before suggesting `remove-bg` or `batch`.
- **LLM caption generation requires either:** a valid keyfile (cloud LLM) or a running Ollama server with the target model pulled (local LLM).
- **Pipeline stages are atomic.** If any stage fails, the pipeline halts. The user can resume from the failure point.
- **Disk space.** Batch pipelines generate intermediate directories. Ensure sufficient disk space for `resized/`, `no-bg/`, and `exports/` outputs.
