---
version: "2.1"
name: "${PROJECT_NAME}"
type: "unity-project"
unity_version: "${UNITY_VERSION}"

imports:
  - "${OPCODE_STACK_ROOT}/domains/game-engine/unity/csharp-api/module.opencode.md"
  - "${OPCODE_STACK_ROOT}/domains/game-engine/unity/editor/module.opencode.md"

agents:
  default: "unity.csharp.orchestrator"

mcp_servers:
  - "mcp://unity-editor"
  - "mcp://git"
  - "mcp://filesystem"

rules:
  - "./local.rules.opencode.md"
---
