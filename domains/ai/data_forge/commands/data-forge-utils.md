---
description: 快速访问 Data Forge MCP 工具文档、依赖版本检查、服务器状态诊断和故障排除
---

# `/data-forge-utils` — 工具与参考指南

用于快速访问 Data Forge MCP 所有工具文档、依赖版本检查、服务器状态诊断、代码片段参考和故障排除指导的斜杠命令。

---

## 1. 用法

```
/data-forge-utils docs <tool-name>              — Look up tool documentation
/data-forge-utils version [--all]              — Check dependency versions
/data-forge-utils status <service>             — Check ComfyUI or Ollama server status
/data-forge-utils snippets <topic>             — Browse code snippet index
/data-forge-utils help                         — Show this help
```

### 别名

```
/df-utils docs resize_images
/df-utils version --all
/df-utils status ollama
/df-utils snippets caption-search
```

---

## 2. 工具文档查询（`docs`）

查询任何 Data Forge MCP 工具的签名、参数和返回格式。

```
/data-forge-utils docs <tool-name>
```

AI 智能体回应以下内容：
- 工具名称和类别
- 完整的参数列表及类型和描述
- 返回格式：`{"status": "ok"|"error", "message": "..."}`
- 使用示例
- 常见错误场景

---

## 3. 版本检查（`version`）

检查 Data Forge 工具链已安装的依赖版本。

```
/data-forge-utils version [--all]
```

| 依赖项 | 最低版本 | 检查命令 |
|---|---|---|
| Python | 3.12+ | `python --version` |
| uv | 最新版 | `uv --version` |
| FastMCP | 最新版 | `uv pip list | grep fastmcp` |
| rembg | 最新版（含 BiRefNet） | `pip show rembg` |
| Ollama | 最新版 | `ollama --version` |
| ComfyUI | 最新版 | 通过 `comfyui_status` 检查 |

**用法：**

```
/df-utils version          — 显示 Python 及核心依赖版本
/df-utils version --all    — 显示所有依赖，包括 rembg、Ollama、ComfyUI
```

---

## 4. 服务器状态（`status`）

检查 Data Forge 所需的外部服务是否正在运行并可访问。

```
/data-forge-utils status comfyui
/data-forge-utils status ollama
```

### ComfyUI 状态（`status comfyui`）

1. 调用 `comfyui_status` MCP 工具。
2. 报告：服务器可达性、可用工作流、GPU 可用性、队列状态。
3. 如果不可达，提供故障排除步骤（参见 §7 — 故障排除）。

### Ollama 状态（`status ollama`）

1. 调用 `ollama_list_models` MCP 工具。
2. 报告：服务器可达性、已安装模型及标签、模型大小。
3. 如果不可达，提供故障排除步骤（参见 §7 — 故障排除）。

---

## 5. 代码片段（`snippets`）

常见 Data Forge 工具调用模式的快速参考。

```
/data-forge-utils snippets <topic>
```

### 片段索引

| 主题 | 描述 |
|---|---|
| `resize-batch` | 使用 fit/pad 模式批量调整图像大小 |
| `bg-remove` | 单张和批量背景移除 |
| `caption-search` | 跨描述的正则表达式搜索 |
| `caption-stats` | 完整数据集概况分析 |
| `caption-dedup` | 去重描述 |
| `caption-export-import` | 格式转换工作流 |
| `llm-batch` | 批量 LLM 图像描述 |
| `ollama-batch` | 批量 Ollama 图像描述 |
| `comfyui-workflow` | 运行 ComfyUI 工作流 |
| `pipeline-end-to-end` | 完整流水线：调整大小 → 背景移除 → 描述 → 导出 |

### Snippet: `resize-batch`

```
Tool: resize_images
Parameters:
  input_dir: str    — Directory containing source images
  output_dir: str   — Directory for resized output
  width: int        — Target width (pixels)
  height: int       — Target height (pixels)
  mode: str         — "fit" or "pad"
Returns: {"status": "ok"|"error", "message": "..."}
Example: resize_images(input_dir="./images", output_dir="./resized", width=512, height=512, mode="fit")
```

### Snippet: `caption-stats`

```
Tool: caption_stats
Parameters:
  directory: str    — Directory containing caption files
Returns: {"status": "ok"|"error", "message": "...", "data": {...}}
  data fields: total, word_count (min/max/mean/median/stddev),
               char_count (min/max/mean), empty_count
Example: caption_stats(directory="./captions")
```

### Snippet: `llm-batch`

```
Tool: llm_batch_describe_images
Parameters:
  input_dir: str    — Directory containing images
  output_dir: str   — Directory for generated captions
  model: str        — Model name (e.g., "gpt-4o")
  keyfile: str      — Path to API keyfile JSON
Returns: {"status": "ok"|"error", "message": "..."}
Example: llm_batch_describe_images(input_dir="./images", output_dir="./captions",
          model="gpt-4o", keyfile="./keys/openai.json")
```

### Snippet: `comfyui-workflow`

```
Tool: comfyui_run_workflow
Parameters:
  workflow: dict    — Workflow JSON as Python dict
  parameters: dict  — Parameter overrides
Returns: {"status": "ok"|"error", "message": "..."}
Tool: comfyui_run_batch
Parameters:
  workflow: dict    — Base workflow JSON
  parameter_sets: list[dict]  — Array of parameter overrides for batch
Returns: {"status": "ok"|"error", "message": "..."}
```

---

## 6. 完整 MCP 工具参考

全部 24 个 Data Forge MCP 工具，按类别组织。

### 调整大小（1 个工具）

| 工具 | 参数 | 描述 |
|---|---|---|
| `resize_images` | `input_dir`、`output_dir`、`width`、`height`、`mode` | 使用 fit/pad 模式批量调整图像大小 |

### 背景移除（2 个工具）

| 工具 | 参数 | 描述 |
|---|---|---|
| `remove_background` | `input_path`、`output_path`、`model`（可选） | 移除单张图像背景 |
| `remove_background_batch` | `input_dir`、`output_dir`、`model`（可选） | 批量背景移除 |

### 描述（9 个工具）

| 工具 | 参数 | 描述 |
|---|---|---|
| `caption_list` | `directory`、`recursive`（可选） | 列出目录中所有描述文件 |
| `caption_read` | `file_path` | 读取单个描述文件 |
| `caption_read_all` | `directory` | 读取目录中所有描述 |
| `caption_search` | `directory`、`query`（正则表达式）、`case_sensitive`（可选） | 通过正则表达式模式搜索描述 |
| `caption_batch_replace` | `directory`、`query`（正则表达式）、`replace_with` | 跨描述批量正则替换 |
| `caption_export` | `input_dir`、`output_path`、`format`（json/csv/jsonl） | 导出描述至文件 |
| `caption_import` | `input_file`、`output_dir`、`format`（json/csv） | 从文件导入描述 |
| `caption_stats` | `directory` | 计算描述统计信息 |
| `caption_deduplicate` | `directory`、`strategy`（keep-first/keep-last） | 去重描述 |

### LLM 云端（4 个工具）

| 工具 | 参数 | 描述 |
|---|---|---|
| `llm_chat` | `prompt`、`model`、`keyfile` | 单轮 LLM 对话 |
| `llm_describe_image` | `image_path`、`prompt`、`model`、`keyfile` | 描述单张图像 |
| `llm_batch_chat` | `prompts`（列表）、`model`、`keyfile` | 批量 LLM 对话 |
| `llm_batch_describe_images` | `input_dir`、`output_dir`、`model`、`keyfile` | 批量图像描述 |

### Ollama 本地（5 个工具）

| 工具 | 参数 | 描述 |
|---|---|---|
| `ollama_generate` | `prompt`、`model` | 通过 Ollama 进行单次文本生成 |
| `ollama_list_models` | _（无）_ | 列出可用的 Ollama 模型 |
| `ollama_describe_image` | `image_path`、`prompt`、`model` | 通过 Ollama 描述单张图像 |
| `ollama_batch_generate` | `prompts`（列表）、`model` | 批量文本生成 |
| `ollama_batch_describe_images` | `input_dir`、`output_dir`、`model` | 通过 Ollama 批量描述图像 |

### ComfyUI（3 个工具）

| 工具 | 参数 | 描述 |
|---|---|---|
| `comfyui_status` | _（无）_ | 检查 ComfyUI 服务器状态 |
| `comfyui_run_workflow` | `workflow`（字典）、`parameters`（字典，可选） | 运行单个 ComfyUI 工作流 |
| `comfyui_run_batch` | `workflow`（字典）、`parameter_sets`（字典列表） | 使用参数扫描运行批量 ComfyUI 工作流 |

### 响应格式（所有工具）

每个工具返回：
```json
{"status": "ok"|"error", "message": "..."}
```

当返回 `"ok"` 时，可能包含额外字段（例如 `caption_stats` 返回 `data`，批量操作返回 `count`）。
当返回 `"error"` 时，`message` 包含错误描述。

---

## 7. 配置参考

### Keyfile 格式（云端 LLM）

具有以下结构的 JSON 文件路径：

```json
{
  "provider": "openai",
  "api_key": "sk-...",
  "api_base": "https://api.openai.com/v1"
}
```

| 字段 | 是否必需 | 描述 |
|---|---|---|
| `provider` | 是 | 供应商标识符：`openai` 或 `deepseek` |
| `api_key` | 是 | API 密钥字符串 |
| `api_base` | 否 | 自定义 API 基础 URL（用于代理或自托管端点） |

**说明：**
- AI 智能体**绝不**生成 API 密钥或 keyfile。仅指导用户自行创建。
- Keyfile 路径必须为绝对路径或相对于工作目录的路径。

### ComfyUI 工作流格式

ComfyUI 工作流是 ComfyUI API 格式的 JSON 对象：

```json
{
  "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"}},
  "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "a beautiful landscape", "clip": ["1", 1]}},
  "3": {"class_type": "KSampler", "inputs": {"seed": 42, "steps": 20, "cfg": 7.0, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0, "model": ["1", 0], "positive": ["2", 0], "negative": ["4", 0], "latent_image": ["5", 0]}},
  "4": {"class_type": "CLIPTextEncode", "inputs": {"text": "bad quality, blurry", "clip": ["1", 1]}},
  "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
  "6": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["1", 2]}},
  "7": {"class_type": "SaveImage", "inputs": {"filename_prefix": "output", "images": ["6", 0]}}
}
```

**说明：**
- 节点 ID 为字符串键（`"1"`、`"2"` 等）。
- 节点引用格式为 `[source_node_id, output_index]`。
- `comfyui_run_batch` 接受 `parameter_sets` 作为字典列表，每个字典覆盖一次批量迭代的节点输入。

### Ollama 设置

1. 安装 Ollama：`curl -fsSL https://ollama.com/install.sh | sh`
2. 拉取支持视觉的模型：`ollama pull llava:13b`
3. 验证：`ollama list`
4. Data Forge MCP 工具默认连接到 `http://localhost:11434`。

---

## 8. 故障排除

### 场景 1：`comfyui_status` 返回错误

**症状：** `{"status": "error", "message": "Connection refused"}`

**原因：** ComfyUI 服务器未运行或使用了其他端口。

**步骤：**
1. 验证 ComfyUI 是否正在运行：检查终端窗口中是否有 ComfyUI 进程。
2. 默认 URL：`http://127.0.0.1:8188`。验证该端口未被防火墙阻止。
3. 重启 ComfyUI，然后重新运行 `comfyui_status`。

### 场景 2：`ollama_list_models` 返回错误

**症状：** `{"status": "error", "message": "Failed to connect to Ollama"}`

**原因：** Ollama 服务未运行。

**步骤：**
1. 启动 Ollama：`ollama serve`
2. 验证：`ollama list`
3. 如果未安装模型：`ollama pull llava:13b`
4. 重新运行 `ollama_list_models`。

### 场景 3：`llm_batch_describe_images` 失败，返回 401

**症状：** `{"status": "error", "message": "401 Unauthorized"}`

**原因：** Keyfile 中的 API 密钥无效或缺失。

**步骤：**
1. 验证 keyfile 存在且包含有效的 `api_key` 字段。
2. 检查密钥是否未被吊销或过期。
3. 验证 `api_base` URL 是否正确（尤其对于 DeepSeek 或代理设置）。
4. 使用最小的单张图像调用进行测试：`llm_describe_image`。

### 场景 4：`remove_background_batch` 失败

**症状：** `{"status": "error", "message": "No module named 'rembg'"}`

**原因：** 未安装 `rembg` Python 包或未下载 BiRefNet 模型。

**步骤：**
1. 安装 rembg：`uv pip install rembg`
2. 下载 BiRefNet 模型：`rembg download`（或等效命令）
3. 验证：`python -c "from rembg import remove"` 成功执行。
4. GPU 加速：确保已安装 CUDA toolkit 和 `onnxruntime-gpu`。

### 场景 5：`caption_import` 在 CSV 上失败

**症状：** `{"status": "error", "message": "Missing required fields"}`

**原因：** CSV 文件列标题不正确或数据缺失。

**步骤：**
1. 必需列：`image`（文件名）、`caption`（文本）。
2. 可选列：`timestamp`、`tags`。
3. 验证无空行，描述文本中无未转义的逗号。
4. 如果数据复杂，尝试以 JSON 而非 CSV 格式导入。

### 场景 6：`caption_search` 无匹配结果

**症状：** 对有效的正则表达式模式找不到结果。

**原因：** 大小写敏感不匹配或文件编码问题。

**步骤：**
1. 验证 `case_sensitive` 参数（默认值可能有所不同）。
2. 检查描述文件编码——非 UTF-8 文件可能导致静默失败。
3. 先用简单的字面模式测试，然后增加正则表达式复杂度。
4. 运行 `caption_read_all` 验证描述是否可访问。

### 场景 7：批量流水线磁盘空间不足

**症状：** 工具返回 `{"status": "error", "message": "No space left on device"}`

**原因：** 中间流水线阶段（resized/、no-bg/、exports/）占用大量磁盘空间。

**步骤：**
1. 估算所需空间：原始大小 × 3（resized + no-bg + exports）。
2. 如果空间紧张，在每个阶段后清理中间目录。
3. 如可用，在其他卷上使用 `--output-dir`。

---

## 9. 外部资源

| Resource | URL |
|---|---|
| Data Forge GitHub | `git@github.com:HaoNaN9279/data_forge.git` |
| Python 3.12 Documentation | `https://docs.python.org/3.12/` |
| FastMCP Documentation | `https://github.com/jlowin/fastmcp` |
| rembg (Background Removal) | `https://github.com/danielgatis/rembg` |
| BiRefNet Models | `https://github.com/ZhengPeng7/BiRefNet` |
| Ollama | `https://ollama.com/` |
| ComfyUI | `https://github.com/comfyanonymous/ComfyUI` |
| uv Package Manager | `https://github.com/astral-sh/uv` |

---

**相关命令：** `/data-forge-dataset`、`/data-forge-process`、`/data-forge-prompt`、`/data-forge-export`

**相关智能体：** Data Forge Development Assistant、Data Forge Data Curator、Data Forge Prompt Engineer
