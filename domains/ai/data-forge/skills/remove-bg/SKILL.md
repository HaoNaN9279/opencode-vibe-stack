---
name: remove-bg
description: 通过 DataForge CLI 使用 BiRefNet 模型移除图片背景，支持单张和批量处理，可调精细边缘和背景填充色。
---

# Remove-BG

需安装: `uv sync --extra rembg`

## ⚠️ 前置检查
```
data-forge --help
```
未安装：`git clone https://github.com/HaoNan9279/DataForge.git && cd DataForge && uv sync --extra rembg`

## 命令

### `remove-bg single` — 单张去背景
- `--input` `--output` (必填)
- `--model` (默认 birefnet-general) | `--background-color` (hex, 默认白色)
- `--alpha-matting` 精细边缘
```
data-forge remove-bg single --input photo.jpg --output cutout.png
data-forge remove-bg single --input photo.jpg --output cutout.png --alpha-matting
```

### `remove-bg batch` — 批量去背景
- `--input-dir` `--output-dir` (必填)
- `--model` `--background-color` `--alpha-matting` `--overwrite`
```
data-forge remove-bg batch --input-dir ./photos --output-dir ./cutouts
```
