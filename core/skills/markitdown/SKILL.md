---
name: markitdown
description: 当用户需要将 PDF、Word、Excel、PPT、HTML、图片、音频等文件转换为 Markdown 格式时使用。支持 CLI 和 Python API 两种调用方式，通过 uv 管理虚拟环境。
license: MIT
compatibility: opencode
metadata:
  audience: developers
  category: document-conversion
---

# MarkItDown — 文档转 Markdown 工具

Microsoft MarkItDown 是一个轻量级 Python 工具，将各种文件格式转换为 Markdown，用于 LLM 和文本分析管线。

支持的文件格式：PDF、PowerPoint、Word、Excel、图片（EXIF/OCR）、音频、HTML、CSV/JSON/XML、ZIP、YouTube 链接、EPub 等。

## 项目位置

skill 所在目录即为项目根目录，git submodule 位于 `repo/` 下：

```
~/.config/opencode/skills/markitdown/
  ├── SKILL.md
  └── repo/packages/markitdown/    # markitdown 源码 + 虚拟环境
```

## 核心工作流

### 1. CLI 方式（推荐快速转换）

```bash
# 进入 markitdown 包目录
cd ~/.config/opencode/skills/markitdown/repo/packages/markitdown

# 转换文件到 stdout
uv run markitdown path/to/file.pdf

# 转换文件并保存到文件
uv run markitdown path/to/file.pdf -o output.md

# 从 stdin 读取
cat path/to/file.pdf | uv run markitdown

# 指定文件扩展名（stdin 模式时使用）
uv run markitdown -x .docx < file.bin

# 查看版本
uv run markitdown --version
```

### 2. Python API 方式（需要在代码中使用时）

```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("path/to/file.xlsx")
print(result.text_content)

# 使用 LLM 进行图片描述
from openai import OpenAI
client = OpenAI()
md = MarkItDown(llm_client=client, llm_model="gpt-4o")
result = md.convert("example.jpg")
print(result.text_content)
```

### 3. Python API — 安全调用（建议用于服务端）

```python
from markitdown import MarkItDown

md = MarkItDown()
# 仅限本地文件
result = md.convert_local("path/to/file.pdf")
print(result.text_content)

# 从字节流转换
with open("path/to/file.pdf", "rb") as f:
    result = md.convert_stream(f)
    print(result.text_content)
```

### 4. 测试 markitdown 可用性

```python
from markitdown import MarkItDown

md = MarkItDown()
print(md.convert("README.md").text_content)
```

## 参数说明

- **`enable_plugins`**: 是否启用第三方插件（默认 `False`）
- **`llm_client`**: OpenAI 兼容客户端，用于图片/PPT 中的图片描述
- **`llm_model`**: 模型名称（如 `"gpt-4o"`）
- **`llm_prompt`**: 自定义图片描述提示词
- **`docintel_endpoint`**: Azure Document Intelligence 端点
- **`cu_endpoint`**: Azure Content Understanding 端点
- **`cu_analyzer_id`**: Content Understanding 分析器 ID

### CLI 选项

| 选项 | 说明 |
|------|------|
| `-o FILE` | 输出到文件 |
| `-x EXT` | 提示文件扩展名 |
| `-m MIME` | 提示 MIME 类型 |
| `-c CHARSET` | 提示字符集 |
| `-d -e ENDPOINT` | 使用 Azure Document Intelligence |
| `--use-cu --cu-endpoint ENDPOINT` | 使用 Azure Content Understanding |
| `-p` / `--use-plugins` | 启用第三方插件 |
| `--list-plugins` | 列出已安装的插件 |
| `--keep-data-uris` | 保留 data URI（默认被截断） |

## 使用场景

- 将 Office 文档转为 Markdown 供 LLM 处理
- 批量转换 PDF/Word/Excel 为向量数据库的输入格式
- 从网页 HTML 提取结构化 Markdown 内容
- 图片 OCR 文字提取（需配合 LLM 客户端）
- 音频转文字（需安装 `[audio-transcription]` 依赖）
- YouTube 视频字幕提取（需安装 `[youtube-transcription]` 依赖）

## 注意事项

- **安全**: markitdown 会以当前进程权限执行 I/O。在服务端环境中，不要将未受信任的输入直接传给 `convert()`，优先使用 `convert_local()` 或 `convert_stream()`
- **虚拟环境**: 通过 `uv run` 自动使用 `.venv`，无需手动激活
- **依赖**: 首次使用前确保已执行 `uv sync --all-extras` 安装所有依赖
- **输出质量**: markitdown 输出面向文本分析工具，不是高保真文档转换

## 故障处理

如果 `uv run markitdown` 报模块未找到错误：

```bash
cd ~/.config/opencode/skills/markitdown/repo/packages/markitdown
uv sync --all-extras
```
