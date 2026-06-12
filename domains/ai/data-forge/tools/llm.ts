/**
 * DataForge LLM Tool — Cloud LLM text generation and image description.
 *
 * Wraps ``python -m data_forge.llm`` CLI, which uses any OpenAI-compatible
 * API provider (OpenAI, DeepSeek, Groq, Together, vLLM, Ollama, etc.).
 *
 * Subcommands:
 *   chat            — Single-turn text generation
 *   describe        — Image description via vision model
 *   batch-chat      — Batch text generation from prompt files
 *   batch-describe  — Batch image description
 *   list-providers  — List configured providers from keyfile
 */
import { tool } from "@opencode-ai/plugin"
import path from "path"

// ---------------------------------------------------------------------------
// Tool definition
// ---------------------------------------------------------------------------

const data_forge_llm = tool({
  description:
    "Cloud LLM text generation and image description via OpenAI-compatible APIs. " +
    "Supports chat, describe, batch-chat, batch-describe, and list-providers subcommands. " +
    "Requires a JSON keyfile with provider credentials (or KEYFILE environment variable).",

  args: {
    // ── Subcommand ────────────────────────────────────────────────────
    subcommand: tool.schema
      .enum(["chat", "describe", "batch-chat", "batch-describe", "list-providers"])
      .describe(
        "Operation to perform: chat = single text generation; describe = image description; " +
          "batch-chat = batch text generation from .txt files; " +
          "batch-describe = batch image description; list-providers = show available providers.",
      ),

    // ── Core (required per subcommand) ─────────────────────────────────
    provider: tool.schema
      .string()
      .optional()
      .describe(
        "Provider name defined in keyfile, e.g. 'openai', 'deepseek'. Required for chat, describe, batch-chat, batch-describe.",
      ),
    model: tool.schema
      .string()
      .optional()
      .describe(
        "Model name, e.g. 'gpt-4o', 'deepseek-chat'. Required for chat, describe, batch-chat, batch-describe.",
      ),

    // ── Chat / describe ────────────────────────────────────────────────
    prompt: tool.schema
      .string()
      .optional()
      .describe(
        "User prompt text. Required for 'chat'. Optional for 'describe' and 'batch-describe' (defaults to image description prompt).",
      ),
    image: tool.schema
      .string()
      .optional()
      .describe("Path to an image file. Required for 'describe' subcommand."),

    // ── Batch operations ───────────────────────────────────────────────
    inputDir: tool.schema
      .string()
      .optional()
      .describe(
        "Input directory: .txt prompt files for 'batch-chat', image files for 'batch-describe'.",
      ),
    outputDir: tool.schema
      .string()
      .optional()
      .describe("Output directory for batch results."),

    // ── Keyfile ────────────────────────────────────────────────────────
    keyfile: tool.schema
      .string()
      .optional()
      .describe(
        "Path to a JSON keyfile mapping provider names to {api_key, base_url}. " +
          "If omitted, the KEYFILE environment variable is used. Required for all subcommands.",
      ),

    // ── Optional tunables ──────────────────────────────────────────────
    system: tool.schema
      .string()
      .optional()
      .describe("System message. Supported by 'chat' and 'batch-chat' subcommands."),
    temperature: tool.schema
      .number()
      .optional()
      .default(0.7)
      .describe("Sampling temperature (0.0–2.0, default: 0.7)."),
    maxTokens: tool.schema
      .number()
      .optional()
      .describe("Maximum tokens to generate."),
  },

  async execute(args, context) {
    // Resolve the data-forge Python package directory.
    // In a vibe-stack activated project, tools/ is linked from
    // domains/ai/data-forge/tools/, so the data-forge/ subdirectory
    // lives at .opencode/tools/data-forge/ relative to worktree.
    const dataForgeDir = path.join(context.worktree, ".opencode", "tools", "data-forge")

    // ── Build CLI argument array ───────────────────────────────────
    const subArgs: string[] = []

    const flag = (f: string, v: unknown) => {
      if (v !== undefined && v !== null) subArgs.push(f, String(v))
    }

    switch (args.subcommand) {
      case "chat": {
        flag("--prompt", args.prompt)
        flag("--provider", args.provider)
        flag("--model", args.model)
        flag("--system", args.system)
        flag("--temperature", args.temperature)
        flag("--max-tokens", args.maxTokens)
        flag("--keyfile", args.keyfile)
        break
      }
      case "describe": {
        flag("--image", args.image)
        flag("--provider", args.provider)
        flag("--model", args.model)
        flag("--prompt", args.prompt)
        flag("--temperature", args.temperature)
        flag("--max-tokens", args.maxTokens)
        flag("--keyfile", args.keyfile)
        break
      }
      case "batch-chat": {
        flag("--input-dir", args.inputDir)
        flag("--output-dir", args.outputDir)
        flag("--provider", args.provider)
        flag("--model", args.model)
        flag("--system", args.system)
        flag("--temperature", args.temperature)
        flag("--max-tokens", args.maxTokens)
        flag("--keyfile", args.keyfile)
        break
      }
      case "batch-describe": {
        flag("--input-dir", args.inputDir)
        flag("--output-dir", args.outputDir)
        flag("--provider", args.provider)
        flag("--model", args.model)
        flag("--prompt", args.prompt)
        flag("--temperature", args.temperature)
        flag("--max-tokens", args.maxTokens)
        flag("--keyfile", args.keyfile)
        break
      }
      case "list-providers": {
        flag("--keyfile", args.keyfile)
        break
      }
    }

    const cliArgs: string[] = [args.subcommand, ...subArgs]

    try {
      const result =
        await Bun.$`uv run python -m data_forge.llm ${cliArgs}`
          .cwd(dataForgeDir)
          .quiet()
          .text()

      return result.trim()
    } catch (error: unknown) {
      // Bun.ShellError carries stderr as .stderr (Buffer) — extract it
      const stderr =
        error && typeof error === "object" && "stderr" in error
          ? String((error as { stderr: Buffer }).stderr).trim()
          : ""
      return `DataForge LLM error: ${stderr || String(error)}`
    }
  },
})

export default data_forge_llm
