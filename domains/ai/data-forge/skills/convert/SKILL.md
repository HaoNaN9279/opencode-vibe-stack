---
name: convert
description: 通过 DataForge CLI 转换图片格式，支持单张和批量处理，含透明通道填充和质量控制。
---

# Convert

## ⚠️ 前置检查
```
data-forge --help
```
未安装：`git clone https://github.com/HaoNan9279/DataForge.git && cd DataForge && uv sync`

## 命令

### `convert single` — 单张转换
- `--input` `--output` (必填)
- `--background-color` (hex, 默认白色) | `--fill-alpha` 填充透明通道
- `--quality` (默认 95) | `--overwrite`
```
data-forge convert single --input logo.png --output logo.jpg
data-forge convert single --input logo.png --output logo_filled.png --fill-alpha --background-color "#0000FF"
```

### `convert batch` — 批量转换
- `--input-dir` `--output-dir` (必填)
- `--target-format` (默认 png: png/jpg/jpeg/webp/bmp)
- `--background-color` `--fill-alpha` `--quality` (默认 95) `--overwrite`
```
data-forge convert batch --input-dir ./raw --output-dir ./converted --target-format webp
```
