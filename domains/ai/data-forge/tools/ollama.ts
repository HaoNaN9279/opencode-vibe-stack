/**
 * OpenCode custom tool for local Ollama LLM inference.
 *
 * Wraps `uv run python -m data_forge.ollama <subcommand>` to support
 * model listing, text generation, image description, and batch operations.
 *
 * Tool name: data_forge_ollama
 * File:      domains/ai/data-forge/tools/ollama.ts
 */

import { tool } from "@opencode-ai/plugin";
import path from "path";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Resolve the data-forge submodule directory relative to the worktree. */
function submoduleDir(context: { worktree: string }): string {
  return path.join(context.worktree, "domains", "ai", "data-forge", "tools", "data-forge");
}

/** Build CLI arguments for a subcommand, mapping tool args → Python CLI flags. */
function buildCliArgs(args: Record<string, unknown>): string[] {
  const argv: string[] = [args.subcommand as string];

  // Shared options (applied after subcommand to avoid argparser confusion)
  const shared: string[] = [];
  if (args.baseUrl) shared.push("--base-url", args.baseUrl as string);
  if (args.timeout !== undefined) shared.push("--timeout", String(args.timeout));

  const sc = args.subcommand as string;

  if (sc === "list") {
    // list only uses --base-url / --timeout
    argv.push(...shared);
  } else if (sc === "pull") {
    // pull uses --name (not --model)
    argv.push("--name", args.model as string);
    argv.push(...shared);
  } else if (sc === "generate") {
    argv.push("--model", args.model as string);
    argv.push("--prompt", args.prompt as string);
    if (args.system) argv.push("--system", args.system as string);
    if (args.temperature !== undefined) argv.push("--temperature", String(args.temperature));
    argv.push(...shared);
  } else if (sc === "describe") {
    argv.push("--model", args.model as string);
    argv.push("--image", args.image as string);
    if (args.prompt) argv.push("--prompt", args.prompt as string);
    argv.push(...shared);
  } else if (sc === "batch-generate") {
    argv.push("--model", args.model as string);
    argv.push("--input-dir", args.inputDir as string);
    argv.push("--output-dir", args.outputDir as string);
    if (args.system) argv.push("--system", args.system as string);
    if (args.temperature !== undefined) argv.push("--temperature", String(args.temperature));
    argv.push(...shared);
  } else if (sc === "batch-describe") {
    argv.push("--model", args.model as string);
    argv.push("--input-dir", args.inputDir as string);
    argv.push("--output-dir", args.outputDir as string);
    if (args.prompt) argv.push("--prompt", args.prompt as string);
    argv.push(...shared);
  }

  return argv;
}

// ---------------------------------------------------------------------------
// Tool definition
// ---------------------------------------------------------------------------

export const data_forge_ollama = tool({
  description:
    "Interact with a local Ollama server for LLM inference and vision model image description. " +
    "Supports listing installed models, downloading models, text generation (generate), " +
    "image description (describe), and batch operations (batch-generate, batch-describe). " +
    "Requires a running Ollama server (default: http://localhost:11434).",

  args: {
    subcommand: tool.schema
      .enum(["list", "pull", "generate", "describe", "batch-generate", "batch-describe"])
      .describe(
        "Operation: list (list installed models), pull (download a model), " +
          "generate (text completion), describe (image → text via vision model), " +
          "batch-generate (batch text from .txt prompts), " +
          "batch-describe (batch image description from an input directory)",
      ),

    model: tool.schema
      .string()
      .optional()
      .describe(
        "Ollama model name (required for pull, generate, describe, batch-generate, batch-describe). " +
          'Examples: "llama3.2", "gemma3:12b", "llava", "minicpm-v".',
      ),

    prompt: tool.schema
      .string()
      .optional()
      .describe(
        "Text prompt (required for generate; optional for describe/batch-describe, " +
          'default: "Describe this image in detail.").',
      ),

    image: tool.schema
      .string()
      .optional()
      .describe("Path to an image file (required for describe)."),

    inputDir: tool.schema
      .string()
      .optional()
      .describe(
        "Directory containing input files — .txt prompts for batch-generate, " +
          "images for batch-describe.",
      ),

    outputDir: tool.schema
      .string()
      .optional()
      .describe("Directory where generated output text files will be written."),

    system: tool.schema
      .string()
      .optional()
      .describe("Optional system prompt for generate and batch-generate."),

    temperature: tool.schema
      .number()
      .optional()
      .describe("Sampling temperature 0-2 (default: 0.7). Higher = more creative."),

    baseUrl: tool.schema
      .string()
      .optional()
      .default("http://localhost:11434")
      .describe("Ollama server URL (default: http://localhost:11434)."),

    timeout: tool.schema
      .number()
      .optional()
      .default(300)
      .describe("Request timeout in seconds (default: 300)."),
  },

  async execute(args, context) {
    // --- Validation ---
    const sc = args.subcommand as string;

    const needsModel = new Set(["pull", "generate", "describe", "batch-generate", "batch-describe"]);
    if (needsModel.has(sc) && !args.model) {
      return `Error: --model is required for the "${sc}" subcommand.`;
    }

    if (sc === "generate" && !args.prompt) {
      return 'Error: --prompt is required for the "generate" subcommand.';
    }
    if (sc === "describe" && !args.image) {
      return 'Error: --image is required for the "describe" subcommand.';
    }
    const needsIO = new Set(["batch-generate", "batch-describe"]);
    if (needsIO.has(sc)) {
      if (!args.inputDir) return `Error: --input-dir is required for the "${sc}" subcommand.`;
      if (!args.outputDir) return `Error: --output-dir is required for the "${sc}" subcommand.`;
    }

    // --- Invoke CLI ---
    const workDir = submoduleDir(context);
    const cliArgs = buildCliArgs(args);

    try {
      const result =
        await Bun.$`uv run --directory ${workDir} python -m data_forge.ollama ${cliArgs}`.text();
      return result.trim() || "(no output)";
    } catch (error: unknown) {
      // Detect connection failures
      if (error instanceof Error) {
        const msg = error.message;
        if (/connect|refused|unreachable|timeout/i.test(msg)) {
          return (
            `Error: Cannot connect to Ollama server at ${args.baseUrl ?? "http://localhost:11434"}.\n` +
            "Make sure Ollama is running (`ollama serve`) and the URL is correct."
          );
        }
        return `Error: ${msg}`;
      }
      return `Error: ${String(error)}`;
    }
  },
});
