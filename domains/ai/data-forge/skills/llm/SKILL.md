---
name: llm
description: 通过 ai_data-forge_llm 工具调用 OpenAI 兼容 API，支持多提供商文本生成、图片描述、批量处理和提供商管理。
---

# LLM

需要 API keyfile（JSON），通过 `keyfile` 参数或 `KEYFILE` 环境变量指定。

Keyfile 格式：
```json
{"openai": {"api_key": "sk-...", "base_url": "https://api.openai.com/v1"}}
```

## 前置检查
确认 `ai_data-forge_llm` 工具已注册（位于 `.opencode/tools/ai_data-forge_llm.ts`）。该工具由领域激活时自动注册。

## 用法

使用 `ai_data-forge_llm` 工具，通过 `subcommand` 参数选择操作。

### `chat` — 单轮对话
- 必填：`subcommand: "chat"` `prompt` `provider` `model`
- 可选：`keyfile` `system` `temperature`（默认 0.7） `maxTokens`

### `describe` — 图片描述
- 必填：`subcommand: "describe"` `image` `provider` `model`
- 可选：`keyfile` `prompt` `temperature` `maxTokens`

### `batch-chat` — 批量对话
- 必填：`subcommand: "batch-chat"` `inputDir` `outputDir` `provider` `model`
- 可选：`keyfile` `system` `temperature` `maxTokens`

### `batch-describe` — 批量图片描述
- 必填：`subcommand: "batch-describe"` `inputDir` `outputDir` `provider` `model`
- 可选：`keyfile` `prompt` `temperature` `maxTokens`

### `list-providers` — 列出已配置的提供商
- 必填：`subcommand: "list-providers"`
- 可选：`keyfile`
