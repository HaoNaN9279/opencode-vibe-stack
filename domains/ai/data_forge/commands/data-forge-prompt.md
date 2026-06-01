---
description: 管理 LLM 提示和描述的完整生命周期：生成、优化、批量操作和提示模板管理
---

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

## 4. 执行步骤

### 4.1 `generate` — 通过 LLM 生成描述

**云端 LLM（openai/deepseek）：**
1. **验证 keyfile** — 确认 `--keyfile` 存在且包含有效的 JSON，包含 `provider`、`api_key`、`api_base` 字段。
2. **选择工具** — 单张图像使用 `llm_describe_image`；目录使用 `llm_batch_describe_images`。优先使用批处理。
3. **调用批处理工具** — 传递 `input_dir`、`output_dir`、`model` 和 `keyfile` 参数。
4. **验证响应** — 检查 `{"status": "ok"}`。如果返回 `"error"`，检查 `message` 中是否有 API 密钥问题、速率限制或模型不可用。
5. **质量检查** — 对生成的输出运行 `caption_stats`。标记空描述和异常词数。

**本地 Ollama：**
1. **检查服务器** — 调用 `ollama_list_models` 验证 Ollama 正在运行且目标模型可用。
2. **选择工具** — 单张图像使用 `ollama_describe_image`；目录使用 `ollama_batch_describe_images`。优先使用批处理。
3. **调用批处理工具** — 传递 `input_dir`、`output_dir` 和 `model` 参数。
4. **验证响应** — 检查 `{"status": "ok"}`。如果返回 `"error"`，`message` 可能指示模型未拉取或服务器连接被拒绝。
5. **质量检查** — 对生成的输出运行 `caption_stats`。

### 4.2 `refine` — 清理和改进描述

1. **范围识别** — 如果提供了 `--query`，运行 `caption_search` 识别匹配该模式的描述。报告匹配数量。
2. **文本替换** — 如果提供了 `--replace`，对匹配的描述运行 `caption_batch_replace`。确认前预览更改。
3. **LLM 重新生成** — 如果指定了 `--re-generate`，识别匹配描述对应的图像，使用改进的提示词重新运行 `llm_describe_image` 或 `ollama_describe_image`。
4. **质量检查** — 优化后运行 `caption_stats` 以验证改进效果。
5. **报告** — 呈现前后对比：修改的描述数、找到的模式、质量指标变化。

### 4.3 `batch` — 批量描述操作

**`search`：**
1. 使用 `--query` 正则表达式模式运行 `caption_search`。
2. 报告匹配的描述及上下文。

**`replace`：**
1. 使用 `--query` 运行 `caption_search` 确认匹配项。
2. 使用 `--query` 和 `--replace-with` 运行 `caption_batch_replace`。
3. 报告所做的替换和受影响的文件。

**`deduplicate`：**
1. 使用 `--strategy` 运行 `caption_deduplicate`。
2. 报告移除的描述数和保留率。

**`stats`：**
1. 对目录运行 `caption_stats`。
2. 报告完整分布：词数、字符数、词汇量、空文件。

**`export`：**
1. 使用 `--format`（json/csv）运行 `caption_export`。
2. 报告输出文件路径和记录数。

### 4.4 `template` — 提示模板管理

**`create`：**
1. 为指定的 `--provider` 和 `--style` 设计一个提示模板。
2. 文档化模板：版本标签、供应商、风格、创建日期、设计理由。
3. 存储模板（建议在与命令文件同级的 `.md` 或 `.json` 文件中）。

**`list`：**
1. 枚举可用的提示模板及其元数据（供应商、风格、版本、日期）。

**`compare`：**
1. 选择两个提示模板和一组测试图像。
2. 通过 `llm_batch_describe_images` 或 `ollama_batch_describe_images` 使用两个模板分别生成描述。
3. 对两个输出运行 `caption_stats` 并比较：词数分布、词汇多样性、格式合规性。

**`test`：**
1. 选择一个提示模板和一小批测试图像（10-50 张）。
2. 通过相应的 LLM 工具生成描述。
3. 对输出运行 `caption_stats` 和 `caption_search`。
4. 报告质量指标并建议调整。

---

## 5. 输出

**示例输出（`generate`）：**

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

**示例输出（`batch search`）：**

```
Search Results: ./captions/
├── Query:        "bad_pattern_\d+"
├── Matches:      17 files
└── See above for matching lines with context
```

**示例输出（`template create`）：**

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

## 6. 供应商选择指南

| 因素 | 云端 LLM（OpenAI/DeepSeek） | 本地 Ollama |
|---|---|---|
| **质量** | 更高（最先进模型） | 因模型而异（llava、bakllava） |
| **成本** | 按 Token 计费的 API 定价 | 免费（本地计算） |
| **速度** | 依赖 API，可能有速率限制 | 依赖本地 GPU/CPU |
| **隐私** | 数据发送至外部 API | 所有数据保留在本地 |
| **设置** | 需要 Keyfile | Ollama 服务器 + 模型拉取 |
| **最适合** | 生产数据集、高质量 | 开发、实验、敏感数据 |

---

## 7. 说明

- **不执行 LLM。** 此命令仅提供指导。所有 LLM 推理通过 Data Forge MCP 工具在用户机器上运行。
- **Keyfile 格式：** 包含 `provider`、`api_key` 和 `api_base` 字段的 JSON。用户必须自行创建此文件——AI 智能体绝不能生成 API 密钥。
- **Ollama 设置：** Ollama 必须在本地运行且已拉取目标模型（`ollama pull <model>`）。使用 `ollama_list_models` 验证。
- **提示模板是指导性的。** 它们告知 AI 智能体如何为 LLM 工具构建提示词，而非运行时配置。
- **优先使用批量操作。** 始终推荐 `llm_batch_describe_images` 和 `ollama_batch_describe_images` 而非单张图像工具以提高效率。
