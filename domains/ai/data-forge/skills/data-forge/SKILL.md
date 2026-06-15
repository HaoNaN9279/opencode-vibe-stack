---
name: data-forge
description: DataForge 数据锻造工具集 — 图片预处理、标注管理、LLM 生成、ComfyUI 合成
---

# DataForge — AI 训练数据管线工具集

DataForge 是一套可组合的 AI 训练数据集构建工具，覆盖从图片预处理到标注管理、LLM 描述生成再到 ComfyUI 合成图像的完整管线。

仓库：https://github.com/HaoNaN9279/data_forge.git

## 前置检查

使用本领域任何工具前，确保 DataForge submodule 已初始化并安装依赖：

```bash
# 初始化 submodule
git submodule update --init --recursive

# 安装 Python 依赖
cd domains/ai/data-forge/skills/data-forge
uv sync
```

DataForge submodule 位于 `domains/ai/data-forge/skills/data-forge/`，Python 源码位于其下的 `src/data_forge/`。

## 工具概览

DataForge 包含 8 个独立工具模块，每个工具的详细用法见对应参考文档：

| 工具 | 模块 | 用途 | 详细参考 |
|------|------|------|----------|
| **ComfyUI Client** | `comfyui` | 连接本地 ComfyUI 服务器，提交工作流、追踪执行、下载生成图片 | [comfyui.md](comfyui.md) |
| **Image Resize** | `resize` | 批量缩放图片，支持精确尺寸、长边适配与填充模式 | [resize.md](resize.md) |
| **Image Converter** | `convert` | PNG / JPG / WebP / BMP 格式互转，支持单张与批量模式 | [convert.md](convert.md) |
| **Background Fill** | `fill_background` | 给带透明通道的图片填充指定颜色背景，始终输出 RGB | [fill-background.md](fill-background.md) |
| **Background Removal** | `remove_bg` | 使用 BiRefNet 模型（rembg）去除图片背景 | [remove-bg.md](remove-bg.md) |
| **Ollama Client** | `ollama` | 本地模型推理 — 文本生成与视觉模型图片描述 | [ollama.md](ollama.md) |
| **LLM Client** | `llm` | 通过 OpenAI 兼容 API 调用云端大模型进行文本生成与图片描述 | [llm.md](llm.md) |
| **Caption Editor** | `caption` | 批量管理 `.txt` 标注文件，支持创建、搜索、替换、导入导出、去重、统计 | [caption.md](caption.md) |

## 典型工作流

DataForge 工具按以下管线组合使用，方括号内为可选步骤：

```
resize → [remove-bg] → [convert] → [fill-background] → Ollama / LLM → caption → ComfyUI
```

**流程说明：**

1. **`resize`** — 将原始图片统一缩放至目标尺寸
2. **`remove-bg`**（可选） — 去除背景，提取主体
3. **`convert`**（可选） — 统一图片格式（如全部转为 PNG 或 JPG）
4. **`fill-background`**（可选） — 为透明通道图片填充指定颜色背景，确保输出 RGB
5. **`Ollama` 或 `LLM`** — 使用本地模型或云端大模型为图片生成描述文本
6. **`caption`** — 管理、清理、批量编辑生成的标注文件
7. **`ComfyUI`** — 使用标注文本作为提示词，生成合成图像

## CLI 调用方式

所有工具通过统一的 CLI 模式调用：

```bash
uv run --directory domains/ai/data-forge/skills/data-forge python -m data_forge.<工具模块> <子命令> [参数]
```

| 部分 | 说明 |
|------|------|
| `--directory` | 指向 DataForge submodule 所在路径 |
| `python -m data_forge.<模块>` | 以模块方式运行指定工具 |
| `<子命令>` | 各工具支持的子命令，详见对应参考文档 |

**示例：**

```bash
# 缩放图片
uv run --directory domains/ai/data-forge/skills/data-forge python -m data_forge.resize \
    --input-dir ./photos --output-dir ./resized --width 1024 --height 1024

# 查询 ComfyUI 服务器状态
uv run --directory domains/ai/data-forge/skills/data-forge python -m data_forge.comfyui status
```

各工具的具体参数、子命令和用法请查阅对应的参考文档。
