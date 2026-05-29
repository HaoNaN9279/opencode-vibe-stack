# Data Forge MCP Configuration

This directory contains the Data Forge MCP server configuration and the git submodule pointing to the [data_forge](https://github.com/HaoNaN9279/data_forge) repository.

## Structure

```
mcp/
├── data-forge.json        # MCP server configuration for OMO/OpenCode
├── data_forge/            # Git submodule — the actual MCP server code
└── README.md              # This file
```

## How It Works

When this domain is activated via `vibe-stack activate ai/data_forge`:

1. `vibe-stack` reads `data-forge.json` from this directory
2. Resolves `${VIBE_STACK_HOME}` placeholders to absolute paths
3. Adds `vibe:` namespace prefix (→ `vibe:data-forge`)
4. Merges the entry into `.opencode/opencode.json` under the `mcp` key
5. OpenCode auto-discovers and connects to the MCP server on next startup

When deactivated, the `vibe:data-forge` entry is removed from `.opencode/opencode.json`.

## Prerequisites

- **Python >= 3.12** — required by Data Forge
- **uv** — Python package manager, used to run the MCP server
- **Git** — for submodule initialization

## Setup

1. **Initialize the submodule** (if not already done):
   ```bash
   git submodule update --init --recursive
   ```

2. **Install dependencies** (from the submodule directory):
   ```bash
   cd domains/ai/data_forge/mcp/data_forge
   uv sync
   ```

3. **Optional: Install rembg for background removal**:
   ```bash
   cd domains/ai/data_forge/mcp/data_forge
   uv sync --extra rembg
   ```

4. **Configure API keys** (if using cloud LLM tools):
   Create `domains/ai/data_forge/mcp/data_forge/src/data_forge/resources/keys.json`:
   ```json
   {
     "openai": {
       "api_key": "sk-...",
       "base_url": "https://api.openai.com/v1"
     }
   }
   ```

5. **Configure ComfyUI workflows** (optional):
   Place API-format workflow JSON files in `domains/ai/data_forge/mcp/data_forge/src/data_forge/resources/ComfyUI_workflows/`.

## Configuration Reference

The `data-forge.json` file uses the OpenCode native `mcp` configuration format:

```json
{
  "mcp": {
    "data-forge": {
      "type": "local",
      "command": [
        "uv",
        "run",
        "--directory",
        "${VIBE_STACK_HOME}/domains/ai/data_forge/mcp/data_forge",
        "data-forge-mcp"
      ],
      "enabled": true
    }
  }
}
```

| Field | Description |
|---|---|
| `type` | Must be `"local"` for stdio-based MCP servers |
| `command` | Full command array (executable + arguments) |
| `enabled` | Whether the server starts automatically |
| `${VIBE_STACK_HOME}` | Placeholder resolved at activation time |

> **Naming**: The server name `data-forge` in this file is automatically prefixed with `vibe:` when written to `.opencode/opencode.json` (→ `vibe:data-forge`), preventing collisions with user or Claude Code MCPs.

## Available MCP Tools (24)

| Category | Tools |
|---|---|
| **Resize** | `resize_images` |
| **Background Removal** | `remove_background`, `remove_background_batch` |
| **Captions** | `caption_list`, `caption_read`, `caption_read_all`, `caption_search`, `caption_batch_replace`, `caption_export`, `caption_import`, `caption_stats`, `caption_deduplicate` |
| **LLM (Cloud)** | `llm_chat`, `llm_describe_image`, `llm_batch_chat`, `llm_batch_describe_images` |
| **Ollama (Local)** | `ollama_generate`, `ollama_list_models`, `ollama_describe_image`, `ollama_batch_generate`, `ollama_batch_describe_images` |
| **ComfyUI** | `comfyui_status`, `comfyui_run_workflow`, `comfyui_run_batch` |
