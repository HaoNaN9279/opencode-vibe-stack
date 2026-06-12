---
name: remove-bg
description: 通过 DataForge CLI 使用 BiRefNet 模型移除图片背景，支持单张处理，可调模型和背景填充色。
---

# Remove-BG — DataForge CLI 去背景工具

使用 DataForge 的 BiRefNet 模型移除图片背景的 CLI 参考。

## 前置依赖

安装 `rembg` 可选依赖：

```bash
uv sync --extra rembg
```

## CLI 调用

```bash
uv run --directory <path> python -m data_forge.remove_bg single \
  --input <源图片路径> \
  --output <输出图片路径> \
  [--model <模型变体>] \
  [--background-color <十六进制颜色>]
```

其中 `<path>` 为 DataForge 子模块路径（例如 `.opencode/tools/data-forge` 或项目克隆路径）。

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--input` | string | 是 | — | 源图片路径 |
| `--output` | string | 是 | — | 输出图片路径 |
| `--model` | string | 否 | `birefnet-general` | BiRefNet 模型变体（详见下方列表） |
| `--background-color` | string | 否 | `#FFFFFF` | 背景填充色，hex 格式（如 `#FFFFFF`、`#000000`） |

## BiRefNet 模型变体

| 模型名称 | 说明 |
|----------|------|
| `birefnet-general` | **通用模型**（默认）。适用于大多数日常场景，平衡精度与速度。 |
| `birefnet-general-lite` | **通用轻量版**。速度更快，适合对性能要求较高的场景。 |
| `birefnet-portrait` | **人像优化**。针对人物肖像分割进行了专门训练，人物边缘更精细。 |
| `birefnet-dis` | **显著目标检测**（DIS）。擅长从复杂背景中分离突出前景物体。 |
| `birefnet-hrsod` | **高分辨率显著目标检测**（HRSOD）。针对高分辨率图像优化，细节保留更好。 |
| `birefnet-cod` | **伪装目标检测**（COD）。擅长检测与背景高度融合的伪装物体。 |
| `birefnet-massive` | **大规模高精度模型**。精度最高，但推理速度最慢且显存占用最大。 |

## 使用示例

### 基本用法：移除背景输出透明 PNG

```bash
uv run --directory .opencode/tools/data-forge python -m data_forge.remove_bg single \
  --input photo.jpg \
  --output cutout.png
```

### 指定模型和背景色

```bash
uv run --directory .opencode/tools/data-forge python -m data_forge.remove_bg single \
  --input portrait.jpg \
  --output portrait_cutout.png \
  --model birefnet-portrait \
  --background-color "#000000"
```

### 使用高精度模型处理高分辨率图片

```bash
uv run --directory .opencode/tools/data-forge python -m data_forge.remove_bg single \
  --input large_photo.png \
  --output result.png \
  --model birefnet-hrsod
```

## 输出格式说明

- 输出为 `.png` 等支持透明通道的格式时，保留透明背景。
- 输出为 `.jpg`、`.bmp` 等不支持透明通道的格式时，自动以 `--background-color` 填充背景色。
