---
name: hn-unity-mcp
description: 当用户需要通过 MCP 与 Unity Editor 交互时使用，包括获取编译错误、控制台日志等 Unity Editor 操作
license: MIT
compatibility: opencode
metadata:
  audience: developers
  category: domain-config
---

# Unity MCP 桥接技能

通过 MCP（Model Context Protocol）在 OpenCode 与 Unity Editor 之间建立实时双向通信。本技能封装了 HNUnityMCP 桥接层，让 AI 可以直接读取 Unity Editor 状态（如编译错误）并执行编辑器操作。

---

## Unity MCP 概述

hn-unity-mcp 是一个 Python MCP Server，通过 HTTP 与 Unity Editor 内的 HNUnityMCP 编辑器扩展通信。Unity Editor 中的扩展在端口 18080 上提供 REST API，本技能作为 OpenCode 侧的 MCP 工具层，将编辑器能力暴露为可调用的工具。

架构链路：

```
OpenCode AI → hn-unity-mcp (MCP Server) → HTTP → Unity Editor (HNUnityMCP 扩展)
```

---

## 前置条件

在使用本技能前，请确保以下条件满足：

1. **Unity Editor 正在运行**，且已打开目标项目
2. **HNUnityMCP 编辑器扩展已安装**，位于 Unity 项目的 `Assets/Editor/HNUnityMCP/` 目录下
3. **Python MCP Server 可用**，通过 `hn-unity-mcp` 命令启动
4. **端口 18080 可达**，Unity Editor 的 HTTP 桥接已启动
5. **领域栈已激活**，已加载 `game-dev/unity` 领域的完整配置
6. **Windows 端口 ACL**（首次使用）：以管理员身份执行 `netsh http add urlacl url=http://+:18080/ user=Everyone`

---

## 可用工具

当前 `unity_mcp_tools.json` 中注册的工具如下：

| 工具名称 | 描述 |
|---------|------|
| `get_compile_errors` | 获取 Unity 控制台中的编译错误和警告信息 |

### 扩展计划

以下工具位已预留，将在后续版本中逐步实现：

| 工具名称 | 描述 |
|---------|------|
| `list_scenes` | 列出项目中所有场景 |
| `open_scene` | 在编辑器中打开指定场景 |
| `get_game_objects` | 获取当前场景中的 GameObject 层级结构 |
| `execute_menu` | 执行 Unity 编辑器菜单命令 |
| `run_editmode_tests` | 运行 Edit Mode 测试 |
| `run_playmode_tests` | 运行 Play Mode 测试 |
| `get_console_log` | 获取编辑器控制台日志 |
| `set_prefab` | 修改 Prefab 属性 |
| `execute_unity_command` | 执行自定义 Unity 编辑器命令 |

---

## 调用方式

通过 `skill_mcp` 工具调用 MCP 工具：

```python
# 获取 Unity 编译错误
skill_mcp(mcp_name="hn-unity-mcp", tool_name="get_compile_errors", arguments="{}")
```

返回结果包含编译错误列表及其摘要统计（错误数、警告数）。

---

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `UNITY_MCP_HOST` | `localhost` | Unity MCP 服务主机地址 |
| `UNITY_MCP_PORT` | `18080` | Unity MCP 服务端口 |

---

## 常见问题

### skill_mcp 返回 "connection refused"

可能的原因：

1. **Unity Editor 未运行** — 打开 Unity Editor 并加载目标项目
2. **HNUnityMCP 插件缺失** — 确认插件已放入 `Assets/Editor/HNUnityMCP/`
3. **端口错误** — 确认 `UNITY_MCP_PORT` 环境变量与编辑器实际端口一致
4. **端口 ACL 未配置**（Windows）— 以管理员身份运行 `netsh http add urlacl url=http://+:18080/ user=Everyone`
5. **Python MCP Server 未启动** — 运行 `hn-unity-mcp` 命令启动服务

### 调用成功但没有工具返回

1. 确认技能已正确加载（`skill_mcp` 可识别 `mcp_name="hn-unity-mcp"`）
2. 检查 `mcp.json` 中 hn-unity-mcp 的配置是否正确
3. 重新加载技能后重试

### 获取到空结果

1. `get_compile_errors` 返回空列表表示项目无编译错误
2. 确认 Unity Editor 已完成编译（等待编译进度条消失）

---

## 参考

- 领域 MCP 配置：`mcp/unity.json` — hn-unity-mcp 注册配置
- MCP 源码：`mcp/HNUnityMCP/` — 完整的 MCP 桥接实现（Python Server + Unity Editor 扩展）
- 父技能：`skills/unity/SKILL.md` — Unity 游戏开发完整技能
