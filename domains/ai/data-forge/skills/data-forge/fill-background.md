---
name: fill-background
description: 给带透明通道的图片填充指定颜色背景，始终输出 RGB
---

# Fill-Background — 图片背景填充

使用 DataForge 的 `fill_background` 模块为带透明通道（RGBA）的图片填充指定十六进制颜色背景，输出为不含透明通道的 RGB 图片。支持单张和批量两种模式。

## CLI 调用

```bash
# 单张处理
uv run --directory domains/ai/data-forge/skills/data-forge \
  python -m data_forge.tools.fill_background single \
  --input <源图片路径> \
  --output <输出图片路径> \
  [--background-color "#FFFFFF"]

# 批量处理
uv run --directory domains/ai/data-forge/skills/data-forge \
  python -m data_forge.tools.fill_background batch \
  --input-dir <源目录> \
  --output-dir <输出目录> \
  [--background-color "#FFFFFF"] \
  [--overwrite]
```

## 参数说明

| 参数 | 模式 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--input` | single | 是 | — | 源图片文件路径 |
| `--output` | single | 是 | — | 输出图片文件路径 |
| `--input-dir` | batch | 是 | — | 源图片目录，处理目录下所有支持的图片 |
| `--output-dir` | batch | 是 | — | 输出目录，处理后的图片写入此目录 |
| `--background-color` | 通用 | 否 | `#FFFFFF` | 填充颜色的十六进制值，格式如 `#FFFFFF`、`#0000FF` |
| `--overwrite` | batch | 否 | `false` | 覆盖已存在的输出文件。默认跳过已有文件 |

## 使用示例

### 1. 基本用法：PNG 透明背景 → 白色背景 JPEG

将带透明通道的 PNG logo 转换为白色背景的 JPEG：

```bash
uv run --directory domains/ai/data-forge/skills/data-forge \
  python -m data_forge.tools.fill_background single \
  --input logo.png \
  --output logo.jpg
```

### 2. 自定义颜色：RGBA 图片 → 绿色背景

```bash
uv run --directory domains/ai/data-forge/skills/data-forge \
  python -m data_forge.tools.fill_background single \
  --input overlay.png \
  --output overlay_green.jpg \
  --background-color "#00FF00"
```

### 3. 批量处理整个目录

将 `assets/` 下所有带透明通道的图片批量填充白色背景，输出到 `filled/`：

```bash
uv run --directory domains/ai/data-forge/skills/data-forge \
  python -m data_forge.tools.fill_background batch \
  --input-dir assets \
  --output-dir filled \
  --background-color "#FFFFFF" \
  --overwrite
```

## 输出格式说明

- 输出始终为 RGB（不含透明通道），透明区域替换为指定的 `--background-color`。
- 输入图片若不含透明通道（如 JPEG），则不做任何修改直接输出。
