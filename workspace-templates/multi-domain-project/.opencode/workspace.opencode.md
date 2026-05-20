---
version: "2.1"
name: "${PROJECT_NAME}"
type: "multi-domain"

domains:
  - "${DOMAIN_LIST}"

imports:
  - "${OPCODE_STACK_ROOT}/combinations/game-asset-pipeline/combination.opencode.md"

combinator:
  conflict_resolution: "workspace-override"
  priority: ["workspace", "combinations", "domains", "core"]
  lazy_load: true

agents:
  default: "core.dynamic-orchestrator"

mcp_servers:
  - "mcp://git"
  - "mcp://filesystem"

rules:
  - "./local.rules.opencode.md"
---