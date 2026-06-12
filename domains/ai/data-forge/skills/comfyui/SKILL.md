---
name: comfyui
description: 通过 ai_data-forge_comfyui 工具连接 ComfyUI 服务器，支持检查运行状态、执行工作流、批量参数扫描和查看队列。
---

# ComfyUI

## ⚠️ 前置检查
确保 `ai_data-forge_comfyui` 工具已注册。该工具会自动调用 DataForge CLI。
未安装 DataForge：`git clone https://github.com/HaoNan9279/DataForge.git && cd DataForge && uv sync`

## 命令

### `status` — 检查服务器状态
调用 `ai_data-forge_comfyui` 工具，`subcommand=status`，传入 `server` 参数。
```
ai_data-forge_comfyui (subcommand=status, server=http://127.0.0.1:8188)
```

### `run` — 运行单个工作流
调用 `ai_data-forge_comfyui` 工具，`subcommand=run`。
参数：`server` (必填)、`workflow` (必填)、`outputDir` (必填)、`nodeOverride` (可选 JSON 字符串)、`timeout` (可选，默认 30.0)。
```
ai_data-forge_comfyui (subcommand=run, server=http://127.0.0.1:8188, workflow=wf.json, outputDir=./output)
ai_data-forge_comfyui (subcommand=run, server=http://127.0.0.1:8188, workflow=wf.json, outputDir=./out, nodeOverride={"3":{"inputs":{"seed":42}}})
```

### `batch` — 批量参数扫描
调用 `ai_data-forge_comfyui` 工具，`subcommand=batch`。
参数：`server`、`workflow`、`outputDir` (必填)；`paramList` (可选 JSON 数组字符串)；`timeout` (可选，默认 3600)。
```
ai_data-forge_comfyui (subcommand=batch, server=http://127.0.0.1:8188, workflow=wf.json, outputDir=./out)
```

### `queue-size` — 查看队列
调用 `ai_data-forge_comfyui` 工具，`subcommand=queue-size`，传入 `server` 参数。
```
ai_data-forge_comfyui (subcommand=queue-size, server=http://127.0.0.1:8188)
```
