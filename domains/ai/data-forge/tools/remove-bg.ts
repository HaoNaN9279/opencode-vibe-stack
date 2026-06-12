import { tool } from "@opencode-ai/plugin"
import path from "path"

export const data_forge_remove_bg = tool({
  description:
    "Remove image backgrounds using BiRefNet models (via rembg). Supports single-image processing with configurable model and background color.",
  args: {
    input: tool.schema.string().describe("Source image path"),
    output: tool.schema.string().describe("Output image path"),
    model: tool.schema
      .string()
      .optional()
      .default("birefnet-general")
      .describe(
        "BiRefNet model variant (birefnet-general, birefnet-general-lite, birefnet-portrait, birefnet-dis, birefnet-hrsod, birefnet-cod, birefnet-massive)",
      ),
    background: tool.schema
      .string()
      .optional()
      .default("#FFFFFF")
      .describe("Background fill color in hex format (e.g. #FFFFFF, #000000)"),
  },
  async execute(args, context) {
    const submoduleDir = path.join(
      context.worktree,
      ".opencode/tools/data-forge",
    )
    try {
      const result =
        await Bun.$`uv run --directory ${submoduleDir} python -m data_forge.remove_bg single --input ${args.input} --output ${args.output} --model ${args.model} --background-color ${args.background}`.text()
      return result.trim()
    } catch (error) {
      return `Background removal failed: ${error instanceof Error ? error.message : String(error)}`
    }
  },
})
