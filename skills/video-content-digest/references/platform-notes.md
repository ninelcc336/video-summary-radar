# 平台说明

## 匿名获取与浏览器隔离

- 对 URL 输入，先尝试匿名公开元数据和字幕；调用 `yt-dlp` 时加 `--ignore-config`，不传 Cookie、浏览器 Cookie 导入或账号凭据，避免外部配置隐式启用登录态。
- 需要页面交互、播放或关键画面时，优先考虑 Codex 内置浏览器，但必须先根据当前工具说明或启动参数确认它与个人浏览器分离、未载入账号状态。不能仅凭“内置”“专用”或页面上没有头像判断隔离成立。
- 内置浏览器不适用时，可用 `agent-browser` 等工具启动全新的独立上下文或空配置目录。使用任务专属会话；不连接已有个人 Chrome/CDP，不启用自动连接，不加载个人 profile、扩展、认证状态文件或会话恢复；检查实际生效的配置和环境变量是否会启用这些行为。仅设置会话名称或打开新的普通标签页不构成登录态隔离。
- Agent-Reach/OpenCLI 等后端也必须确认匿名运行、不会从用户浏览器自动复制登录态，才能用于本任务。无法确认时跳过该后端，改用匿名公开入口，并记录限制；不要通过读取个人 Cookie 或会话存储来验证隔离。
- 视频页、短链接跳转和媒体下载使用同一匿名边界。浏览器路线不可用或采集失败时，不自动切回个人 Chrome，不自动要求用户登录；其他匿名渠道仍失败时，请用户提供本地视频或导出字幕。
- 普通登录提示可继续尝试匿名渠道；遇到验证码、明确风控拦截或限流则停止对该平台的请求，记录原因，不换账号、后端或浏览器连续尝试。不绕过登录、付费或访问限制，不点赞、评论、关注或投稿。
- 字幕和页面证据不足时，B 站、抖音可用本地下载脚本，再提取音频、转写和补充必要画面。结果的“证据与处理说明”记录实际获取渠道、匿名方式及失败阶段。

## YouTube

- 使用 `yt-dlp` 获取元数据和字幕。
- 优先使用人工上传字幕，再考虑自动生成字幕。
- 如果只有英文字幕，保留原意并将最终内容输出为中文，同时说明原始字幕为英文。

```powershell
yt-dlp --ignore-config --write-info-json --write-auto-subs --write-subs --sub-langs "zh.*,en.*" --skip-download -o ".video-summary-radar/outputs/%(title).200s/%(title).200s.%(ext)s" "<url>"
```

## Bilibili

- `yt-dlp` 通常可以获取元数据，字幕能力取决于视频。
- 本地下载支持 BV、av、`b23.tv` 分享短链和 `?p=2` 等分 P 参数，默认第 1 P。优先选用 720p 及以下的可用 DASH 视频和音频轨道，以 FFmpeg 合成 MP4。播放接口返回单段媒体时也可下载。
- 标题、简介、UP 主和章节可以辅助标注时间线，但主要观点必须来自字幕或转录。

## Douyin

- 分享链接可能经过短链接跳转，尽量先解析最终 URL。
- 仅通过匿名公开入口或已确认隔离且未登录的浏览器读取视频页章节、可见字幕、文案与必要画面；不使用已有登录态或会自动复制个人登录态的后端。
- 本地下载支持视频长链和 `v.douyin.com` 分享短链，使用官方嵌入播放器的公开接口和返回的播放地址，保留平台提供的画面。仅处理视频作品。
- 短视频仍应按问题、方法、证据和结论组织，不应以冗长时间线充数。

## 本地下载（B 站 / 抖音）

用户要求下载时直接运行。蒸馏任务在字幕和页面证据不足时使用。

```powershell
python <skill-path>/scripts/download_video.py "<video-url>"
```

1. 在实际工作区运行，传入原视频 URL。脚本使用 Python 标准库发起匿名 HTTP 请求，通过系统上的 FFmpeg 封装 MP4。
2. 成功时核对返回的 `video_id`、`part` 和 `title`。`path` 指向默认视频产物目录中的 `处理资料/直连-平台-视频ID.mp4`，B 站多分 P 附带分 P 后缀。批量作业传 `--materials "<materials_path>"`。记录原链接、实际获取渠道与本地媒体路径。
3. 蒸馏任务将 `path` 传给 `extract_audio.py`，再用 `transcribe.py` 和 `normalize_transcript.py` 转写与整理。按需读取本地关键画面。
4. 失败时记录标准错误中的 `stage` 和 `reason`。`blocked` 或 `restricted` 表示平台限制，停止该平台请求。仍缺正文时，交付已确认的内容，并请用户提供本地视频或导出字幕。

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
- 公共视频页面的普通登录提示仍可尝试匿名公开字幕或本地下载。私有、付费或需要额外权限的内容，请用户提供有权使用的本地文件、导出的字幕或转录稿。
