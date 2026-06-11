---
name: comfyui
description: 通过 DataForge CLI 连接 ComfyUI 服务器，支持检查运行状态、执行工作流、批量参数扫描和查看队列。
---

# ComfyUI

## ⚠️ 前置检查
```
data-forge --help
```
未安装：`git clone https://github.com/HaoNan9279/DataForge.git && cd DataForge && uv sync`

## 命令

### `comfyui status` — 检查服务器状态
- `--server` (必填) ComfyUI URL
```
data-forge comfyui status --server http://127.0.0.1:8188
```

### `comfyui run` — 运行单个工作流
- `--server` (必填) | `--workflow` (必填) JSON 路径 | `--output-dir` (必填)
- `--node-override` (可选) JSON 节点覆盖 | `--timeout` (默认 30.0)
```
data-forge comfyui run --server http://127.0.0.1:8188 --workflow wf.json --output-dir ./output
data-forge comfyui run --server http://127.0.0.1:8188 --workflow wf.json --output-dir ./out --node-override '{"3":{"inputs":{"seed":42}}}'
```

### `comfyui batch` — 批量参数扫描
- `--server` `--workflow` `--input-dir` `--output-dir` (必填)
- `--seed-strategy` (默认 round: round/random/sequential)
- `--seeds-per-image` (默认 4) | `--total-rounds` (默认 4)
- `--timeout` (默认 3600) | `--poll-interval` (默认 5.0)
- `--no-skip` | `--node-override`
```
data-forge comfyui batch --server http://127.0.0.1:8188 --workflow wf.json --input-dir ./images --output-dir ./out
```

### `comfyui queue-size` — 查看队列
- `--server` (必填)
```
data-forge comfyui queue-size --server http://127.0.0.1:8188
```
