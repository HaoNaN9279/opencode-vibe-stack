import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description: "Batch resize images with aspect-ratio preservation and optional padding",
  args: {
    inputDir: tool.schema.string().describe("Source image directory path"),
    outputDir: tool.schema.string().describe("Output directory path"),
    width: tool.schema.number().describe("Target width in pixels"),
    height: tool.schema.number().describe("Target height in pixels"),
    fitLongEdge: tool.schema
      .boolean()
      .optional()
      .default(false)
      .describe("Fit the long edge within target dimensions instead of exact resize"),
    padToFit: tool.schema
      .boolean()
      .optional()
      .default(false)
      .describe("Pad image to exact target size instead of cropping"),
    overwrite: tool.schema
      .boolean()
      .optional()
      .default(false)
      .describe("Overwrite existing output files"),
  },
  async execute(args, context) {
    const dataForgeDir = path.join(
      context.worktree,
      "domains",
      "ai",
      "data-forge",
      "tools",
      "data-forge",
    )
    const inputDir = path.resolve(context.directory, args.inputDir)
    const outputDir = path.resolve(context.directory, args.outputDir)

    const cmdArgs: string[] = [
      "run",
      "--directory",
      dataForgeDir,
      "python",
      "-m",
      "data_forge.resize",
      "--input-dir",
      inputDir,
      "--output-dir",
      outputDir,
      "--width",
      String(args.width),
      "--height",
      String(args.height),
    ]

    if (args.fitLongEdge) cmdArgs.push("--fit-long-edge")
    if (args.padToFit) cmdArgs.push("--pad-to-fit")
    if (args.overwrite) cmdArgs.push("--overwrite")

    try {
      const result = await Bun.$`uv ${cmdArgs}`.text()
      return result.trim()
    } catch (error) {
      return `Resize failed: ${error instanceof Error ? error.message : String(error)}`
    }
  },
})
