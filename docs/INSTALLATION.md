# 安装与运行

## 安装 skill

使用 skills.sh 安装器并选择需要的 skill：

```bash
npx skills add <github-owner>/video-summary-radar
```

也可以将 `skills/<skill-name>/` 整个目录复制到目标 Agent 的技能目录。安装时只复制源码；不要携带 `.video-summary-radar/` 运行目录。

## 首次运行

在你的项目工作区调用 skill。它会先检查 Python、`ffmpeg`、`yt-dlp`、Agent-Reach 与模型等前置条件，并报告缺失项。只有在你明确同意后，才会运行安装命令。

`video-content-digest` 的默认运行时路径为：

```text
<workspace>/.video-summary-radar/runtime/
```

结果默认写入：

```text
<workspace>/.video-summary-radar/outputs/
```

可通过 `VIDEO_SUMMARY_RADAR_RUNTIME_DIR` 显式覆盖运行时目录；仅在用户确认其私有且可写时使用该变量。

公开 URL 的脱敏示例见 [video-urls.example.txt](examples/video-urls.example.txt)。

## 系统支持

Windows、macOS 与 Linux 均为正式支持目标。`ffmpeg` 由系统包管理器维护，skill 只提供检测与安装建议，不会自动安装或卸载它。
