---
name: resize
description: 通过 ai_data-forge_resize 工具批量缩放图片，支持目标尺寸裁剪、等比缩放、长边适配和填充。
---

# Resize

使用 `ai_data-forge_resize` 工具批量处理图片缩放。

## 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `inputDir` | string | 是 | 源图片目录路径 |
| `outputDir` | string | 是 | 输出目录路径 |
| `width` | number | 是 | 目标宽度（像素） |
| `height` | number | 是 | 目标高度（像素） |
| `fitLongEdge` | boolean | 否 | 等比缩放，长边适配 |
| `padToFit` | boolean | 否 | 缩放后填充至精确尺寸 |
| `overwrite` | boolean | 否 | 覆盖已有输出文件 |

## 示例

```
subcommand: resize
inputDir: ./photos
outputDir: ./resized
width: 1024
height: 1024
```

```
subcommand: resize
inputDir: ./photos
outputDir: ./resized
width: 1024
height: 1024
fitLongEdge: true
padToFit: true
overwrite: true
```
