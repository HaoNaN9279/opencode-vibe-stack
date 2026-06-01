# `/data-forge-prompt` — 提示与描述管理

> **这是一份指导文档，而非自动化执行工具。**
> 它指导 AI 智能体如何管理 AI 训练流水线中基于 LLM 的图像描述的提示和描述。此命令不直接执行任何 LLM 推理、API 调用或自动生成。

---

## 1. 用途

管理 LLM 提示和描述的完整生命周期：通过云端或本地 LLM 生成描述、优化和清理现有描述、执行批量描述操作以及管理提示模板。

| 子命令 | 描述 |
|---|---|
| `generate` | 通过 LLM（云端或本地）为图像生成描述 |
| `refine` | 清理、改进或重新格式化现有描述 |
| `batch` | 执行批量描述操作（搜索、替换、去重） |
| `template` | 管理提示模板（创建、列出、比较） |

---

## 2. 用法

```
/data-forge-prompt generate --directory <path> --provider openai|deepseek|ollama [--model <name>] [--keyfile <path>]
/data-forge-prompt refine --directory <path> [--query <pattern>] [--replace <text>]
/data-forge-prompt batch --directory <path> <operation> [options]
/data-forge-prompt template <action> [--name <template-name>] [--provider openai|deepseek|ollama]
```

### 别名

```
/df-prompt generate --directory ./images --provider ollama --model llava
/df-prompt refine --directory ./captions --query "bad pattern" --replace "good pattern"
/df-prompt batch --directory ./captions deduplicate --strategy keep-first
/df-prompt template create --name factual-v1 --provider openai
```

---

## 3. 参数

### `generate` 参数

| 参数 | 是否必需 | 描述 |
|---|---|---|
| `--directory` | 是 | 包含需要描述的图像的目录。 |
| `--provider` | 是 | LLM 供应商：`openai`、`deepseek` 或 `ollama`。 |
| `--model` | 否 | 模型名称。对于 Ollama：模型标签（例如 `llava:13b`）。对于云端：模型 ID。默认值：供应商特定默认值。 |
| `--keyfile` | 否（云端） | API keyfile 路径。`openai`/`deepseek` 供应商必需。格式：包含 `provider`、`api_key`、`api_base` 字段的 JSON。 |
| `--output-dir` | 否 | 生成描述的目录。默认值：`--directory/captions/`。 |

### `refine` 参数

| 参数 | 是否必需 | 描述 |
|---|---|---|
| `--directory` | 是 | 包含需要优化描述的目录。 |
| `--query` | 否 | 用于 `caption_search` 的正则表达式模式，用于查找需要优化的描述。如果省略，则处理所有描述。 |
| `--replace` | 否 | `caption_batch_replace` 的替换文本。需要 `--query`。 |
| `--re-generate` | 否 | 通过 LLM 重新生成匹配 `--query` 的描述，而非文本替换。需要 `--provider`。 |

### `batch` 参数

| 参数 | 是否必需 | 描述 |
|---|---|---|
| `--directory` | 是 | 包含描述的目录。 |
| `<operation>` | 是 | 以下之一：`search`、`replace`、`deduplicate`、`stats`、`export`。 |
| `--query` | 条件性 | 用于 `caption_search` 的正则表达式模式。`search` 和 `replace` 需要此参数。 |
| `--replace-with` | 条件性 | `caption_batch_replace` 的替换文本。`replace` 需要此参数。 |
| `--strategy` | 否 | 去重策略：`keep-first` 或 `keep-last`。默认值：`keep-first`。用于 `deduplicate`。 |
| `--format` | 否 | 导出格式：`json` 或 `csv`。默认值：`json`。用于 `export`。 |

### `template` 参数

| 参数 | 是否必需 | 描述 |
|---|---|---|
| `<action>` | 是 | 以下之一：`create`、`list`、`compare`、`test`。 |
| `--name` | 条件性 | 模板名称。`create` 必需；`compare`/`test` 可选。 |
| `--provider` | 否 | 模板的目标供应商：`openai`、`deepseek` 或 `ollama`。决定提示结构。 |
| `--style` | 否 | 提示风格：`factual`、`creative` 或 `technical`。默认值：`factual`。 |

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
