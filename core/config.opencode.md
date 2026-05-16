---
version: "2.1"
global:
  vibe_coding:
    enabled: true
    style: "intuitive-first"
    context_window: "auto"
    incremental_changes: true

  code_standards:
    comment_style: "self-documenting"
    error_handling: "defensive"
    performance_notes: true
    security_checks: true

imports:
  - "./a2a/protocol/messages.opencode.md"
  - "./a2a/bus/config.opencode.md"
  - "./rules/*.opencode.md"
  - "./skills/*.opencode.md"
  - "./agents/*.opencode.md"
  - "./mcp/*.opencode.md"
  - "./combinator/*.opencode.md"

conditional_imports:
  - condition: "platform == 'windows'"
    imports:
      - "../../platforms/windows/config.opencode.md"
  - condition: "platform == 'wsl2'"
    imports:
      - "../../platforms/wsl2/config.opencode.md"
  - condition: "platform == 'linux'"
    imports:
      - "../../platforms/linux/config.opencode.md"
---
