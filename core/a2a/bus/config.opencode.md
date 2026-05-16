---
version: "2.1"
message_bus:
  type: "in-process"
  port: 5100
  enable_encryption: true

  registry:
    enable_auto_discovery: true
    heartbeat_interval: 5s
    timeout: 30s
---
