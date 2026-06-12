/**
 * data_forge_caption — OpenCode 自定义工具：管理 AI 训练数据集标注文件。
 *
 * 包装 `python -m data_forge.caption` CLI，提供标注文件的增删改查、搜索替换、
 * 去重统计及 JSON/CSV 导入导出功能。
 *
 * 所有相对路径基于项目根目录 (process.cwd()) 解析。
 *
 * @example
 *   // 列出所有标注文件
 *   data_forge_caption({ subcommand: "list", directory: "captions/" })
 *
 *   // 搜索标注内容
 *   data_forge_caption({ subcommand: "search", directory: "captions/", query: "sunset" })
 *
 *   // 创建标注（指定文件名和内容）
 *   data_forge_caption({ subcommand: "create", directory: "captions/", file: "img01", content: "a sunset over the ocean" })
 *
 *   // 批量替换
 *   data_forge_caption({ subcommand: "replace", directory: "captions/", old: "sunset", new: "sunrise" })
 *
 *   // 导出为 JSON
 *   data_forge_caption({ subcommand: "export", directory: "captions/", output: "captions.json", format: "json" })
 *
 *   // 统计信息 + 词频
 *   data_forge_caption({ subcommand: "stats", directory: "captions/", word_frequency: "true", top_n: "10" })
 *
 * @param subcommand - 子命令: list | create | read | edit | delete | search | replace | rename | stats | export | import | deduplicate
 * @param params - 各子命令对应的 CLI 参数（snake_case 自动转为 --kebab-case）
 */
export const data_forge_caption = async ({
  subcommand,
  ...params
}: {
  subcommand: string;
  [key: string]: string | undefined;
}): Promise<{ output: string } | { error: string }> => {
  const args: string[] = [subcommand];

  // 布尔标志位：Python argparse store_true，不需要传值，只需出现即生效
  const booleanFlags = new Set([
    "overwrite",
    "case_sensitive",
    "regex",
    "by_filename",
    "all",
    "word_frequency",
  ]);

  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;

    let flag = key.replace(/_/g, "-");

    // edit 子命令使用 --dir，其他子命令使用 --directory
    if (subcommand === "edit" && flag === "directory") {
      flag = "dir";
    }

    if (booleanFlags.has(key)) {
      // 布尔标志：仅当值为 "true" 或 true 时添加
      const isTruthy = value === "true" || (value as unknown) === true;
      if (isTruthy) {
        args.push(`--${flag}`);
      }
    } else {
      args.push(`--${flag}`, value);
    }
  }

  const result =
    await $`uv run python -m data_forge.caption ${args}`.nothrow();

  if (result.exitCode !== 0) {
    const stderr = result.stderr.toString();
    return {
      error: stderr || `命令执行失败，退出码: ${result.exitCode}`,
    };
  }

  return { output: result.stdout.toString() };
};
