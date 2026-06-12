---
name: ollama
description: 通过 ai_data-forge_ollama 工具调用本地 Ollama 进行文本生成、视觉模型图片描述、模型管理和批量处理。
---

# Ollama

Ollama 服务默认 `http://localhost:11434`，可通过 `baseUrl` 参数修改。

## ⚠️ 前置检查

确保 `ai_data-forge_ollama` 工具可用（由 `domains/ai/data-forge/tools/ollama.ts` 注册）。

## 工具调用

使用 `ai_data-forge_ollama` 工具，通过 `subcommand` 参数指定操作。

### `list` — 列出模型

| 参数 | 类型 | 说明 |
|------|------|------|
| `subcommand` | `"list"` | 操作类型 |
| `baseUrl` | `string` | Ollama 地址（默认 http://localhost:11434） |
| `timeout` | `number` | 超时秒数（默认 300） |

### `pull` — 拉取模型

| 参数 | 类型 | 说明 |
|------|------|------|
| `subcommand` | `"pull"` | 操作类型 |
| `model` | `string` | 模型名称（必填，如 `llama3.2`） |
| `baseUrl` | `string` | Ollama 地址 |
| `timeout` | `number` | 超时秒数 |

### `generate` — 文本生成

| 参数 | 类型 | 说明 |
|------|------|------|
| `subcommand` | `"generate"` | 操作类型 |
| `model` | `string` | 模型名称（必填） |
| `prompt` | `string` | 提示词（必填） |
| `system` | `string` | 系统提示词（可选） |
| `temperature` | `number` | 采样温度 0-2（默认 0.7） |
| `baseUrl` | `string` | Ollama 地址 |
| `timeout` | `number` | 超时秒数（默认 300） |

### `describe` — 视觉描述

| 参数 | 类型 | 说明 |
|------|------|------|
| `subcommand` | `"describe"` | 操作类型 |
| `model` | `string` | 视觉模型名称（必填，如 `llava`） |
| `image` | `string` | 图片路径（必填） |
| `prompt` | `string` | 提示词（可选，默认 `Describe this image in detail.`） |
| `baseUrl` | `string` | Ollama 地址 |
| `timeout` | `number` | 超时秒数 |

### `batch-generate` — 批量文本生成

| 参数 | 类型 | 说明 |
|------|------|------|
| `subcommand` | `"batch-generate"` | 操作类型 |
| `model` | `string` | 模型名称（必填） |
| `inputDir` | `string` | 输入目录（含 `.txt` 文件，必填） |
| `outputDir` | `string` | 输出目录（必填） |
| `system` | `string` | 系统提示词（可选） |
| `temperature` | `number` | 采样温度（可选） |
| `baseUrl` | `string` | Ollama 地址 |
| `timeout` | `number` | 超时秒数 |

### `batch-describe` — 批量视觉描述

| 参数 | 类型 | 说明 |
|------|------|------|
| `subcommand` | `"batch-describe"` | 操作类型 |
| `model` | `string` | 视觉模型名称（必填） |
| `inputDir` | `string` | 输入目录（含图片文件，必填） |
| `outputDir` | `string` | 输出目录（必填） |
| `prompt` | `string` | 提示词（可选） |
| `baseUrl` | `string` | Ollama 地址 |
| `timeout` | `number` | 超时秒数 |

## 示例

```jsonc
// 列出模型
{
  "subcommand": "list"
}

// 拉取模型
{
  "subcommand": "pull",
  "model": "llama3.2"
}

// 文本生成
{
  "subcommand": "generate",
  "model": "llama3.2",
  "prompt": "Hello"
}

// 视觉描述
{
  "subcommand": "describe",
  "model": "llava",
  "image": "photo.jpg"
}

// 批量文本生成
{
  "subcommand": "batch-generate",
  "model": "llama3.2",
  "inputDir": "./prompts",
  "outputDir": "./results"
}

// 批量视觉描述
{
  "subcommand": "batch-describe",
  "model": "llava",
  "inputDir": "./images",
  "outputDir": "./captions"
}
```
