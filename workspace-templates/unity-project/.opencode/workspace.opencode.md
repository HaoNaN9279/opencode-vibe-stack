---
version: "2.1"
name: "${PROJECT_NAME}"
type: "unity-project"
unity_version: "${UNITY_VERSION}"

imports:
  - "${OPCODE_STACK_ROOT}/domains/game-engine/unity/editor/module.opencode.md"

agents:
  default: "unity.csharp.orchestrator"

mcp_servers:
  - "mcp://unity-editor"
  - "mcp://git"
  - "mcp://filesystem"

skills:
  paths:
    - "${OPCODE_STACK_ROOT}/domains/game-engine/unity/csharp-api/skills"
    - "${OPCODE_STACK_ROOT}/domains/game-engine/unity/editor/skills"

rules:
  - "./local.rules.opencode.md"
---