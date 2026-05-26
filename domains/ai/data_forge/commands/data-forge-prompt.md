# `/data-forge-prompt` — Prompt & Caption Management

> **This is a guidance document, not an automated execution tool.**
> It instructs AI agents on how to manage prompts and captions for LLM-based image description in AI training pipelines. No LLM inference, API calls, or automated generation is performed by this command directly.

---

## 1. Purpose

Manage the full lifecycle of LLM prompts and captions: generating captions via cloud or local LLMs, refining and cleaning existing captions, executing batch caption operations, and managing prompt templates.

| Sub-command | Description |
|---|---|
| `generate` | Generate captions for images via LLM (cloud or local) |
| `refine` | Clean, improve, or reformat existing captions |
| `batch` | Execute batch caption operations (search, replace, deduplicate) |
| `template` | Manage prompt templates (create, list, compare) |

---

## 2. Usage

```
/data-forge-prompt generate --directory <path> --provider openai|deepseek|ollama [--model <name>] [--keyfile <path>]
/data-forge-prompt refine --directory <path> [--query <pattern>] [--replace <text>]
/data-forge-prompt batch --directory <path> <operation> [options]
/data-forge-prompt template <action> [--name <template-name>] [--provider openai|deepseek|ollama]
```

### Aliases

```
/df-prompt generate --directory ./images --provider ollama --model llava
/df-prompt refine --directory ./captions --query "bad pattern" --replace "good pattern"
/df-prompt batch --directory ./captions deduplicate --strategy keep-first
/df-prompt template create --name factual-v1 --provider openai
```

---

## 3. Parameters

### `generate` parameters

| Parameter | Required | Description |
|---|---|---|
| `--directory` | Yes | Directory containing images to describe. |
| `--provider` | Yes | LLM provider: `openai`, `deepseek`, or `ollama`. |
| `--model` | No | Model name. For Ollama: model tag (e.g., `llava:13b`). For cloud: model ID. Default: provider-specific default. |
| `--keyfile` | No (cloud) | Path to API keyfile. Required for `openai`/`deepseek` providers. Format: JSON with `provider`, `api_key`, `api_base` fields. |
| `--output-dir` | No | Directory for generated captions. Default: `--directory/captions/`. |

### `refine` parameters

| Parameter | Required | Description |
|---|---|---|
| `--directory` | Yes | Directory containing captions to refine. |
| `--query` | No | Regex pattern for `caption_search` to find captions needing refinement. If omitted, all captions are processed. |
| `--replace` | No | Replacement text for `caption_batch_replace`. Requires `--query`. |
| `--re-generate` | No | Re-generate captions matching `--query` via the LLM instead of text replacement. Requires `--provider`. |

### `batch` parameters

| Parameter | Required | Description |
|---|---|---|
| `--directory` | Yes | Directory containing captions. |
| `<operation>` | Yes | One of: `search`, `replace`, `deduplicate`, `stats`, `export`. |
| `--query` | Conditional | Regex pattern for `caption_search`. Required for `search` and `replace`. |
| `--replace-with` | Conditional | Replacement text for `caption_batch_replace`. Required for `replace`. |
| `--strategy` | No | Deduplication strategy: `keep-first` or `keep-last`. Default: `keep-first`. Used with `deduplicate`. |
| `--format` | No | Export format: `json` or `csv`. Default: `json`. Used with `export`. |

### `template` parameters

| Parameter | Required | Description |
|---|---|---|
| `<action>` | Yes | One of: `create`, `list`, `compare`, `test`. |
| `--name` | Conditional | Template name. Required for `create`; optional for `compare`/`test`. |
| `--provider` | No | Target provider for the template: `openai`, `deepseek`, or `ollama`. Determines prompt structure. |
| `--style` | No | Prompt style: `factual`, `creative`, or `technical`. Default: `factual`. |

---

## 4. Execution Steps

### 4.1 `generate` — Generate Captions via LLM

**Cloud LLM (openai/deepseek):**
1. **Validate keyfile** — Confirm `--keyfile` exists and contains valid JSON with `provider`, `api_key`, `api_base`.
2. **Select tool** — `llm_describe_image` for single image; `llm_batch_describe_images` for directory. Prefer batch.
3. **Invoke batch tool** — Pass `input_dir`, `output_dir`, `model`, and `keyfile` parameters.
4. **Validate response** — Check `{"status": "ok"}`. On `"error"`, inspect `message` for API key issues, rate limits, or model availability.
5. **Quality check** — Run `caption_stats` on generated output. Flag empty captions, outlier word counts.

**Local Ollama:**
1. **Check server** — Call `ollama_list_models` to verify Ollama is running and target model is available.
2. **Select tool** — `ollama_describe_image` for single image; `ollama_batch_describe_images` for directory. Prefer batch.
3. **Invoke batch tool** — Pass `input_dir`, `output_dir`, and `model` parameters.
4. **Validate response** — Check `{"status": "ok"}`. On `"error"`, `message` may indicate model not pulled or server connection refused.
5. **Quality check** — Run `caption_stats` on generated output.

### 4.2 `refine` — Clean and Improve Captions

1. **Scope identification** — If `--query` provided, run `caption_search` to identify captions matching the pattern. Report match count.
2. **Text replacement** — If `--replace` provided, run `caption_batch_replace` on matched captions. Preview changes before confirming.
3. **LLM re-generation** — If `--re-generate` specified, identify matched captions' corresponding images and re-run `llm_describe_image` or `ollama_describe_image` with an improved prompt.
4. **Quality check** — Run `caption_stats` post-refinement to verify improvement.
5. **Report** — Present before/after: captions modified, patterns found, quality metrics delta.

### 4.3 `batch` — Batch Caption Operations

**`search`:**
1. Run `caption_search` with `--query` regex pattern.
2. Report matching captions with surrounding context.

**`replace`:**
1. Run `caption_search` with `--query` to confirm matches.
2. Run `caption_batch_replace` with `--query` and `--replace-with`.
3. Report replacements made and affected files.

**`deduplicate`:**
1. Run `caption_deduplicate` with `--strategy`.
2. Report captions removed and retention rate.

**`stats`:**
1. Run `caption_stats` on the directory.
2. Report full distribution: word count, character count, vocabulary, empty files.

**`export`:**
1. Run `caption_export` with `--format` (json/csv).
2. Report output file path and record count.

### 4.4 `template` — Prompt Template Management

**`create`:**
1. Design a prompt template for the specified `--provider` and `--style`.
2. Document the template with: version label, provider, style, creation date, design rationale.
3. Store template (recommend `.md` or `.json` in a `templates/` directory).

**`list`:**
1. Enumerate available prompt templates with their metadata (provider, style, version, date).

**`compare`:**
1. Select two prompt templates and a test image set.
2. Generate captions with both templates via `llm_batch_describe_images` or `ollama_batch_describe_images`.
3. Run `caption_stats` on both outputs and compare: word count distribution, vocabulary diversity, format compliance.

**`test`:**
1. Select a prompt template and a small test image set (10-50 images).
2. Generate captions via the appropriate LLM tool.
3. Run `caption_stats` and `caption_search` on output.
4. Report quality metrics and recommend adjustments.

---

## 5. Output

**Example output (`generate`):**

```
Caption Generation Complete
├── Provider:     ollama
├── Model:        llava:13b
├── Images:       250
├── Generated:    248/250 (2 failed)
├── Output Dir:   ./images/captions/
├── Quality:
│   ├── Mean Words:   14.2
│   ├── Empty:        1
│   └── Outliers:     3 (word count > 50)
└── Status:       ok
```

**Example output (`batch search`):**

```
Search Results: ./captions/
├── Query:        "bad_pattern_\d+"
├── Matches:      17 files
└── See above for matching lines with context
```

**Example output (`template create`):**

```
Template Created: factual-v1
├── Provider:     openai
├── Style:        factual
├── Version:      1.0.0
├── Date:         2026-05-26
└── Prompt:
    "Describe this image in one concise sentence. Include only observable facts:
    main subject, action, setting, and visible objects. Do not include subjective
    opinions, aesthetic judgments, or imagined details. Output: plain text."
```

---

## 6. Provider Selection Guide

| Factor | Cloud LLM (OpenAI/DeepSeek) | Local Ollama |
|---|---|---|
| **Quality** | Higher (state-of-the-art models) | Varies by model (llava, bakllava) |
| **Cost** | Per-token API pricing | Free (local compute) |
| **Speed** | API-dependent, may have rate limits | Local GPU/CPU dependent |
| **Privacy** | Data sent to external API | All data stays local |
| **Setup** | Keyfile required | Ollama server + model pull |
| **Best for** | Production datasets, high quality | Development, experimentation, sensitive data |

---

## 7. Notes

- **No LLM execution.** This command provides guidance only. All LLM inference runs via Data Forge MCP tools on the user's machine.
- **Keyfile format:** JSON with `provider`, `api_key`, and `api_base` fields. The user must create this file — the AI agent must never generate API keys.
- **Ollama setup:** Ollama must be running locally with the target model pulled (`ollama pull <model>`). Verify with `ollama_list_models`.
- **Prompt templates are guidance.** They inform the AI agent how to construct prompts for LLM tools; they are not runtime configurations.
- **Batch operations are preferred.** Always recommend `llm_batch_describe_images` and `ollama_batch_describe_images` over single-image tools for efficiency.
