# DataForge 领域规则

仓库：https://github.com/HaoNaN9279/data_forge.git

## 前置检查

使用本领域任何工具前，确认 DataForge submodule 已初始化：

```bash
git submodule update --init --recursive
```

DataForge submodule 已通过项目初始化在 `domains/ai/data-forge/tools/data-forge/` 就绪。

## 工具索引

| 工具 | Tool 名称 | 详细参考 |
|------|-----------|----------|
| ComfyUI Client | `data-forge-comfyui` | 加载 `comfyui` skill |
| Image Resize | `data-forge-resize` | 加载 `resize` skill |
| Image Converter | `data-forge-convert` | 加载 `convert` skill |
| Background Removal | `data-forge-remove-bg` | 加载 `remove-bg` skill |
| Ollama Client | `data-forge-ollama` | 加载 `ollama` skill |
| LLM Client | `data-forge-llm` | 加载 `llm` skill |
| Caption Editor | `data-forge-caption` | 加载 `caption` skill |

## 典型工作流

```
data-forge-resize → [data-forge-remove-bg] → [data-forge-convert] → data-forge-llm / data-forge-ollama → data-forge-caption → data-forge-comfyui
```
