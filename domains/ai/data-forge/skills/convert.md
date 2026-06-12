# Convert — 图片格式转换

通过 DataForge 的 `convert` 模块在 PNG、JPG、JPEG、WebP、BMP 格式之间转换图片，支持单张和批量两种模式。

## 用法

```bash
# 单张转换（格式由输出文件扩展名自动识别）
uv run --directory domains/ai/data-forge/skills/data-forge \
  python -m data_forge.convert single \
  --input <源图片路径> \
  --output <目标图片路径> \
  [--quality <质量>] \
  [--background-color <背景色>]

# 批量转换（需指定 --target-format）
uv run --directory domains/ai/data-forge/skills/data-forge \
  python -m data_forge.convert batch \
  --input-dir <源目录> \
  --output-dir <输出目录> \
  --target-format <目标格式> \
  [--quality <质量>] \
  [--background-color <背景色>]
```

## 参数说明

| 参数 | 模式 | 必填 | 说明 |
|------|------|------|------|
| `--input` | single | 是 | 源图片文件路径 |
| `--output` | single | 是 | 输出图片文件路径，格式由扩展名自动识别 |
| `--input-dir` | batch | 是 | 源图片目录，转换目录下所有支持的图片 |
| `--output-dir` | batch | 是 | 输出目录，所有转换后的图片写入此目录 |
| `--target-format` | batch | 是 | 目标格式：`png`、`jpg`、`jpeg`、`webp`、`bmp` |
| `--quality` | 通用 | 否 | JPEG/WebP 输出质量，范围 1–100，默认 `95` |
| `--background-color` | 通用 | 否 | RGBA → RGB 转换时填充透明通道的十六进制背景色，默认 `#FFFFFF` |

## 支持格式

- `png` — Portable Network Graphics
- `jpg` / `jpeg` — JPEG
- `webp` — WebP
- `bmp` — BMP

## 模式区别

| | 单张模式 (single) | 批量模式 (batch) |
|---|---|---|
| 触发条件 | 使用 `--input` / `--output` | 提供 `--target-format` |
| 目标格式 | 由 `--output` 文件扩展名自动识别 | 由 `--target-format` 显式指定 |
| 输入 | 单个文件 | 整个目录（所有支持的格式） |
| 输出 | 单个文件 | 整个目录，文件名保留原名、扩展名替换为目标格式 |

## 示例

### 1. 单张转换：PNG → JPEG

将带透明通道的 PNG logo 转换为白色背景的 JPEG：

```bash
uv run --directory domains/ai/data-forge/skills/data-forge \
  python -m data_forge.convert single \
  --input logo.png \
  --output logo.jpg \
  --quality 90 \
  --background-color "#FFFFFF"
```

### 2. 单张转换：JPEG → WebP

```bash
uv run --directory domains/ai/data-forge/skills/data-forge \
  python -m data_forge.convert single \
  --input photo.jpg \
  --output photo.webp \
  --quality 85
```

### 3. 批量转换：整个目录转 WebP

将 `raw_photos/` 下所有图片转换为 WebP 格式，输出到 `webp_output/`：

```bash
uv run --directory domains/ai/data-forge/skills/data-forge \
  python -m data_forge.convert batch \
  --input-dir raw_photos \
  --output-dir webp_output \
  --target-format webp \
  --quality 92
```

### 4. 批量转换：带透明通道填充

将 `assets/` 下所有 PNG 转换为 JPG，透明区域填充蓝色：

```bash
uv run --directory domains/ai/data-forge/skills/data-forge \
  python -m data_forge.convert batch \
  --input-dir assets \
  --output-dir jpg_output \
  --target-format jpg \
  --background-color "#0000FF"
```
