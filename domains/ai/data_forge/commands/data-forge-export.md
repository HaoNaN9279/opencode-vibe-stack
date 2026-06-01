---
description: 跨格式导出和导入 AI 训练数据：描述导出/导入、ComfyUI 工作流配置和批量格式转换
---

# `/data-forge-export` — 导出与格式转换

> **这是一份指导文档，而非自动化执行工具。**
> 它指导 AI 智能体如何使用 Data Forge MCP 工具导出和导入数据集、描述和工作流配置。此命令不直接执行任何文件 I/O 或格式转换。

---

## 1. 用途

跨格式导出和导入 AI 训练数据：将描述导出为 JSON/CSV、ComfyUI 工作流配置以及批量格式转换。每个子命令对应特定的 Data Forge MCP 导出/导入工具。

| 子命令 | 描述 |
|---|---|
| `captions` | 将描述导出或导入为 JSON 或 CSV |
| `workflow` | 导出 ComfyUI 工作流配置 |
| `batch` | 批量导出并转换格式以集成到流水线 |

---

## 2. 用法

```
/data-forge-export captions --action export|import --input-path <path> [--output-path <path>] [--format json|csv|jsonl]
/data-forge-export workflow --action export [--input-path <path>] [--output-path <path>]
/data-forge-export batch --input-dir <path> --output-dir <path> [--format json|csv|jsonl] [--include all|captions|workflows]
```

### 别名

```
/df-export captions --action export --input-path ./captions --output-path ./exports/captions.json
/df-export workflow --action export --output-path ./exports/workflow.json
/df-export batch --input-dir ./dataset --output-dir ./exports --format json
```

---

## 3. 参数

### `captions` 参数

| 参数 | 是否必需 | 描述 |
|---|---|---|
| `--action` | 是 | 操作：`export`（描述 → 文件）或 `import`（文件 → 描述）。 |
| `--input-path` | 是 | 对于 `export`：包含描述文件的目录。对于 `import`：JSON/CSV 文件路径。 |
| `--output-path` | 条件性 | 对于 `export`：输出文件路径。对于 `import`：生成描述文件的目标目录。除非使用默认值，否则需要。 |
| `--format` | 否 | 文件格式：`json`、`csv` 或 `jsonl`。默认值：`json`。 |

### `workflow` 参数

| 参数 | 是否必需 | 描述 |
|---|---|---|
| `--action` | 是 | 操作：仅 `export`（工作流配置导出）。 |
| `--input-path` | 否 | ComfyUI 工作流 JSON 的路径。如果省略，引用最近使用的工作流。 |
| `--output-path` | 否 | 输出文件路径。默认值：`./exports/workflow_<timestamp>.json`。 |

### `batch` 参数

| 参数 | 是否必需 | 描述 |
|---|---|---|
| `--input-dir` | 是 | 包含数据集（图像、描述、工作流）的目录。 |
| `--output-dir` | 是 | 导出文件的目录。如果不存在则创建。 |
| `--format` | 否 | 导出格式：`json`、`csv` 或 `jsonl`。默认值：`json`。 |
| `--include` | 否 | 导出内容：`all`（描述 + 工作流）、`captions` 或 `workflows`。默认值：`all`。 |

---

## 4. 执行步骤

### 4.1 `captions` — 导出/导入描述

**导出：**
1. **验证输入** — 确认 `--input-path` 是包含描述文件的目录。运行 `caption_read_all` 验证数据完整性。
2. **调用 `caption_export`** — 传递 `input_dir` 和 `output_path`（或从默认值推导），并指定 `--format`。
3. **验证响应** — 检查 `{"status": "ok"}`。如果出错，`message` 可能指示文件权限问题或目录无效。
4. **验证输出** — 确认导出文件存在且包含预期数量的记录。对于 JSON：验证结构。对于 CSV：验证列标题。

**导入：**
1. **验证输入** — 确认 `--input-path` 是 JSON/CSV 文件。验证结构：对于 JSON，应为包含必要字段的对象数组；对于 CSV，检查表头是否包含描述文本和图像引用列。
2. **调用 `caption_import`** — 传递 `input_file` 和 `output_dir`，并指定 `--format`。
3. **验证响应** — 检查 `{"status": "ok"}`。如果出错，`message` 可能指示格式验证失败。
4. **导入后验证** — 在输出目录上运行 `caption_stats` 以验证导入质量。检查编码问题、字段不匹配、孤立文件。

### 4.2 `workflow` — 导出 ComfyUI 工作流

1. **定位工作流** — 如果提供了 `--input-path`，则使用该路径；否则引用最近的工作流 JSON。
2. **验证工作流** — 确认 JSON 是有效的 ComfyUI API 格式工作流（包含带有 class_type 和 inputs 的节点定义）。
3. **导出** — 将工作流 JSON 复制或序列化到 `--output-path`。
4. **报告** — 输出文件路径、工作流节点数和关键参数（模型、分辨率、种子范围）。

### 4.3 `batch` — 批量导出

**阶段 1：描述导出**
1. 在 `--input-dir/captions/` 中定位描述（或从目录结构中检测）。
2. 使用检测到的输入目录调用 `caption_export`，输出为 `--output-dir/captions_export.<format>`。
3. 验证 `{"status": "ok"}`。

**阶段 2：工作流导出（如果 `--include all` 或 `workflows`）**
1. 在 `--input-dir/workflows/` 或类似位置定位工作流 JSON。
2. 将工作流文件复制到 `--output-dir/workflows/`。
3. 报告导出的工作流数量。

**阶段 3：格式转换**
1. 如果 `--format jsonl`，将任何 JSON 导出转换为 JSONL（每行一条记录）以实现流式流水线兼容。
2. 验证所有输出文件。

**阶段 4：汇总报告**
1. 列出所有导出的文件及记录数。
2. 验证交叉引用：导出的描述数量与源描述数量一致。

---

## 5. 输出

**示例输出（`captions export`）：**

```
Caption Export Complete
├── Source:       ./captions/ (1,248 files)
├── Output:       ./exports/captions.json
├── Format:       json
├── Records:      1,248
├── Fields:       image, caption, timestamp
└── Status:       ok
```

**示例输出（`captions import`）：**

```
Caption Import Complete
├── Source:       ./external/captions.csv
├── Output:       ./captions/ (1,000 files created)
├── Format:       csv
├── Records:      1,000 imported
├── Warnings:     3 rows skipped (missing image field)
└── Status:       ok
```

**示例输出（`batch`）：**

```
Batch Export Complete
├── Captions:     ./exports/captions.json (1,248 records) [ok]
├── Workflows:    ./exports/workflows/ (3 files) [ok]
├── Format:       json
├── Output Dir:   ./exports/
└── Status:       ok
```

---

## 6. 格式规范

### JSON 导出（`caption_export --format json`）

```json
[
  {
    "image": "image_001.png",
    "caption": "A red car parked on a city street under cloudy skies.",
    "timestamp": "2026-05-26T12:00:00Z"
  }
]
```

### CSV 导出（`caption_export --format csv`）

```csv
image,caption,timestamp
image_001.png,"A red car parked on a city street under cloudy skies.",2026-05-26T12:00:00Z
```

### JSONL 导出（`caption_export --format jsonl`）

```jsonl
{"image": "image_001.png", "caption": "A red car parked on a city street under cloudy skies.", "timestamp": "2026-05-26T12:00:00Z"}
{"image": "image_002.png", "caption": "A woman reading a book in a sunlit cafe.", "timestamp": "2026-05-26T12:00:01Z"}
```

---

## 7. 说明

- **不执行文件 I/O。** 此命令仅提供指导。所有读/写操作由 Data Forge MCP 工具执行。
- **导入时格式验证至关重要。** 导入前始终检查 CSV 表头和 JSON 结构。不匹配的 Schema 会导致 `caption_import` 失败并返回 `{"status": "error"}`。
- **大型数据集建议使用 JSONL。** 流式兼容格式避免将整个数据集加载到内存中。
- **导出不会修改源数据。** 所有导出操作对源数据是只读的。导入操作会写入新文件，不会修改源数据。
- **工作流导出仅供参考。** ComfyUI 工作流 JSON 按原样复制；不验证工作流的可执行性。
