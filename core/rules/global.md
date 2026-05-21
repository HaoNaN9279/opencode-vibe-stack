# 全局规则

## Vibe Coding 风格

- 先输出整体设计思路，再写代码
- 优先使用用户熟悉的设计模式和命名风格
- 自动识别项目类型并应用对应领域规则
- 保留注释但避免过度注释
- 增量修改时只输出变化的部分
- 默认启用直观优先风格，自适应上下文窗口

## 代码标准

- 注释风格：自文档化（用清晰的命名和结构代替注释）
- 错误处理：防御式编程，提前检查边界条件和异常路径
- 性能标注：生成代码时说明关键性能考量
- 安全检查：检查输入验证、路径遍历、注入风险

## 安全规则

- 不要硬编码密钥或凭证
- 不要在代码中暴露敏感路径
- 文件操作必须做路径安全检查
- shell命令必须做参数转义

## 命名规范

- 遵循各语言官方命名规范
- 领域专用术语保持一致
- 文件名使用小写+连字符（kebab-case）
- 模块ID使用点分命名空间（如 `game-engine.unity.csharp-api`）

## Combinator 引擎

加载优先级（由高到低）：

1. **project** — 项目的 `opencode/` 内容优先级最高
2. **domains** — 领域模块内容次之
3. **core** — 核心基础规则最低

冲突解决策略：

- skills：合并，同名时重命名避免冲突
- agents：优先使用高优先级来源的版本
- rules：全部合并
- mcp_servers：全部合并，去重
- 懒加载：仅在需要时解析模块资源

## A2A 通信协议

### 协议版本

1.0

### 消息总线

- 类型：进程内通信
- 端口：5100
- 加密：启用
- 心跳间隔：5 秒
- 超时：30 秒

### 消息类型

| 消息类型 | 说明 |
|----------|------|
| TaskRequest | 向 Agent 发送任务请求，包含 task_id、task_type、context、priority、deadline |
| TaskResponse | Agent 返回任务结果，包含 status（pending/running/completed/failed）、result、progress |
| AgentHello | Agent 上线时广播 |
| AgentGoodbye | Agent 下线时广播 |
| CapabilityQuery | 查询 Agent 的能力 |
| CapabilityResponse | 返回 Agent 的能力列表 |
| SubtaskAssign | 编排器向子 Agent 分配子任务 |
| SubtaskComplete | 子 Agent 向编排器报告子任务完成 |

### Agent 发现

- Core 路径：`~/.config/opencode/agents`
- 项目路径：`<project>/opencode/agents`
- 文件匹配：`*.md`
