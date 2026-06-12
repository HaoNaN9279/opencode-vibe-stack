/**
 * DataForge ComfyUI — 自定义工具
 *
 * 通过 DataForge CLI (python -m data_forge.comfyui) 连接 ComfyUI 服务器，
 * 支持: status / run / batch / queue-size 子命令。
 *
 * 工具名: data_forge_comfyui
 */

import { tool } from "@opencode-ai/plugin"
import path from "path"

const TIMEOUT_MS = 120_000  // 默认总超时 120s

export const data_forge_comfyui = tool({
  description: [
    "通过 DataForge CLI 连接 ComfyUI 服务器。",
    "子命令:",
    "  status     — 检查服务器运行状态",
    "  run        — 执行单个工作流并下载输出",
    "  batch      — 批量参数扫描",
    "  queue-size — 查看执行队列大小",
  ].join("\n"),

  args: {
    subcommand: tool.schema
      .enum(["status", "run", "batch", "queue-size"])
      .describe("子命令"),

    server: tool.schema
      .string()
      .describe("ComfyUI 服务器地址，如 http://127.0.0.1:8188"),

    workflow: tool.schema
      .string()
      .optional()
      .describe("工作流 JSON 文件路径 (run / batch 需要)"),

    outputDir: tool.schema
      .string()
      .optional()
      .describe("输出目录路径 (run / batch 需要)"),

    nodeOverride: tool.schema
      .string()
      .optional()
      .describe("JSON 字符串，节点覆盖参数 (run 可选)"),

    paramList: tool.schema
      .string()
      .optional()
      .describe("JSON 数组字符串，批量参数列表 (batch 需要)"),

    timeout: tool.schema
      .number()
      .optional()
      .describe("单次请求超时秒数 (run / batch 有效，默认由 CLI 决定)"),
  },

  async execute(args, context) {
    // ── 解析 DataForge 项目路径 ──
    const dataForgeDir = path.join(
      context.worktree,
      ".opencode",
      "tools",
      "data-forge",
    )

    // ── 构建 CLI 命令参数 ──
    const cmd = [
      "uv",
      "run",
      "--directory",
      dataForgeDir,
      "python",
      "-m",
      "data_forge.comfyui",
      args.subcommand,
    ]

    // 通用参数
    if (args.server) cmd.push("--server", args.server)

    // run / batch 参数
    if (args.workflow) cmd.push("--workflow", args.workflow)
    if (args.outputDir) cmd.push("--output-dir", args.outputDir)
    if (args.nodeOverride) cmd.push("--node-override", args.nodeOverride)
    if (args.paramList) cmd.push("--param-list", args.paramList)
    if (args.timeout !== undefined && (args.subcommand === "run" || args.subcommand === "batch")) {
      cmd.push("--timeout", String(args.timeout))
    }

    // ── 执行 & 超时控制 ──
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)

    try {
      const proc = Bun.spawn(cmd, {
        stdout: "pipe",
        stderr: "pipe",
        env: { ...process.env },
      })

      // 等待进程结束，同时监听 abort 信号
      const exitCode = await new Promise<number>((resolve, reject) => {
        const onAbort = () => {
          proc.kill()
          reject(new Error("TIMEOUT"))
        }
        controller.signal.addEventListener("abort", onAbort, { once: true })

        proc.exited.then((code) => {
          controller.signal.removeEventListener("abort", onAbort)
          resolve(code)
        })
      })

      clearTimeout(timer)

      const stdout = await new Response(proc.stdout).text()
      const stderr = await new Response(proc.stderr).text()

      if (exitCode !== 0) {
        const errMsg = stderr.trim() || stdout.trim() || "未知错误"
        return `ComfyUI ${args.subcommand} 失败 (退出码 ${exitCode}):\n${errMsg}`
      }

      return stdout.trim() || `ComfyUI ${args.subcommand} 完成 (无输出)`
    } catch (error: unknown) {
      clearTimeout(timer)

      // 超时
      if (error instanceof Error && error.message === "TIMEOUT") {
        return `ComfyUI ${args.subcommand} 超时 (>${TIMEOUT_MS / 1000}s): 无法连接到 ${args.server || "服务器"}，请确认 ComfyUI 是否正在运行`
      }

      // 其他异常
      const msg = error instanceof Error ? error.message : String(error)
      return `ComfyUI ${args.subcommand} 异常: ${msg}`
    }
  },
})
