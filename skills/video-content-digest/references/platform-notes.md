# 平台说明

## 浏览器优先取证

- 对 URL 输入，先检查当前环境是否具备浏览器操作能力，例如 Codex Chrome、`agent-browser` 或 `agent-reach`。
- 有可用能力时，优先通过用户的现有浏览器会话读取可见标题、描述、章节、字幕，以及理解内容所需的关键画面。
- 不读取 Cookie、会话存储或密码；不绕过登录、付费或访问限制；不点赞、评论、关注、投稿或执行其他写操作。
- 浏览器证据不足时，再尝试公开元数据/字幕；B站、抖音仍读不到主要内容时，先走下述 PeanutDL 下载回退，再用本地视频提取音频、转写和补充必要画面。

## YouTube

- 使用 `yt-dlp` 获取元数据和字幕。
- 优先使用人工上传字幕，再考虑自动生成字幕。
- 如果只有英文字幕，保留原意并将最终内容输出为中文，同时说明原始字幕为英文。

```powershell
yt-dlp --write-info-json --write-auto-subs --write-subs --sub-langs "zh.*,en.*" --skip-download -o ".video-summary-radar/outputs/%(title).200s/%(title).200s.%(ext)s" "<url>"
```

## Bilibili

- `yt-dlp` 通常可以获取元数据，字幕能力取决于视频。
- 页面内容和字幕不足以恢复主要内容时，使用 [PeanutDL B站下载](https://peanutdl.com/zh/bilibili)，按下述下载回退流程处理。
- 标题、简介、UP 主和章节可以辅助标注时间线，但主要观点必须来自字幕或转录。

## Douyin

- 分享链接可能经过短链接跳转，尽量先解析最终 URL。
- 优先使用已有登录态的浏览器读取视频页章节、可见字幕、文案与必要画面；不要探查或导出 Cookie。
- 浏览器与公开字幕均不足以恢复主要内容时，使用 [PeanutDL 抖音下载](https://peanutdl.com/zh/douyin)，按下述下载回退流程处理。该入口用于抖音，不作为 TikTok 的默认下载入口。
- 短视频仍应按问题、方法、证据和结论组织，不应以冗长时间线充数。

## PeanutDL 下载回退（B站 / 抖音）

仅在页面、播放内容或字幕无法可靠读出主要内容时使用；已取得足够内容则无需额外下载。用户要求获取视频内容时，下载公开可访问的视频属于该获取流程，不必为进入下载页再次询问。

1. 按来源平台打开上面的对应页面，检查当前可见界面。将用户提供的视频 URL（或已解析的最终 URL）填入链接输入框，点击“获取视频”（以当前页面为准）；不要把整段分享文案当成 URL，也不要根据标题换成其他视频。
2. 从解析结果中核对标题、封面、时长等可用信息，确认是目标视频；B站多分 P 时核对目标分 P。选择能满足转写和必要画面识别的下载结果，不默认下载全部清晰度或全部分 P。
3. 通过解析结果的下载按钮或视频另存为入口，配合当前浏览器工具的下载能力，将实际媒体保存到 `.video-summary-radar/outputs/<safe-video-title>/source/`；批量作业则保存到该作业的内容包目录下。下载链接临时有效，应及时保存媒体。确认得到可读取的媒体文件，而非解析页、广告页或仅一个下载链接。记录原视频 URL、PeanutDL 页面 URL、下载文件路径及实际失败信息（如有）。
4. 使用现有 `extract_audio.py`、`transcribe.py` 和 `normalize_transcript.py` 继续提取与整理内容；必要时查看本地关键画面。下载成功不等于转写完成，PeanutDL 只作为媒体获取渠道，不作为视频观点的证据来源。
5. 解析失败、无目标资源、页面不可用或工具不能保存媒体时，记录具体阶段和原因；无法继续时交付已确认内容，并请用户提供本地视频或导出字幕。遇到验证码或需要用户操作的登录时，请用户完成该步骤或提供本地文件；不循环重试同一失败操作。

## 本地视频

- 将用户提供的路径视为来源文件。
- 使用 `ffmpeg` 提取音频。
- 如果文件名包含有意义的标题，可作为默认标题。

## 转录

- 本地转录只使用 FunASR 中文后端。
- ASR 模型默认位于 `<workspace>/.video-summary-radar/runtime/models/SenseVoiceSmall`，缺失时报告准确路径。
- `<workspace>/.video-summary-radar/runtime/models/FSMN-VAD` 和 `PUNC` 为可选模型。
- FunASR 模型文件不会自动下载。
- Windows CPU 部署时，`torch` 与 `torchaudio` 使用匹配版本；安装器会使用 CPU 软件源。
- 最终内容包记录实际转录后端、模型来源和转录限制。

## 依赖设置

- Python 必须为 3.10 或更高版本。
- Python 依赖安装在工作区私有的 `.video-summary-radar/runtime/venv/`。
- 模型安装在工作区私有的 `.video-summary-radar/runtime/models/`。
- 使用 `where.exe ffmpeg`（Windows）或 `which ffmpeg`（macOS）检查 `ffmpeg`。
- 手动安装 `ffmpeg` 使用 `winget install Gyan.FFmpeg` 或 `brew install ffmpeg`。

## 隐私与访问

- 不绕过私有、付费、需要登录或受限制的内容。
- 区分公开视频页面的登录提示与内容本身的访问限制：前者可继续尝试公开字幕和 PeanutDL；私有、付费或本身需要额外权限的内容，请用户完成授权访问或提供本地文件、导出的字幕或转录稿。
