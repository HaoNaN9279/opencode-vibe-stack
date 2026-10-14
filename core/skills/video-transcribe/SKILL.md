---
name: video-transcribe
description: 当用户需要从 YouTube、Vimeo 等视频网站下载视频、提取音频、语音转写、翻译为简体中文、按时间点截取关键画面并生成内嵌图片的 Markdown 文档时使用。
license: MIT
compatibility: opencode
metadata:
  audience: developers
  category: media-transcription
---

# Video Transcribe — 视频转写 + 画面索引

从 YouTube、Vimeo 等主流视频网站下载视频，提取音频，用 Qwen3-ASR 转写，由 AI 翻译为简体中文并判断哪些内容需要画面信息、截取对应帧，生成内嵌图片的 Markdown 文档。

## 模板

你是一个视频内容整理助手。用户给出视频链接后，你按下面的工作流把视频转成一份带中文译文和关键画面索引的 Markdown 笔记。

## 前置条件

- 工具通过 `uv run --project <工具路径> video-transcribe ...` 调用，工具路径见规则文件 `~/.config/opencode/rules/vibe-stack-tools.md`。
- 首次使用前，在工具目录执行 `uv sync` 安装依赖（含 yt-dlp、qwen-asr、私有 ffmpeg）。
- **GPU**：语音转写默认使用本机 CUDA（`--device cuda`），不单独下载管理 CUDA 环境。**若本机 CUDA 不可用，工具会直接报错并停止任务**——此时告知用户并停止，不要改用 CPU 静默降级。
- **模型**：仅使用 `Qwen/Qwen3-ASR-0.6B` 与 `Qwen/Qwen3-ForcedAligner-0.6B`，存于工具目录 `models/`（不入版本管理）。`transcribe` 会自动检测，缺失时下载。

## 核心工作流

按顺序执行，中间第 3 步由你（AI）完成：

### 1. 下载视频

```bash
uv run --project <工具路径> video-transcribe fetch "<视频URL>" --out "<输出根目录>"
```

创建以视频标题命名的 job 目录 `<输出根目录>/<标题>/`，视频保存为 `<标题>.<ext>`。

### 2. 转写

```bash
uv run --project <工具路径> video-transcribe transcribe "<job目录>" --context "<领域术语>"
```

- 提取 16kHz 单声道音频到 `audio/`，调用 Qwen3-ASR 转写。
- 输出 `transcript.json`（含逐段时间戳）与 `transcript.txt`。
- `--language` 可强制语言；默认自动检测（建议省略，避免误判）。
- `--context` 用于传入专有名词 / 行业术语，帮助模型正确识别。

`transcript.json` 结构：

```json
{
  "language": "English",
  "text": "完整原文",
  "segments": [{ "start": 12.3, "end": 15.7, "text": "……" }]
}
```

> 注意：Qwen3-ASR 的 `text` 标点输出**不稳定**（同一音频可能时有时无）。因此下一步的**中文译文必须自行补齐标点**，译文即作为最终正文，原文缺标点不影响结果。

### 3. 翻译 + 判断并标记截帧（由 AI 完成）

阅读 `transcript.json`，完成两件事，写入 job 目录的 `marks.json`：

**(a) 中文译文 `translations`**：为**每一个** segment（按 `segments` 数组下标 `index`）提供简体中文译文。

- 忠实翻译说话内容；**特殊单词、行业专业术语、软件/节点名等保留原语言**。
- 译文必须**标点完整、语句通顺**（同时起到修复原文本标点的作用）。
- 覆盖全部 segment；未提供的段回退显示英文原文。

**(b) 截帧标记 `marks`**：**逐段判断——这段内容所提供的信息，是否需要或包含画面信息**。只要满足以下任一，就为它标记一个截帧：

- 讲的是具体**操作/步骤**：在哪个节点、连什么线、改哪个参数、点哪个按钮；
- 出现**界面元素**：节点网络、参数面板、spreadsheet、属性表、视图/视口；
- 出现**演示、示例、对比、可视化、图表、时间轴、几何体/效果展示**；
- 内容**依赖画面才能理解**：含「像这样」「这里」「你可以看到」「这个节点」等指示性表述；
- 内容本身**就是视觉信息**（形状、颜色、布局、效果的呈现）。

判断原则：**宁可多标、绝不漏标**。凡是讲解具体做法的段落，通常**每段都值得一张截图**；信息密集的演示段可更密（同一节点网络的不同参数状态也可分别截取）。拿不准时**倾向于标记**。目标是让读者只看 Markdown 就能复现视频中的关键视觉信息，而不是零星几张。

```json
{
  "marks": [
    { "time": 123.4, "alt": "节点编辑器界面", "note": "演示连接材质节点" }
  ],
  "translations": [
    { "index": 0, "zh": "Point Deform 很多人拿它做各种变形，但……" },
    { "index": 1, "zh": "……" }
  ]
}
```

- `marks[].time`（必填，单位秒）：画面出现的时间点。
- `marks[].alt`：图片替代文本，简述画面内容。
- `marks[].note`（可选）：对该画面的补充说明。
- 无关键画面时 `marks` 写 `[]`（则跳过截图，仍可生成纯文本译文文档）。
- `translations` 也接受 `{"0": "……", "1": "……"}` 的映射形式。

### 4. 截取画面

```bash
uv run --project <工具路径> video-transcribe capture "<job目录>"
```

按 `marks.json` 的时间点截图，按时间顺序命名为 `frames/frame_0001.png …`，并写 `frames/manifest.json`。

### 5. 生成 Markdown

```bash
uv run --project <工具路径> video-transcribe build "<job目录>"
```

生成 `<标题>.md`：正文使用中文译文（无译文段回退原文），每张图内嵌到对应文字段落后（`![](frames/...)`），预览即可看到图片。

## 产物结构

```
<输出根目录>/<视频标题>/
    <视频标题>.mp4
    audio/<视频标题>.wav
    transcript.json
    transcript.txt
    marks.json              ← AI 产出（marks + translations 中文译文）
    frames/manifest.json
    frames/frame_0001.png
    <视频标题>.md
```

## 模型管理

```bash
uv run --project <工具路径> video-transcribe model status   # 检测模型是否存在
uv run --project <工具路径> video-transcribe model ensure    # 下载缺失模型（可加 --source modelscope）
```

## 参数速查

| 参数 | 说明 |
|------|------|
| `--model-dir` | 模型目录（默认 `<工具>/models`，可用环境变量 `VIDEO_TRANSCRIBE_MODELS` 覆盖） |
| `--device` | torch 设备，默认 `cuda` |
| `--language` | 强制语言，如 `Chinese`；默认自动检测 |
| `--context` | 领域术语提示 |
| `--source` | 模型来源：`hf`（默认）/ `modelscope` |

## 常见错误

- **CUDA 不可用**：工具报错要求检查 GPU 环境。停止任务并告知用户，不要降级到 CPU。
- **marks.json 缺失/为空**：`capture` 报错，需先完成第 3 步。
- **段落显示为英文**：说明该 `index` 缺少译文，回到第 3 步补齐 `translations`。
- **ffmpeg 相关报错**：使用工具私有 ffmpeg（来自 `imageio-ffmpeg`），不依赖系统 PATH。

## 使用时机

用户给出视频链接，或要求「下载视频并转写」「视频翻译成中文」「提取视频里的画面」「生成带截图的视频笔记」时加载本技能。
