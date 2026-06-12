import { tool } from "@opencode-ai/plugin"
import path from "path"

// ---------------------------------------------------------------------------
// Vibe Stack home resolution
// ---------------------------------------------------------------------------

/** Resolve the vibe-stack repository root directory. */
function resolveVibeStackHome(worktree: string): string {
  // 1. VIBE_STACK_HOME environment variable (set during install)
  const envHome = process.env.VIBE_STACK_HOME
  if (envHome) return envHome

  // 2. Common default install location
  const home = process.env.USERPROFILE || process.env.HOME || "~"
  return path.join(home, ".opencode-vibe-stack")
}

// ---------------------------------------------------------------------------
// Tool definition
// ---------------------------------------------------------------------------

const data_forge_convert = tool({
  description:
    "Convert images between formats: PNG, JPG, JPEG, WebP, BMP. " +
    "Supports single-file conversion and batch directory conversion " +
    "with optional alpha-channel background-fill and JPEG/WebP quality control. " +
    "Powered by DataForge (Pillow).",

  args: {
    input: tool.schema
      .string()
      .describe("Source image path (single mode) or source directory (batch mode)"),
    output: tool.schema
      .string()
      .describe(
        "Output image path (single mode) or output directory (batch mode)"
      ),
    format: tool.schema
      .enum(["png", "jpg", "jpeg", "webp", "bmp"])
      .optional()
      .describe(
        "Target output format for batch mode. When provided, the conversion " +
        "runs in batch mode and all images in the input directory are converted. " +
        "Omit to convert a single file (format auto-detected from output extension)."
      ),
    quality: tool.schema
      .number()
      .optional()
      .default(95)
      .describe("JPEG / WebP quality (1-100, default: 95)"),
    background: tool.schema
      .string()
      .optional()
      .default("#FFFFFF")
      .describe(
        "Hex background color for alpha-channel fill, e.g. '#FFFFFF' (default). " +
        "Useful when converting RGBA → RGB formats."
      ),
  },

  async execute(args, context) {
    // ── Resolve the data-forge Python submodule directory ──
    const vibeHome = resolveVibeStackHome(context.worktree)
    const submoduleDir = path.join(
      vibeHome,
      "domains",
      "ai",
      "data-forge",
      "tools",
      "data-forge"
    )

    // ── Build CLI arguments ──
    const isBatch = args.format !== undefined

    const cliArgs: string[] = [
      "--directory",
      submoduleDir,
      "python",
      "-m",
      "data_forge.convert",
      isBatch ? "batch" : "single",
    ]

    if (isBatch) {
      cliArgs.push("--input-dir", args.input)
      cliArgs.push("--output-dir", args.output)
      cliArgs.push("--target-format", args.format!)
    } else {
      cliArgs.push("--input", args.input)
      cliArgs.push("--output", args.output)
    }

    cliArgs.push("--quality", String(args.quality))
    cliArgs.push("--background-color", args.background)

    // ── Execute ──
    try {
      const result =
        await Bun.$`uv ${cliArgs}`.text()
      return result.trim()
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error)
      return `data-forge convert failed: ${msg}`
    }
  },
})

export default data_forge_convert
