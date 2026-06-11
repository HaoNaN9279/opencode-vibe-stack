---
name: resize
description: 通过 DataForge CLI 批量缩放图片，支持目标尺寸裁剪、等比缩放、长边适配和填充。
---

# Resize

## ⚠️ 前置检查
```
data-forge --help
```
未安装：`git clone https://github.com/HaoNan9279/DataForge.git && cd DataForge && uv sync`

## 命令

### `resize images` — 批量缩放
- `--input-dir` `--output-dir` `--width` `--height` (必填)
- `--fit-long-edge` 等比缩放，长边适配
- `--pad-to-fit` 缩放后填充至精确尺寸
- `--background-color` (hex, 默认白色) 填充色
- `--overwrite`
```
data-forge resize images --input-dir ./photos --output-dir ./resized --width 1024 --height 1024
data-forge resize images --input-dir ./photos --output-dir ./resized --width 1024 --height 1024 --fit-long-edge --pad-to-fit --background-color "#000000"
```
