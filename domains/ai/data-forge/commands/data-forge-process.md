---
description: 执行 AI 训练数据集的图像处理操作：调整大小、背景移除和批量流水线
---

# `/data-forge-process` — 图像处理流水线

> **这是一份指导文档，而非自动化执行工具。**
> 它指导 AI 智能体如何使用 Data Forge MCP 工具执行图像处理流水线。此命令不直接执行任何图像处理、GPU 操作或模型推理。

---

## 1. 用途

对 AI 训练数据集执行图像处理操作：调整大小、背景移除和全量批量流水线。每个子命令代表一个处理阶段，可独立运行或串联执行。

| 子命令 | 描述 |
|---|---|
| `resize` | 批量将图像调整为目标尺寸，支持 fit/pad 模式 |
| `remove-bg` | 使用 BiRefNet 模型移除图像背景 |
| `batch` | 执行完整流水线：调整大小 → 背景移除 → 描述生成 → 描述优化 → 导出 |

---

## 2. 用法

```
/data-forge-process resize --input-dir <path> --output-dir <path> --width <px> --height <px> [--mode fit|pad]
/data-forge-process remove-bg --input-dir <path> --output-dir <path> [--model <model-name>]
/data-forge-process batch --input-dir <path> --output-dir <path> [--width <px>] [--height <px>] [--bg-model <model-name>] [--caption-provider openai|deepseek|ollama] [--export-format json|csv]
```

### 别名

```
/df-process resize --input-dir ./images --output-dir ./resized --width 512 --height 512
/df-process remove-bg --input-dir ./images --output-dir ./no-bg
/df-process batch --input-dir ./raw --output-dir ./processed
```

---

## 3. 参数

### `resize` 参数

| 参数 | 是否必需 | 描述 |
|---|---|---|
| `--input-dir` | 是 | 包含源图像的目录。 |
| `--output-dir` | 是 | 调整大小后输出图像的目录。如不存在则创建。 |
| `--width` | 是 | 目标宽度（像素）。 |
| `--height` | 是 | 目标高度（像素）。 |
| `--mode` | 否 | 调整模式：`fit`（缩放以适应尺寸，保持宽高比）或 `pad`（缩放并填充到精确尺寸）。默认值：`fit`。 |

### `remove-bg` 参数

| 参数 | 是否必需 | 描述 |
|---|---|---|
| `--input-dir` | 是 | 包含源图像的目录。 |
| `--output-dir` | 是 | 背景移除后输出图像的目录。 |
| `--model` | 否 | BiRefNet 模型变体。选项取决于已安装的 `rembg` 版本。默认值：最新可用版本。 |

### `batch` 参数

| 参数 | 是否必需 | 描述 |
|---|---|---|
| `--input-dir` | 是 | 包含源图像的目录。 |
| `--output-dir` | 是 | 根输出目录。各阶段子目录在此创建。 |
| `--width` | 否 | 调整大小的目标宽度。默认值：`512`。 |
| `--height` | 否 | 调整大小的目标高度。默认值：`512`。 |
| `--bg-model` | 否 | 背景移除的 BiRefNet 模型。默认值：最新可用版本。 |
| `--caption-provider` | 否 | 图像描述的 LLM 供应商：`openai`、`deepseek` 或 `ollama`。默认值：`ollama`。 |
| `--export-format` | 否 | 最终导出格式：`json` 或 `csv`。默认值：`json`。 |

---

## 4. 执行步骤

### 4.1 `resize` — 批量图像调整

1. **验证输入** — 确认 `--input-dir` 存在且包含图像文件。报告检测到的文件数和格式。
2. **调用 `resize_images`** — 传递 `input_dir`、`output_dir`、`width`、`height` 和 `mode` 参数。
3. **验证响应** — 在继续之前检查 `{"status": "ok"}`。出错时报告 `message` 并停止。
4. **报告** — 输出调整后的数量、应用的尺寸、使用的模式、输出位置。

### 4.2 `remove-bg` — 背景移除

1. **验证输入** — 确认 `--input-dir` 包含图像（最好已预先调整大小）。验证已安装带 BiRefNet 模型的 `rembg` 包。
2. **选择工具** — 单张图像使用 `remove_background`；目录使用 `remove_background_batch`。优先使用批处理。
3. **调用 `remove_background_batch`** — 传递 `input_dir`、`output_dir`，可选 `model`。
4. **验证响应** — 检查 `{"status": "ok"}`。背景移除是 GPU 密集型操作；错误通常表示缺少模型或 CUDA 问题。
5. **报告** — 输出处理数量、使用的模型、输出位置。

### 4.3 `batch` — 完整流水线

批量流水线按顺序执行五个阶段，每个阶段验证通过后才继续。

**阶段 1：调整大小**
1. 创建 `output-dir/resized/` 子目录。
2. 使用 `--width` 和 `--height` 参数调用 `resize_images`。
3. 验证 `{"status": "ok"}`。失败时停止。

**阶段 2：背景移除**
1. 创建 `output-dir/no-bg/` 子目录。
2. 以调整大小后的图像作为输入调用 `remove_background_batch`，如指定则使用 `--bg-model`。
3. 验证 `{"status": "ok"}`。失败时停止。

**阶段 3：描述生成**
1. 根据 `--caption-provider` 确定描述工具：
   - `openai` / `deepseek`：使用 `llm_batch_describe_images`，配合相应的 keyfile。
   - `ollama`：使用 `ollama_batch_describe_images`（通过 `ollama_list_models` 先验证服务器正在运行）。
2. 对背景移除后的图像调用选定的工具。
3. 验证 `{"status": "ok"}`。失败时停止。

**阶段 4：描述质量检查**
1. 对生成的描述运行 `caption_stats`。
2. 运行 `caption_search` 检测异常（空描述、编码问题）。
3. 如果质量指标不达标，建议优化提示词（参见 `/data-forge-prompt`）并重新运行阶段 3。

**阶段 5：导出**
1. 创建 `output-dir/exports/` 子目录。
2. 使用指定的 `--export-format`（json/csv）调用 `caption_export`。
3. 验证 `{"status": "ok"}`。
4. 报告最终流水线摘要。

---

## 5. 输出

每个阶段生成包含工具响应数据的状态报告。

**示例输出（`resize`）：**

```
Resize Complete
├── Input:        ./images (250 files)
├── Output:       ./resized
├── Dimensions:   512 x 512
├── Mode:         fit
├── Processed:    250/250
└── Status:       ok
```

**示例输出（`batch`）：**

```
Batch Pipeline Complete
├── Stage 1: Resize         [ok] — 250/250 → ./processed/resized/
├── Stage 2: Background     [ok] — 250/250 → ./processed/no-bg/
├── Stage 3: Captions       [ok] — 250/250 via ollama/llava
├── Stage 4: Quality Check  [ok] — mean words=14.2, empty=2
├── Stage 5: Export         [ok] — ./processed/exports/captions.json
└── Total Time:             ~12 minutes (estimated)
```

---

## 6. 流水线阶段依赖

```
resize ──→ remove-bg ──→ caption ──→ export
  │            │             │
  └─ optional standalone    └─ requires prior stages
```

- `resize`：独立运行 — 可对原始图像独立执行。
- `remove-bg`：独立运行 — 可独立执行，但建议在 `resize` 之后运行以获得一致的输入尺寸。
- `batch`：一体化 — 按顺序执行所有阶段并进行依赖验证。

---

## 7. 说明

- **不执行 GPU 操作。** 此命令仅提供指导。实际图像处理通过 Data Forge MCP 工具在用户机器上运行。
- **背景移除需要 `rembg`** 配合 BiRefNet 模型。在建议 `remove-bg` 或 `batch` 之前，请验证安装。
- **LLM 描述生成需要：** 有效的 keyfile（云端 LLM）或正在运行且已拉取目标模型的 Ollama 服务器（本地 LLM）。
- **流水线阶段是原子性的。** 如果任何阶段失败，流水线将停止。用户可以从失败点恢复。
- **磁盘空间。** 批量流水线会生成中间目录。确保有足够的磁盘空间用于 `resized/`、`no-bg/` 和 `exports/` 输出。
