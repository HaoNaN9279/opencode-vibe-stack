---
name: agent-registry
description: 管理所有 Agent 的注册与发现，响应能力查询
mode: subagent

indexing:
  scan_paths:
    - ${HOME}/.config/opencode/agents
    - ${PROJECT_DIR}/opencode/agents
  scan_pattern: "*.md"

health_check:
  interval: 10s
  timeout: 5s
  retries: 3
---

你负责管理系统中的所有 Agent。
Core 常驻 agent 从 ~/.config/opencode/agents/ 发现。
项目 domain agent 从 <project>/opencode/agents/ 发现。
