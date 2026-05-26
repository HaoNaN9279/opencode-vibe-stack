# Data Forge — AI Training Data Pipeline Rules

Rules for AI-assisted training data preparation with the Data Forge MCP toolkit. Follow these in every AI dataset project. Target Python 3.12+. **MUST NOT: Fabricate API signatures. All MCP tool signatures must be verifiable against the data_forge AGENTS.md or source code.**

## Project Structure

- Place raw source images in `data/raw/` before any processing. Keep originals unmodified — all transformations write to `data/processed/`.
- Store caption `.txt` files in `captions/`, one per image (same basename). Caption files are plain UTF-8 text — no metadata headers or structured formats unless explicitly requested.
- Write generated or processed outputs to `outputs/`, organized by processing stage: `outputs/resized/`, `outputs/cutouts/`, `outputs/described/`, `outputs/generated/`.
- Keep ComfyUI API-format workflow JSON files in `workflows/`. Workflows must be API format (exported via ComfyUI's "Save (API Format)" button), not standard format.
- Store API keyfiles and other secrets in `resources/`. This directory is git-ignored — never commit keys or tokens. Keyfile format is JSON with provider name keys mapping to credential objects.
- Keep project-level scripts and pipeline orchestration at the project root, importing from `data_forge.tools` modules.
- Separate pipeline stages into discrete scripts — one script per processing stage — for reusability and reproducibility.

## Coding Conventions

- Target Python 3.12+. Use `from __future__ import annotations` in every module for forward-reference type hints.
- Use `uv` for dependency management — `uv sync` for install, `uv add`/`uv remove` for dependency changes, `uv lock` after changes. Never hand-edit `pyproject.toml` dependency lists.
- Always use data_forge MCP tools (via `uv run data-forge-mcp` or direct Python import) instead of raw PIL/requests calls when a tool covers the operation. Fall back to direct library calls only when the tool lacks the required feature.
- Always check `response["status"]` before using MCP tool results. Handle both `"ok"` and `"error"` responses — errors include a `"message"` field with diagnostic information.
- All tools return structured JSON with `status` and tool-specific data. Parse this contract consistently — never assume a successful response without checking the status field.
- Use type hints on all public functions. Follow PEP 8 with a 100-character line limit. Docstrings in Google style.
- Run `uv run ruff check src/` and `uv run ruff format src/` before committing pipeline code.

## API Usage Patterns

- **Resize** (`resize_images`): Batch resize with aspect-ratio preservation. Supports `fit` mode (scale-to-fit within bounds with padding) and `pad` mode (add letterbox padding to reach exact dimensions). Input: directory of images. Output: resized images in output directory with same filenames.
- **Background Removal** (`remove_background`, `remove_background_batch`): Uses BiRefNet models through rembg. `remove_background` processes a single image; `remove_background_batch` processes entire directories. Supports `birefnet-general` and `birefnet-portrait` models with optional alpha matting refinement. rembg must be installed separately: `uv sync --extra rembg`.
- **Captions** (9 tools): Full caption lifecycle management. `caption_list` — enumerate captions in a directory. `caption_read` — read a single caption file. `caption_read_all` — read all captions at once. `caption_search` — search captions by text pattern. `caption_batch_replace` — find-and-replace across all captions (supports regex). `caption_export` — export to JSON, CSV, or JSONL. `caption_import` — import from JSON, CSV, or JSONL. `caption_stats` — word counts, length distributions, and frequency analytics. `caption_deduplicate` — find and remove duplicate captions. All caption tools operate on `.txt` files with one caption per file.
- **LLM — Cloud** (4 tools): Multi-provider text and vision via OpenAI-compatible APIs. Requires a keyfile in `resources/` with provider credentials. `llm_chat` — single-turn text generation. `llm_describe_image` — single image description. `llm_batch_chat` — batch text generation from prompts. `llm_batch_describe_images` — batch image description from directories. Provider is configurable (openai, anthropic, etc.) via keyfile and tool parameter.
- **Ollama — Local** (5 tools): Local model inference for text generation and vision. Defaults to `http://localhost:11434` (configurable). `ollama_generate` — single text generation. `ollama_list_models` — list available local models. `ollama_describe_image` — single image description via vision models. `ollama_batch_generate` — batch text generation. `ollama_batch_describe_images` — batch image description. Models must be pulled in advance with `ollama pull <model>`.
- **ComfyUI** (3 tools): Workflow-based image generation. Defaults to `http://localhost:8188` (configurable). `comfyui_status` — check server availability and queue status. `comfyui_run_workflow` — submit a single workflow and wait for completion. `comfyui_run_batch` — run a workflow with parameter sweeps (e.g., multiple prompts or seeds). Workflows must be ComfyUI API-format JSON — use "Save (API Format)" in ComfyUI, not standard "Save".

## Performance

- Prefer batch operations over single-item calls: use `remove_background_batch` instead of per-image `remove_background`, `llm_batch_describe_images` instead of looping `llm_describe_image`, and `caption_batch_replace` over individual `caption_read`→edit→write cycles.
- Use `llm_batch_describe_images` or `ollama_batch_describe_images` for describing multiple images — single-image calls re-initialize the client and model context on each invocation.
- rembg sessions (BiRefNet model loading) are expensive. `remove_background_batch` caches the loaded model across images — always batch background removal operations.
- Use `comfyui_run_batch` for parameter sweeps (seed grids, prompt variations) instead of submitting individual `comfyui_run_workflow` calls. Batch mode avoids re-uploading the workflow JSON for each variant.
- Monitor `comfyui_status` queue size before submitting large batches — a saturated queue with pending jobs will cause timeouts.

## Common Pitfalls

- Forgetting to check `response["status"]` — "error" responses return 200-level HTTP but contain failure data. Always branch on `status == "ok"` before accessing result payload.
- Missing keyfile for LLM tools — LLM tools require a `resources/` directory with a valid JSON keyfile. Attempting LLM calls without a keyfile returns a clear error but wastes debugging time.
- rembg dependency not installed — background removal tools fail with import errors if rembg is not installed. Use `uv sync --extra rembg` before any background removal operations.
- ComfyUI server not running — tools fail with connection-refused errors. Check `comfyui_status` before submitting workflows. Start ComfyUI separately; data_forge does not manage the server lifecycle.
- Ollama model not pulled — `ollama_generate` and `ollama_describe_image` fail if the requested model is not available locally. Use `ollama_list_models` to verify availability; pull missing models with `ollama pull <model>`.
- Caption file encoding issues — caption tools assume UTF-8. Non-UTF-8 caption files produce garbled text or import failures. Normalize caption encoding before bulk operations.
- Directory paths with spaces — some MCP tools may not handle paths with spaces correctly. Use `Path` objects or quote paths in shell invocations. Prefer relative paths within the project.

## Testing

- Use pytest for all pipeline tests. Mock external dependencies (network calls to ComfyUI/Ollama/LLM APIs, rembg model loading) with `unittest.mock.patch`.
- Test each tool category independently — resize, background removal, captions, LLM, Ollama, and ComfyUI each have their own test module under `tests/`.
- After processing, verify output files exist and are non-empty: check `Path(output_dir).glob("*")` for expected files.
- Always assert on `response["status"]` in integration tests — a successful HTTP response does not guarantee a successful tool operation.
- Use a dedicated test dataset (small set of sample images) for integration tests to keep test runs fast and deterministic.

## Configuration & Environment

- **API Keyfile**: JSON file in `resources/` mapping provider names to credential objects. Format: `{"openai": {"api_key": "sk-...", "base_url": "https://api.openai.com/v1"}, "anthropic": {...}}`. Referenced by LLM tools via the `keyfile` parameter.
- **ComfyUI Workflows**: Stored in `workflows/` as API-format JSON. API format embeds node metadata inline; standard format references external node definitions. Use ComfyUI's "Save (API Format)" option when exporting workflows.
- **Ollama**: Local server at `http://localhost:11434` by default. Override via the `base_url` parameter on Ollama tools. Models must be pre-pulled. Recommended models: `llava` or `minicpm-v` for vision tasks, `llama3.2` or `qwen2.5` for text generation.
- **rembg**: Optional dependency installed via `uv sync --extra rembg`. Downloads BiRefNet model weights on first use. Models are cached locally after initial download.
