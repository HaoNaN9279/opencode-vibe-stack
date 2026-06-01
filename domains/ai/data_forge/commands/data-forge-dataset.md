---
description: 管理 AI 训练数据集的完整生命周期：列表、检查、创建和清理
---

# `/data-forge-dataset` — 数据集管理

> **这是一份指导文档，而非自动化执行工具。**
> 它指导 AI 智能体如何使用 Data Forge MCP 工具管理 AI 训练数据集。此命令不执行任何软件安装、运行时调用或自动化执行。

---

## 1. 用途

管理 AI 训练数据集的全生命周期：列表、检查、创建和清理。每个子命令映射到特定的 Data Forge MCP 工具。

| 子命令 | 描述 |
|---|---|
| `list` | 列出目录中的数据集，显示图像和描述文件数量 |
| `inspect` | 展示数据集概况及统计数据（词数、分布、质量指标） |
| `create` | 使用常规布局搭建新的数据集目录结构 |
| `clean` | 去重描述并验证数据集完整性 |

---

## 2. 用法

```
/data-forge-dataset list --directory <path> [--recursive]
/data-forge-dataset inspect --directory <path> [--format json|csv]
/data-forge-dataset create --directory <path> [--name <dataset-name>]
/data-forge-dataset clean --directory <path> [--strategy keep-first|keep-last]
```

### 别名

```
/df-dataset list --directory ./input
/df-dataset inspect --directory ./my-dataset
/df-dataset create --directory ./projects --name v1-captions
/df-dataset clean --directory ./my-dataset --strategy keep-first
```

---

## 3. 参数

### 全局参数

| 参数 | 是否必需 | 描述 |
|---|---|---|
| `--directory` | 是 | 数据集目录的路径。对 `list`、`inspect`、`clean` 必须已存在；对 `create` 将被创建。 |

### `list` 参数

| 参数 | 是否必需 | 描述 |
|---|---|---|
| `--recursive` | 否 | 递归列出子目录。默认值：`false`（仅顶层）。 |
| `--format` | 否 | 输出格式：`json` 或 `csv`。默认值：终端表格。 |

### `inspect` 参数

| 参数 | 是否必需 | 描述 |
|---|---|---|
| `--format` | 否 | 概况输出格式：`json` 或 `csv`。默认值：`json`。 |

### `create` 参数

| 参数 | 是否必需 | 描述 |
|---|---|---|
| `--name` | 否 | 数据集名称。如果与 `--directory` 不同，用于目录名。默认值：`--directory` 的基本名称。 |

### `clean` 参数

| 参数 | 是否必需 | 描述 |
|---|---|---|
| `--strategy` | 否 | 去重保留策略：`keep-first` 或 `keep-last`。默认值：`keep-first`。 |

---

## 4. 执行步骤

### 4.1 `list` — 列出数据集

1. **验证目录** — 确认 `--directory` 存在且可访问。
2. **使用 `caption_list` 枚举内容** — 对目标目录调用 `caption_list`，检索所有描述文件及相关元数据。
3. **报告** — 呈现图像数量、描述数量以及任何孤立文件（无对应图像的描述、无对应描述的图像）。如果指定了 `--recursive`，则枚举子目录。
4. **格式化输出** — 默认使用表格格式；如果指定了 `--format`，则为 JSON/CSV。

### 4.2 `inspect` — 数据集概况分析

1. **运行 `caption_stats`** — 对目标目录调用 `caption_stats` 计算：
   - 描述总数
   - 词数分布（最小值、最大值、均值、中位数、标准差）
   - 字符数分布
   - 空描述计数
   - 词汇多样性指标
2. **运行 `caption_search` 检测异常** — 使用适当的正则表达式模式搜索空文件、编码问题和格式违规。
3. **使用 `caption_read_all` 交叉验证** — 读取所有描述，验证每张图像都有对应描述，反之亦然。
4. **生成质量评分卡** — 将各项指标汇总为结构化报告：格式合规性、去重估算值、词汇覆盖率。

### 4.3 `create` — 搭建新数据集

1. **创建目录结构：**
   ```
   <dataset-name>/
   ├── images/            # 源图像
   ├── captions/          # 描述文件（.txt、.json、.csv）
   ├── output/            # 处理后的输出（调整大小、背景移除）
   ├── exports/           # 导出产物（JSON/CSV 转储）
   └── workflow/          # ComfyUI 工作流 JSON（可选）
   ```
2. **使用 `caption_import` 初始化** — 如果用户提供了初始描述（JSON/CSV），将其导入到 `captions/` 目录。
3. **报告** — 列出创建的目录及其预期用途。

### 4.4 `clean` — 去重与验证

1. **备份建议** — 始终建议用户在执行破坏性操作之前备份数据集。
2. **运行 `caption_deduplicate`** — 使用指定的 `--strategy` 执行去重：
   - `keep-first`：保留每个描述的首次出现，移除后续重复项。
   - `keep-last`：保留最后一次出现，移除较早的重复项。
3. **清理后运行 `caption_stats`** — 验证去重结果：减少的数量、保留描述的分布概况不变。
4. **验证格式一致性** — 检查所有剩余描述是否具有一致的文件扩展名、编码和结构。
5. **报告** — 呈现清理前后统计数据：移除的描述数、保留的描述数、去重率。

---

## 5. 输出

该命令在每个阶段生成结构化报告。报告包含工具调用结果及 `{"status": "ok"|"error", "message": "..."}` 响应。

**示例输出（`list`）：**

```
Dataset: ./my-dataset
├── images/     — 1,250 files (.png, .jpg)
├── captions/   — 1,248 files (.txt)
└── ORPHANS:    — 2 images without captions, 0 captions without images
```

**示例输出（`inspect`）：**

```
Dataset Profile: ./my-dataset
├── Total Captions:     1,248
├── Word Count:         mean=12.4, median=11, stddev=5.2, min=3, max=47
├── Character Count:    mean=78.2, median=72, min=18, max=312
├── Empty Captions:     3
├── Format Compliance:  98.6% (17 files with encoding issues)
└── Vocabulary Size:    2,847 unique words
```

**示例输出（`clean`）：**

```
Clean Report: ./my-dataset
├── Before:             1,248 captions
├── Duplicates Found:   42
├── After:              1,206 captions
├── Deduplication Rate: 3.4%
└── Strategy:           keep-first
```

---

## 6. 说明

- **不执行自动化操作。** 此命令仅提供指导。AI 智能体会指导用户调用哪些 MCP 工具并解释其输出。
- **工具依赖顺序。** `inspect` 必须在 `clean` 之前执行——切勿在未进行概况分析的情况下清理。
- **`caption_deduplicate` 是破坏性操作。** 执行前始终建议备份。Data Curator 智能体会强制执行此规则。
- **目录验证。** 所有 `--directory` 值必须为绝对路径或相对于当前工作目录的路径。路径直接传递给 MCP 工具。
