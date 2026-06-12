---
name: remove-bg
description: 通过 ai_data-forge_remove-bg 工具使用 BiRefNet 模型移除图片背景，支持单张处理，可调模型和背景填充色。
---

# Remove-BG

需安装: `uv sync --extra rembg`

## 工具

使用 `ai_data-forge_remove-bg` 工具（位于 `tools/remove-bg.ts`）进行单张去背景。

### 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `input` | string | 是 | — | 源图片路径 |
| `output` | string | 是 | — | 输出图片路径 |
| `model` | string | 否 | `birefnet-general` | BiRefNet 模型变体：`birefnet-general`, `birefnet-general-lite`, `birefnet-portrait`, `birefnet-dis`, `birefnet-hrsod`, `birefnet-cod`, `birefnet-massive` |
| `background` | string | 否 | `#FFFFFF` | 背景填充色（hex 格式） |

### 示例

移除图片背景并输出透明 PNG：
```
ai_data-forge_remove-bg(input="photo.jpg", output="cutout.png")
```

指定模型和背景色：
```
data_forge_remove_bg(input="photo.jpg", output="cutout.png", model="birefnet-portrait", background="#000000")
```
