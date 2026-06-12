# DataForge 领域规则

GitHub 仓库：https://github.com/HaoNan9279/DataForge.git

## CLI 安装检查

使用本领域任何命令前，先确认 `data-forge` CLI 已安装：

```bash
data-forge --help
```

如未安装，提示用户：
```bash
git clone https://github.com/HaoNan9279/DataForge.git && cd DataForge && uv sync
# 可选: uv sync --extra rembg | uv sync --extra opencv
```

## 工具索引

| 工具 | CLI 命令 | 详细参考 |
|------|----------|----------|
| ComfyUI Client | `data-forge comfyui` | 加载 `comfyui` skill |
| Image Resize | `data-forge resize` | 加载 `resize` skill |
| Image Converter | `data-forge convert` | 加载 `convert` skill |
| Background Removal | `data-forge remove-bg` | 加载 `remove-bg` skill |
| Ollama Client | `data-forge ollama` | 加载 `ollama` skill |
| LLM Client | `data-forge llm` | 加载 `llm` skill |
| Caption Editor | `data-forge caption` | 加载 `caption` skill |

## 典型工作流

```
resize → [remove-bg] → [convert] → llm/ollama batch-describe → caption stats/search/replace → comfyui batch
```

## 废弃命令

| 废弃 | 替代 |
|------|------|
| `data-forge batch` | `data-forge comfyui batch` |
| `data-forge status` | `data-forge comfyui status` |
