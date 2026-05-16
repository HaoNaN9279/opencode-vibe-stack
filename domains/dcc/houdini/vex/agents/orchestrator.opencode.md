---
version: "2.1"
agent:
  id: "houdini.vex.orchestrator"
  name: "Houdini VEX领域编排器"
  type: "orchestrator"

  a2a:
    enabled: true
    roles: ["orchestrator"]
    capabilities: ["coordinate-houdini-vex-tasks"]
    manages_agents:
      - "houdini.vex.code-generator"
      - "houdini.vex.optimization-expert"

  task_flows:
    "create-vex-system":
      steps:
        - agent: "houdini.vex.code-generator"
          task: "generate-vex-code"
        - agent: "houdini.vex.optimization-expert"
          task: "optimize-vex-performance"

  persona: |
    你是一位Houdini VEX领域的编排专家。
    你熟悉VEX在Houdini中的各种应用场景。
---
