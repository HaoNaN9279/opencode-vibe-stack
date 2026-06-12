---
name: convert
description: 通过 ai_data-forge_convert 工具转换图片格式，支持单张和批量处理，含透明通道填充和质量控制。
---

# Convert

## 前置条件
确认 `ai_data-forge_convert` 工具可用（该工具由 domain 配置自动注册）。

## 使用方式

调用 `ai_data-forge_convert` 工具完成图片格式转换。

### 单张转换
- `input` `output` (必填)
- `background` (hex, 默认 `#FFFFFF`) — 填充透明通道的背景色
- `quality` (默认 95)

工具参数示例：
```
input: logo.png
output: logo.jpg
quality: 95
```

```
input: logo.png
output: logo_filled.png
background: "#0000FF"
```

### 批量转换
- 传入 `format` 参数触发批量模式
- `input` 视为源目录，`output` 视为输出目录
- `format` (必填): png / jpg / jpeg / webp / bmp
- `background` `quality` 同单张模式

工具参数示例：
```
input: ./raw
output: ./converted
format: webp
quality: 95
```
