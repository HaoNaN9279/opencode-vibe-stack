---
version: "2.1"
a2a_registry:
  enable_auto_discovery: true
  discovery_protocol: "broadcast"

  indexing:
    scan_paths:
      - "${OPCODE_STACK_ROOT}/domains"
      - "${OPCODE_STACK_ROOT}/combinations"
    scan_pattern: "**/agents/*.opencode.md"

  health_check:
    interval: 10s
    timeout: 5s
    retries: 3
---
