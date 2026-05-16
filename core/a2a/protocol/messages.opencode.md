---
version: "2.1"
a2a_protocol: "1.0"

message_types:
  - name: "TaskRequest"
    description: "向Agent发送任务请求"
    fields:
      task_id: string
      task_type: string
      description: string
      context: object
      priority: int
      deadline: timestamp

  - name: "TaskResponse"
    description: "Agent返回任务结果"
    fields:
      task_id: string
      status: "pending|running|completed|failed"
      result: object
      error: string
      progress: float

  - name: "AgentHello"
    description: "Agent上线时广播"

  - name: "AgentGoodbye"
    description: "Agent下线时广播"

  - name: "CapabilityQuery"
    description: "查询Agent的能力"

  - name: "CapabilityResponse"
    description: "返回Agent的能力列表"

  - name: "SubtaskAssign"
    description: "编排器向子Agent分配子任务"

  - name: "SubtaskComplete"
    description: "子Agent向编排器报告子任务完成"
---
