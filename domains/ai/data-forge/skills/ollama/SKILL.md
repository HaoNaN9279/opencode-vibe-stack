---
name: ollama
description: 通过 DataForge CLI 调用本地 Ollama 进行文本生成、视觉模型图片描述、模型管理和批量处理。
---

# Ollama

Ollama 服务默认 `http://localhost:11434`，可通过 `--base-url` 修改。

## ⚠️ 前置检查
```
data-forge --help
```
未安装：`git clone https://github.com/HaoNan9279/DataForge.git && cd DataForge && uv sync`

## 命令

### `ollama list` — 列出模型
- `--base-url` (默认 http://localhost:11434) | `--timeout` (默认 300.0)
```
data-forge ollama list
```

### `ollama pull` — 拉取模型
- `--name` (必填) | `--base-url` | `--timeout`
```
data-forge ollama pull --name llama3.2
```

### `ollama generate` — 文本生成
- `--prompt` `--model` (必填)
- `--system` | `--temperature` (默认 0.7) | `--base-url` | `--timeout` (默认 300.0)
```
data-forge ollama generate --prompt "Hello" --model llama3.2
```

### `ollama describe` — 视觉描述
- `--image` `--model` (必填)
- `--prompt` (默认 Describe this image in detail.) | `--base-url` | `--timeout`
```
data-forge ollama describe --image photo.jpg --model llava
```

### `ollama batch-generate` — 批量文本生成
- `--input-dir` `--output-dir` `--model` (必填)
- `--system` `--temperature` `--base-url` `--timeout`
```
data-forge ollama batch-generate --input-dir ./prompts --output-dir ./results --model llama3.2
```

### `ollama batch-describe` — 批量视觉描述
- `--input-dir` `--output-dir` `--model` (必填)
- `--prompt` `--base-url` `--timeout`
```
data-forge ollama batch-describe --input-dir ./images --output-dir ./captions --model llava
```
