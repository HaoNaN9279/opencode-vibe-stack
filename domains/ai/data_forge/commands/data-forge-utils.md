# `/data-forge-utils` — Utility & Reference Guide

Slash command for quick access to tool documentation, dependency version checks, server status diagnostics, code snippet reference, and troubleshooting guidance across all Data Forge MCP tools.

---

## 1. Usage

```
/data-forge-utils docs <tool-name>              — Look up tool documentation
/data-forge-utils version [--all]              — Check dependency versions
/data-forge-utils status <service>             — Check ComfyUI or Ollama server status
/data-forge-utils snippets <topic>             — Browse code snippet index
/data-forge-utils help                         — Show this help
```

### Aliases

```
/df-utils docs resize_images
/df-utils version --all
/df-utils status ollama
/df-utils snippets caption-search
```

---

## 2. Tool Documentation Lookup (`docs`)

Look up the signature, parameters, and return format for any Data Forge MCP tool.

```
/data-forge-utils docs <tool-name>
```

The AI agent responds with:
- Tool name and category
- Full parameter list with types and descriptions
- Return format: `{"status": "ok"|"error", "message": "..."}`
- Usage example
- Common error scenarios

---

## 3. Version Check (`version`)

Check installed dependency versions for the Data Forge toolchain.

```
/data-forge-utils version [--all]
```

| Dependency | Minimum Version | Check Command |
|---|---|---|
| Python | 3.12+ | `python --version` |
| uv | Latest | `uv --version` |
| FastMCP | Latest | `uv pip list | grep fastmcp` |
| rembg | Latest (with BiRefNet) | `pip show rembg` |
| Ollama | Latest | `ollama --version` |
| ComfyUI | Latest | Check via `comfyui_status` |

**Usage:**

```
/df-utils version          — Show Python and core dependency versions
/df-utils version --all    — Show all dependencies including rembg, Ollama, ComfyUI
```

---

## 4. Server Status (`status`)

Check whether external services required by Data Forge are running and accessible.

```
/data-forge-utils status comfyui
/data-forge-utils status ollama
```

### ComfyUI Status (`status comfyui`)

1. Invoke `comfyui_status` MCP tool.
2. Report: server reachability, available workflows, GPU availability, queue state.
3. If unreachable, provide troubleshooting steps (see §7 — Troubleshooting).

### Ollama Status (`status ollama`)

1. Invoke `ollama_list_models` MCP tool.
2. Report: server reachability, installed models with tags, model sizes.
3. If unreachable, provide troubleshooting steps (see §7 — Troubleshooting).

---

## 5. Code Snippets (`snippets`)

Quick reference for common Data Forge tool invocation patterns.

```
/data-forge-utils snippets <topic>
```

### Snippet Index

| Topic | Description |
|---|---|
| `resize-batch` | Batch resize images with fit/pad modes |
| `bg-remove` | Single and batch background removal |
| `caption-search` | Regex search across captions |
| `caption-stats` | Full dataset profiling |
| `caption-dedup` | Deduplicate captions |
| `caption-export-import` | Format conversion workflows |
| `llm-batch` | Batch LLM image description |
| `ollama-batch` | Batch Ollama image description |
| `comfyui-workflow` | Run ComfyUI workflows |
| `pipeline-end-to-end` | Full pipeline: resize → bg → caption → export |

### Snippet: `resize-batch`

```
Tool: resize_images
Parameters:
  input_dir: str    — Directory containing source images
  output_dir: str   — Directory for resized output
  width: int        — Target width (pixels)
  height: int       — Target height (pixels)
  mode: str         — "fit" or "pad"
Returns: {"status": "ok"|"error", "message": "..."}
Example: resize_images(input_dir="./images", output_dir="./resized", width=512, height=512, mode="fit")
```

### Snippet: `caption-stats`

```
Tool: caption_stats
Parameters:
  directory: str    — Directory containing caption files
Returns: {"status": "ok"|"error", "message": "...", "data": {...}}
  data fields: total, word_count (min/max/mean/median/stddev),
               char_count (min/max/mean), empty_count
Example: caption_stats(directory="./captions")
```

### Snippet: `llm-batch`

```
Tool: llm_batch_describe_images
Parameters:
  input_dir: str    — Directory containing images
  output_dir: str   — Directory for generated captions
  model: str        — Model name (e.g., "gpt-4o")
  keyfile: str      — Path to API keyfile JSON
Returns: {"status": "ok"|"error", "message": "..."}
Example: llm_batch_describe_images(input_dir="./images", output_dir="./captions",
          model="gpt-4o", keyfile="./keys/openai.json")
```

### Snippet: `comfyui-workflow`

```
Tool: comfyui_run_workflow
Parameters:
  workflow: dict    — Workflow JSON as Python dict
  parameters: dict  — Parameter overrides
Returns: {"status": "ok"|"error", "message": "..."}
Tool: comfyui_run_batch
Parameters:
  workflow: dict    — Base workflow JSON
  parameter_sets: list[dict]  — Array of parameter overrides for batch
Returns: {"status": "ok"|"error", "message": "..."}
```

---

## 6. Complete MCP Tool Reference

All 24 Data Forge MCP tools organized by category.

### Resize (1 tool)

| Tool | Parameters | Description |
|---|---|---|
| `resize_images` | `input_dir`, `output_dir`, `width`, `height`, `mode` | Batch resize images with fit/pad modes |

### Background Removal (2 tools)

| Tool | Parameters | Description |
|---|---|---|
| `remove_background` | `input_path`, `output_path`, `model` (optional) | Remove background from single image |
| `remove_background_batch` | `input_dir`, `output_dir`, `model` (optional) | Batch background removal |

### Captions (9 tools)

| Tool | Parameters | Description |
|---|---|---|
| `caption_list` | `directory`, `recursive` (optional) | List all caption files in directory |
| `caption_read` | `file_path` | Read a single caption file |
| `caption_read_all` | `directory` | Read all captions in directory |
| `caption_search` | `directory`, `query` (regex), `case_sensitive` (optional) | Search captions by regex pattern |
| `caption_batch_replace` | `directory`, `query` (regex), `replace_with` | Batch regex replace across captions |
| `caption_export` | `input_dir`, `output_path`, `format` (json/csv/jsonl) | Export captions to file |
| `caption_import` | `input_file`, `output_dir`, `format` (json/csv) | Import captions from file |
| `caption_stats` | `directory` | Compute caption statistics |
| `caption_deduplicate` | `directory`, `strategy` (keep-first/keep-last) | Deduplicate captions |

### LLM Cloud (4 tools)

| Tool | Parameters | Description |
|---|---|---|
| `llm_chat` | `prompt`, `model`, `keyfile` | Single-turn LLM chat |
| `llm_describe_image` | `image_path`, `prompt`, `model`, `keyfile` | Describe a single image |
| `llm_batch_chat` | `prompts` (list), `model`, `keyfile` | Batch LLM chat |
| `llm_batch_describe_images` | `input_dir`, `output_dir`, `model`, `keyfile` | Batch image description |

### Ollama Local (5 tools)

| Tool | Parameters | Description |
|---|---|---|
| `ollama_generate` | `prompt`, `model` | Single text generation via Ollama |
| `ollama_list_models` | _(none)_ | List available Ollama models |
| `ollama_describe_image` | `image_path`, `prompt`, `model` | Describe single image via Ollama |
| `ollama_batch_generate` | `prompts` (list), `model` | Batch text generation |
| `ollama_batch_describe_images` | `input_dir`, `output_dir`, `model` | Batch image description via Ollama |

### ComfyUI (3 tools)

| Tool | Parameters | Description |
|---|---|---|
| `comfyui_status` | _(none)_ | Check ComfyUI server status |
| `comfyui_run_workflow` | `workflow` (dict), `parameters` (dict, optional) | Run single ComfyUI workflow |
| `comfyui_run_batch` | `workflow` (dict), `parameter_sets` (list[dict]) | Run batch ComfyUI workflows with parameter sweeps |

### Response Format (All Tools)

Every tool returns:
```json
{"status": "ok"|"error", "message": "..."}
```

On `"ok"`, additional fields may be present (e.g., `data` for `caption_stats`, `count` for batch operations).
On `"error"`, `message` contains the error description.

---

## 7. Configuration Reference

### Keyfile Format (Cloud LLM)

Path to a JSON file with the following structure:

```json
{
  "provider": "openai",
  "api_key": "sk-...",
  "api_base": "https://api.openai.com/v1"
}
```

| Field | Required | Description |
|---|---|---|
| `provider` | Yes | Provider identifier: `openai` or `deepseek` |
| `api_key` | Yes | API key string |
| `api_base` | No | Custom API base URL (for proxies or self-hosted endpoints) |

**Notes:**
- The AI agent must **never** generate API keys or keyfiles. Only guide users to create their own.
- Keyfile paths must be absolute or relative to the working directory.

### ComfyUI Workflow Format

ComfyUI workflows are JSON objects in the ComfyUI API format:

```json
{
  "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"}},
  "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "a beautiful landscape", "clip": ["1", 1]}},
  "3": {"class_type": "KSampler", "inputs": {"seed": 42, "steps": 20, "cfg": 7.0, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0, "model": ["1", 0], "positive": ["2", 0], "negative": ["4", 0], "latent_image": ["5", 0]}},
  "4": {"class_type": "CLIPTextEncode", "inputs": {"text": "bad quality, blurry", "clip": ["1", 1]}},
  "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
  "6": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["1", 2]}},
  "7": {"class_type": "SaveImage", "inputs": {"filename_prefix": "output", "images": ["6", 0]}}
}
```

**Notes:**
- Node IDs are string keys (`"1"`, `"2"`, etc.).
- Node references are `[source_node_id, output_index]`.
- `comfyui_run_batch` accepts `parameter_sets` as a list of dicts, where each dict overrides node inputs for one batch iteration.

### Ollama Setup

1. Install Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
2. Pull a vision-capable model: `ollama pull llava:13b`
3. Verify: `ollama list`
4. The Data Forge MCP tools connect to `http://localhost:11434` by default.

---

## 8. Troubleshooting

### Scenario 1: `comfyui_status` returns error

**Symptom:** `{"status": "error", "message": "Connection refused"}`

**Cause:** ComfyUI server is not running or is on a different port.

**Steps:**
1. Verify ComfyUI is running: check terminal window for the ComfyUI process.
2. Default URL: `http://127.0.0.1:8188`. Verify that port is not blocked by firewall.
3. Restart ComfyUI and re-run `comfyui_status`.

### Scenario 2: `ollama_list_models` returns error

**Symptom:** `{"status": "error", "message": "Failed to connect to Ollama"}`

**Cause:** Ollama service is not running.

**Steps:**
1. Start Ollama: `ollama serve`
2. Verify: `ollama list`
3. If no models installed: `ollama pull llava:13b`
4. Re-run `ollama_list_models`.

### Scenario 3: `llm_batch_describe_images` fails with 401

**Symptom:** `{"status": "error", "message": "401 Unauthorized"}`

**Cause:** Invalid or missing API key in keyfile.

**Steps:**
1. Verify keyfile exists and contains valid `api_key` field.
2. Check the key has not been revoked or expired.
3. Verify `api_base` URL is correct (especially for DeepSeek or proxy setups).
4. Test with a minimal single-image call: `llm_describe_image`.

### Scenario 4: `remove_background_batch` fails

**Symptom:** `{"status": "error", "message": "No module named 'rembg'"}`

**Cause:** `rembg` Python package not installed or BiRefNet models not downloaded.

**Steps:**
1. Install rembg: `uv pip install rembg`
2. Download BiRefNet models: `rembg download` (or equivalent)
3. Verify: `python -c "from rembg import remove"` succeeds.
4. For GPU acceleration: ensure CUDA toolkit and `onnxruntime-gpu` are installed.

### Scenario 5: `caption_import` fails on CSV

**Symptom:** `{"status": "error", "message": "Missing required fields"}`

**Cause:** CSV file has incorrect column headers or missing data.

**Steps:**
1. Required columns: `image` (filename), `caption` (text).
2. Optional columns: `timestamp`, `tags`.
3. Verify no empty rows or unescaped commas in caption text.
4. Try importing as JSON instead of CSV if the data is complex.

### Scenario 6: `caption_search` returns no matches

**Symptom:** No results found for a valid regex pattern.

**Cause:** Case sensitivity mismatch or file encoding issues.

**Steps:**
1. Verify `case_sensitive` parameter (default may vary).
2. Check caption file encoding — non-UTF-8 files may cause silent failures.
3. Test with a simple literal pattern first, then add regex complexity.
4. Run `caption_read_all` to verify captions are accessible.

### Scenario 7: Batch pipeline out of disk space

**Symptom:** Tool returns `{"status": "error", "message": "No space left on device"}`

**Cause:** Intermediate pipeline stages (resized/, no-bg/, exports/) consume significant disk.

**Steps:**
1. Estimate space needed: original_size × 3 (resized + no-bg + exports).
2. Clean intermediate directories after each stage if space is tight.
3. Use `--output-dir` on a different volume if available.

---

## 9. External Resources

| Resource | URL |
|---|---|
| Data Forge GitHub | `git@github.com:HaoNaN9279/data_forge.git` |
| Python 3.12 Documentation | `https://docs.python.org/3.12/` |
| FastMCP Documentation | `https://github.com/jlowin/fastmcp` |
| rembg (Background Removal) | `https://github.com/danielgatis/rembg` |
| BiRefNet Models | `https://github.com/ZhengPeng7/BiRefNet` |
| Ollama | `https://ollama.com/` |
| ComfyUI | `https://github.com/comfyanonymous/ComfyUI` |
| uv Package Manager | `https://github.com/astral-sh/uv` |

---

**Related commands:** `/data-forge-dataset`, `/data-forge-process`, `/data-forge-prompt`, `/data-forge-export`

**Related agents:** Data Forge Development Assistant, Data Forge Data Curator, Data Forge Prompt Engineer
