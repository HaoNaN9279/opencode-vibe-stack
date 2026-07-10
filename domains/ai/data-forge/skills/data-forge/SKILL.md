---
name: data-forge
description: 当用户需要执行ComfyUI任务、图片缩放、图片格式转换、图片填充背景、图片去除背景、标注管理、LLM 生成图片描述时使用
---

# data-forge-tools — AI 训练数据预处理工具集

data-forge-tools 是一套可组合的 AI 训练数据集构建工具，覆盖从图片预处理到标注管理、LLM 描述生成再到 ComfyUI 合成图像的完整管线。

## 工具位置

工具代码位于 Vibe Stack 仓库的 `tools/data-forge/`，具体路径参见规则文件 `~/.config/opencode/rules/vibe-stack-tools.md`（由 `vibe-stack sync` 自动生成）。

## 首次安装

```bash
cd <VIBE_STACK_ROOT>/tools/data-forge
uv sync
```

## 路径规则

**所有文件路径参数必须使用绝对路径**，禁止使用相对路径。

## 工具概览

data-forge-tools 包含 8 个独立工具模块：

| 工具 | CLI 命令 | 用途 |
|------|---------|------|
| **ComfyUI Client** | `uv run --project <VIBE_STACK_ROOT>/tools/data-forge python -m data_forge.comfyui` | 连接 ComfyUI 服务器 |
| **Image Resize** | `... python -m data_forge.resize` | 批量缩放图片 |
| **Image Converter** | `... python -m data_forge.convert` | PNG/JPG/WebP 格式转换 |
| **Background Fill** | `... python -m data_forge.fill_background` | 透明通道填充 |
| **Background Removal** | `... python -m data_forge.remove_bg` | 去除图片背景 |
| **Ollama Client** | `... python -m data_forge.ollama` | 本地模型推理 |
| **LLM Client** | `... python -m data_forge.llm` | OpenAI API 调用 |
| **Caption Editor** | `... python -m data_forge.caption` | 标注管理 |

## 典型工作流

```
resize → [remove-bg] → [convert] → [fill-background] → Ollama / LLM → caption → ComfyUI
```

## CLI 调用方式

所有工具通过统一的 CLI 模式调用：

```bash
uv run --project <VIBE_STACK_ROOT>/tools/data-forge python -m data_forge.<模块> <子命令> [参数]
```

**示例：**

```bash
# 缩放图片
uv run --project <VIBE_STACK_ROOT>/tools/data-forge python -m data_forge.resize \
    --input-dir /path/to/photos --output-dir /path/to/resized --width 1024 --height 1024

# 查询 ComfyUI 服务器状态
uv run --project <VIBE_STACK_ROOT>/tools/data-forge python -m data_forge.comfyui status
```

## 注意事项

- `<VIBE_STACK_ROOT>` 的准确值见 `~/.config/opencode/rules/vibe-stack-tools.md`
