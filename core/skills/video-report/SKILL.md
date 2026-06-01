---
name: video-report
description: 使用 yt-dlp、ffmpeg、whisper 自动化处理网络视频，提取关键帧和文字转录，生成结构化的视频内容分析报告
---

# Video Report — 视频内容分析报告生成器

自动化处理网络视频：下载视频与音频、提取关键帧、语音转文字，最终将视觉与文字内容融合为一份结构化报告。

## 模板

你是一位视频内容分析师。掌握 yt-dlp、ffmpeg、whisper 三个核心工具的使用。工作方式是：下载 → 提取关键帧 → 转录音频 → 融合生成报告。

## 前置条件

以下工具需要在系统上预先安装：

| 工具 | 用途 | 安装验证 |
|------|------|---------|
| `yt-dlp` | 从网络下载视频及音频 | `yt-dlp --version` |
| `ffmpeg` | 视频/音频处理，提取关键帧 | `ffmpeg -version` |
| `ffprobe` | 获取视频元信息（随 ffmpeg 安装） | `ffprobe -version` |
| `whisper` | 语音转文字 | `python -c "import whisper; print(whisper.__version__)"` |

开始工作前先检查所需工具是否安装并可用，如果有任一工具缺失，则停止当前任务并提示用户安装。

## 核心工作流

工作流分为 5 个步骤，按顺序执行。

### 第 1 步：下载视频

使用 `yt-dlp` 下载指定 URL 的视频，选择合适的画质。

```bash
# 下载最佳画质的视频，保存为 video.mp4
yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" `
  -o "video.%(ext)s" <URL>

# 如果不需要最高画质，"bv*+ba/b" 会自动选择合适组合
yt-dlp -f "bv*+ba/b" -o "video.%(ext)s" <URL>
```

关键参数说明：

| 参数 | 用途 |
|------|------|
| `-f, --format` | 指定视频格式选择策略 |
| `-o, --output` | 输出文件名模板 |
| `--write-info-json` | （可选）同时下载视频元数据 JSON |
| `--write-thumbnail` | （可选）同时下载视频缩略图 |

### 第 2 步：提取音频

使用 `yt-dlp` 的音频提取功能，或直接使用 `ffmpeg` 从已下载的视频中提取。

**方式 A — 下载时直接提取音频：**

```bash
yt-dlp -f "bestaudio/best" -x --audio-format mp3 `
  -o "audio.%(ext)s" <URL>
```

**方式 B — 从已下载的视频中提取（推荐）：**

```bash
ffmpeg -i video.mp4 -vn -acodec libmp3lame -q:a 2 audio.mp3
```

| 参数 | 用途 |
|------|------|
| `-vn` | 禁用视频流，只保留音频 |
| `-acodec libmp3lame` | 使用 MP3 编码 |
| `-q:a 2` | 音频质量（0=最好，9=最差，2 为高质量） |

### 第 3 步：提取关键帧

**方式 A — 按固定间隔抽取（推荐）：**

```bash
# 每秒提取一帧
ffmpeg -i video.mp4 -vf "fps=1" -q:v 2 frames/frame_%04d.jpg
```

**方式 B — 按场景变化抽取（智能选帧）：**

```bash
# 场景切换时提取关键帧，只保留关键帧本身
ffmpeg -i video.mp4 -vf "select='gt(scene,0.4)',showinfo" `
  -vsync vfr -q:v 2 frames/frame_%04d.jpg
```

`scene` 参数值（0.0~1.0）控制检测灵敏度：值越小检测越敏感（产生更多帧），值越大只捕获明显场景切换。

抽取前建议先用 `ffprobe` 获取视频基本信息，以合理设置帧间隔：

```bash
ffprobe -v error -show_entries stream=duration,r_frame_rate -of default=noprint_wrappers=1 video.mp4
```

| 参数 | 用途 |
|------|------|
| `-vf "fps=1"` | 每秒提取一帧 |
| `-vf "select='gt(scene,0.4)'"` | 按场景变化选择帧 |
| `-vsync vfr` | 可变帧率模式，只输出选中的帧 |
| `-q:v 2` | JPEG 质量（1=最好，31=最差，2 为高质量） |

### 第 4 步：音频转文字

使用 `whisper` 将上一步提取的音频转换为文字。

```bash
# 使用 base 模型（推荐平衡点）
python -m whisper audio.mp3 --model base --language zh `
  --output_format txt

# 指定输出格式为 srt（字幕）和 txt，便于对时间轴
python -m whisper audio.mp3 --model base --language zh `
  --output_format srt --output_dir ./

# 英文视频
python -m whisper audio.mp3 --model base --language en `
  --output_format txt
```

| 参数 | 用途 |
|------|------|
| `--model` | 模型尺寸：`tiny`/`base`/`small`/`medium`/`large` |
| `--language` | 指定音频语言代码（如 `zh`、`en`、`ja`） |
| `--output_format` | 输出格式：`txt`（纯文本）、`srt`（字幕）、`vtt`、`tsv`、`json` |
| `--output_dir` | 输出目录 |
| `--task` | `transcribe`（转录，默认）或 `translate`（翻译为英文） |

whisper 会输出与音频同名的 `.txt` 文件（或 `.srt` 等），可直接读取。

### 第 5 步：融合生成报告

将关键帧图像与文字转录内容结合，生成结构化的视频分析报告。

**报告内容结构：**

1. **视频元信息** — 标题、时长、来源 URL 等
2. **内容摘要** — 基于转录文本的自动摘要
3. **章节划分** — 根据转录内容将视频划分为逻辑段落
4. **关键帧与文字对照** — 每个关键帧对应的时间点及其上下文转录文字
5. **核心观点提炼** — 提取视频中最重要的 3-5 个观点/结论
6. **完整转录** — 全文转录文本附录

**生成方式：**

- 读取转录文本文件（`audio.txt`）
- 读取关键帧图像列表，用 `ffprobe` 或通过帧序号推断时间戳
- 将文字内容按段落分段，匹配对应时间区间内的关键帧
- 使用 `Write` 工具输出一份结构化的 Markdown 报告文件

> **提示**：时间戳通过帧文件名推算：`frame_0012.jpg` 若按 `fps=1` 抽取，则对应第 12 秒。更精确的做法是用 `ffprobe` 读取每帧的 pts 时间。

## 参数

当用户调用此技能时，可能需要提供以下参数：

| 参数 | 说明 | 必填 |
|------|------|------|
| `url` | 要下载的视频 URL | 是 |
| `keyframe_mode` | 关键帧提取模式（`interval` 或 `scene`），默认 `interval` | 是 |
| `language` | 音频语言（如 `zh`、`en`），默认自动检测 | 否 |
| `model` | whisper 模型大小（`tiny`/`base`/`small`/`medium`/`large`），默认 `base` | 否 |
| `fps` | 关键帧提取频率（帧/秒），默认 `1` | 否 |
| `output_dir` | 输出目录，默认当前工作目录 | 否 |

## 使用时机

在以下场景应该加载此技能：

- 用户要求分析网络视频内容
- 需要从视频中提取文字信息并生成结构化报告
- 涉及 yt-dlp、ffmpeg、whisper 三个工具联动的任务
- 用户需要视频内容摘要、关键帧截图、章节划分等分析产出

## 错误处理指南

### yt-dlp 常见问题

| 错误 | 原因 | 处理方式 |
|------|------|---------|
| `HTTP Error 403` | 视频源限制访问 | 尝试添加 `--user-agent` 或使用 cookies |
| `No video formats found` | 格式不可用 | 使用 `-F` 列出可用格式，选择兼容格式 |
| 下载中断 | 网络不稳定 | 添加 `--continue`（默认启用）恢复下载 |

### ffmpeg 常见问题

| 错误 | 原因 | 处理方式 |
|------|------|---------|
| `Output file already exists` | 输出文件已存在 | 添加 `-y` 覆盖或 `-n` 跳过 |
| `Invalid data found when processing` | 输入文件损坏或格式不兼容 | 检查视频文件是否完整下载 |
| 帧提取数量异常 | fps/select 参数不合适 | 先用 `ffprobe` 检查视频时长和帧率 |

### whisper 常见问题

| 错误 | 原因 | 处理方式 |
|------|------|---------|
| `Model not found` | 首次使用未下载模型 | 自动下载，确保网络连接正常 |
| `Out of memory` | 模型太大或音频太长 | 切换到小模型（`tiny`/`base`）或分段处理 |
| 转录质量差 | 背景噪音或语言不匹配 | 指定正确的 `--language`，或使用更大的模型 |
