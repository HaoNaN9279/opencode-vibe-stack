---
name: llm
description: 通过 DataForge CLI 调用 OpenAI 兼容 API，支持多提供商文本生成、图片描述、批量处理和提供商管理。
---

# LLM

需要 API keyfile（JSON），通过 `--keyfile` 或 `KEYFILE` 环境变量指定。

Keyfile 格式：
```json
{"openai": {"api_key": "sk-...", "base_url": "https://api.openai.com/v1"}}
```

## ⚠️ 前置检查
```
data-forge --help
```
未安装：`git clone https://github.com/HaoNan9279/DataForge.git && cd DataForge && uv sync`

## 命令

### `llm chat` — 单轮对话
- `--prompt` `--provider` `--model` (必填)
- `--keyfile` | `--system` | `--temperature` (默认 0.7) | `--max-tokens`
```
data-forge llm chat --prompt "Hello" --provider openai --model gpt-4o --keyfile keys.json
```

### `llm describe` — 图片描述
- `--image` `--provider` `--model` (必填)
- `--keyfile` | `--prompt` | `--temperature` | `--max-tokens`
```
data-forge llm describe --image photo.jpg --provider openai --model gpt-4o --keyfile keys.json
```

### `llm batch-chat` — 批量对话
- `--input-dir` `--output-dir` `--provider` `--model` (必填)
- `--keyfile` `--system` `--temperature` `--max-tokens`
```
data-forge llm batch-chat --input-dir ./prompts --output-dir ./results --provider openai --model gpt-4o
```

### `llm batch-describe` — 批量图片描述
- `--input-dir` `--output-dir` `--provider` `--model` (必填)
- `--keyfile` `--prompt` `--temperature` `--max-tokens`
```
data-forge llm batch-describe --input-dir ./images --output-dir ./captions --provider openai --model gpt-4o
```

### `llm list-providers` — 列出已配置的提供商
- `--keyfile`
```
data-forge llm list-providers --keyfile keys.json
```
