# 平台说明

## YouTube

- 使用 `yt-dlp` 获取元数据和字幕。
- 优先使用人工上传字幕，再考虑自动生成字幕。
- 如果只有英文字幕，保留原意并将最终内容输出为中文，同时说明原始字幕为英文。

```powershell
yt-dlp --write-info-json --write-auto-subs --write-subs --sub-langs "zh.*,en.*" --skip-download -o "outputs/%(title).200s/%(title).200s.%(ext)s" "<url>"
```

## Bilibili

- `yt-dlp` 通常可以获取元数据，字幕能力取决于视频。
- 没有字幕时，只有在环境和用户意图允许的情况下才下载并提取音频。
- 标题、简介、UP 主和章节可以辅助标注时间线，但主要观点必须来自字幕或转录。

## Douyin

- 分享链接可能经过短链接跳转，尽量先解析最终 URL。
- 公开下载行为可能变化，优先尝试 `yt-dlp`，失败时请求用户提供本地文件或转录稿。
- 短视频时间线应更精简，开头钩子和互动引导应更具体。

## 本地视频

- 将用户提供的路径视为来源文件。
- 使用 `ffmpeg` 提取音频。
- 如果文件名包含有意义的标题，可作为默认标题。

## 转录

- 本地转录只使用 FunASR 中文后端。
- ASR 模型默认位于 `lib/models/SenseVoiceSmall`，缺失时报告准确路径。
- `lib/models/FSMN-VAD` 和 `lib/models/PUNC` 为可选模型。
- FunASR 模型文件不会自动下载。
- Windows CPU 部署时，`torch` 与 `torchaudio` 使用匹配版本；安装器会使用 CPU 软件源。
- 最终内容包记录实际转录后端、模型来源和转录限制。

## 依赖设置

- Python 必须为 3.10 或更高版本。
- Python 依赖安装在当前 skill 目录的 `lib/venv/`。
- 模型安装在当前 skill 目录的 `lib/models/`。
- 使用 `where.exe ffmpeg`（Windows）或 `which ffmpeg`（macOS）检查 `ffmpeg`。
- 手动安装 `ffmpeg` 使用 `winget install Gyan.FFmpeg` 或 `brew install ffmpeg`。

## 隐私与访问

- 不绕过私有、付费、需要登录或受限制的内容。
- 如果 URL 需要登录或额外权限，请用户提供本地文件、导出的字幕或转录稿。
