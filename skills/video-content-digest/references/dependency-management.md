# 依赖管理

## 支持平台

支持 Windows 和 macOS。Linux 作为 Python 运行时和 `ffmpeg` 命令的尽力支持平台。

引导 Python 必须为 3.10 或更高版本。本 skill 不会自动安装 Python。

## 运行时位置

依赖和模型始终安装在调用项目的私有运行目录中：

```text
<workspace>/.video-summary-radar/runtime/
├── venv/          # 隔离的 Python 环境
├── models/        # 用户准备的 FunASR 模型
├── cache/         # 临时下载和处理文件
├── config/        # skill 管理的配置
└── manifest.json  # 运行时清单
```

路径由 `scripts/runtime_paths.py` 解析，不随项目级或全局安装改变。

## 安装行为

`check_env.py` 默认只读。skill 必须先说明缺少的依赖、用途、安装目标和将执行的命令；只有用户明确确认后，才可运行：

```powershell
python scripts/check_env.py --mode chinese --install
```

唯一依赖集合为：

- `yt-dlp`
- `funasr`
- `torch`
- `torchaudio`

安装命令会创建 `<workspace>/.video-summary-radar/runtime/venv/`，并且只向该虚拟环境安装 Python 包。

`ffmpeg` 是系统依赖，永远不自动安装：

- Windows：`winget install Gyan.FFmpeg`
- macOS：`brew install ffmpeg`

如果缺少 Homebrew，应提示用户先自行安装，不要从 skill 中执行 Homebrew 安装脚本。

## 模型

FunASR 模型文件永远不自动下载。中文转录默认使用：

```text
<workspace>/.video-summary-radar/runtime/models/SenseVoiceSmall
```

可选模型为：

```text
<workspace>/.video-summary-radar/runtime/models/FSMN-VAD
<workspace>/.video-summary-radar/runtime/models/PUNC
```

ASR 模型是必需项；VAD 和标点模型由后端按实际存在情况使用。

## 删除和卸载

当用户要求卸载或删除本 skill 管理的运行时：

- 先报告 `<workspace>/.video-summary-radar/runtime/` 下的准确路径。
- 不自动删除虚拟环境、模型、缓存、配置或项目文件。
- 用户确认后，只提供手动删除 `<workspace>/.video-summary-radar/runtime/venv/`、`cache/`、`config/` 和 `manifest.json` 的命令。
- 除非用户另行要求，否则保留 `<workspace>/.video-summary-radar/runtime/models/` 和工作区输出。
- 不删除 `ffmpeg`，只在用户询问时展示系统包管理器命令。

本 skill 没有自动删除脚本。
