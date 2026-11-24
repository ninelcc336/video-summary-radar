---
name: video-content-digest
description: 获取 YouTube、B站、抖音、TikTok、通用视频链接或本地视频中的内容，提取字幕、口播与必要画面，交付中文摘要、内容还原和可追溯转录稿。用户要求读取、总结或转写视频时使用；基于视频创作文案时仅承担前置内容获取，不负责微信公众号、小红书等二次创作。
---

# Video Content Digest

## Purpose

只负责获取并忠实整理单个视频的内容，包括字幕、口播、必要画面和来源信息。交付结果让读者不看原视频也能理解其内容；不承担文案改写、传播策略或发布。默认落盘两份面向读者的产物：`口播稿.txt` 忠实保留原始表达；`视频总结.md` 先整体概括，再解释最值得保留的内容，并展开必要论据。中间资料统一放进 `处理资料/`。除非用户明确只要某一种格式，否则无需额外询问是否保存文件。

获取完成后，可提供“仅保留视频内容（默认） / 微信公众号文案 / 小红书文案 / 其他形式”的后续选项。用户未选择时，交付内容包即完成任务；用户已明确指定创作形式时，直接把内容包作为后续独立创作任务的输入，不重复询问。本 skill 的交付物始终只包含视频内容与证据。

Prefer factual extraction over creative invention. Keep source evidence separate from editorial analysis; every claim must come from the video transcript, captions, visible page content, key frames, title, description, or user-provided context.

## Workflow

1. Identify the input with `scripts/resolve_video.py` and read `references/platform-notes.md`.
2. For URL inputs, use anonymous retrieval by default, in this evidence order:
   - public metadata and subtitles through unauthenticated HTTP/tools or `yt-dlp --ignore-config`, without cookies, account credentials, or browser-session imports;
   - when page interaction, playback, or visual evidence is needed, use an isolated, unsigned-in browser. Prefer the Codex built-in browser when its session isolation is established; otherwise launch a fresh independent browser context/profile. Follow the browser selection rules in `references/platform-notes.md`;
   - when public subtitles and page evidence cannot recover the main content, run `scripts/download_video.py` for Bilibili or Douyin. Use it directly when the user asks to download a video. It retrieves media from the platform's public player and CDN;
   - use the downloaded or user-provided local video for audio extraction and FunASR transcription when the main content still needs recovery.
   Never connect to the user's everyday Chrome, reuse/import personal cookies or saved auth state, or use a backend that automatically copies their login. This applies to tools such as Agent-Reach/OpenCLI as well as direct browser access; a dedicated browser or read-only command alone does not establish anonymous access. If isolation cannot be established, skip that route and record why. Retrieval failures must not trigger a switch to a personal browser or an automatic login request. A generic login prompt on an otherwise public page allows other anonymous routes; if the content itself requires authorization, request a local file/subtitle export instead. Stop requests to a platform on a CAPTCHA, explicit risk-control block, or rate limit rather than switching browsers/backends to retry it. Do not bypass access controls or perform social actions.
3. Build an evidence inventory before writing: title/description, subtitles or ASR, chapter summaries, and necessary visual evidence such as slides, code, UI steps, charts, or before/after states. Resolve conflicts with this priority: clear visual original text or clear speech > human subtitles > automatic subtitles or ASR > page chapter summaries. Record unresolved conflicts instead of silently merging them.
4. Use local transcription only if the evidence inventory cannot recover the main content. Record the actual acquired time spans and gaps. Page metadata or AI chapters alone never establish full speech coverage; do not invent numerical coverage estimates.
   - For Bilibili and Douyin URLs, use the local downloader before asking for a local video. If it reports `blocked` or `restricted`, record the cause and stop platform requests. Feed downloaded media to audio transcription and extract any necessary frames.
   - Then check dependencies with `scripts/check_env.py --mode chinese`.
   - The bootstrap prerequisite is Python 3.10 or newer. If Python is missing, explain that the user must install it from the official Python distribution before continuing.
   - The checker is read-only unless `--install` is explicitly provided after user confirmation.
   - All Python packages, models, cache files, configuration, and the manifest are stored under `<workspace>/.video-summary-radar/runtime/`. Never write to the installed skill directory or the system Python.
   - The only transcription backend is FunASR Chinese mode. `ffmpeg` is checked but never installed or uninstalled by this skill, and FunASR models are never downloaded automatically.
   - If the user declines the required installation or files, deliver all reliable evidence and a `内容缺口与来源` section rather than inventing missing content.
5. If the user asks to uninstall or delete this skill:
   - Report the exact `<workspace>/.video-summary-radar/runtime/` paths first.
   - Do not automatically delete the runtime, models, cache, configuration, or project files.
   - Offer manual deletion commands for `<workspace>/.video-summary-radar/runtime/venv`, `cache`, `config`, and `manifest.json`.
   - Preserve `<workspace>/.video-summary-radar/runtime/models/` and workspace outputs unless the user separately requests their deletion.
   - `ffmpeg` is managed separately by the system package manager and is never removed by this skill.
6. Prepare the stable output directory with `scripts/prepare_output.py` after confirming the video identity. Normalize real subtitles or ASR with `scripts/normalize_transcript.py`; keep timed JSON in `处理资料/`, export `--format txt` for the speech draft, then correct only confirmed recognition/punctuation errors. This script does not extract speech from report Markdown: isolate and review its actual speech first. Never feed a summary or page chapters into transcript export.
7. Read `references/output-templates.md` before writing the final output. Add title/category/tags/summary metadata following `references/retrieval.md`, then run `scripts/index_outputs.py` to refresh the output index after delivery. Reuse existing tag names; never insert metadata into the pure speech TXT.
8. Read `references/quality-checklist.md` before finalizing. Deliver the available video content before offering optional follow-up creation; do not block retrieval or delivery on a platform-copy choice.

## Runtime and Commands

The managed runtime is always relative to the caller's workspace, not the installed skill directory:

```text
<workspace>/.video-summary-radar/runtime/
├── venv/
├── models/
├── cache/
├── config/
└── manifest.json
```

The path is resolved by `scripts/runtime_paths.py`. Set `VIDEO_SUMMARY_RADAR_RUNTIME_DIR` only when the user explicitly requests another private runtime location.

Check dependencies without changing the environment:

```powershell
python scripts/check_env.py --mode chinese
```

After the user explicitly confirms the reported dependencies and install location:

```powershell
python scripts/check_env.py --mode chinese --install
```

The script creates `<workspace>/.video-summary-radar/runtime/venv/` automatically. It never installs Python itself, installs `ffmpeg`, or downloads FunASR models.

For CPU-only Windows FunASR setup, the installer uses matching PyTorch packages from the CPU index when needed:

```powershell
<workspace>\.video-summary-radar\runtime\venv\Scripts\python.exe -m pip install funasr yt-dlp
<workspace>\.video-summary-radar\runtime\venv\Scripts\python.exe -m pip install torch==2.11.0+cpu torchaudio==2.11.0+cpu --index-url https://download.pytorch.org/whl/cpu
```

These are troubleshooting commands only. Prefer `check_env.py --install` so the target environment is selected automatically.

The required ASR model path is:

```text
<workspace>/.video-summary-radar/runtime/models/SenseVoiceSmall
```

Optional model paths are:

```text
<workspace>/.video-summary-radar/runtime/models/FSMN-VAD
<workspace>/.video-summary-radar/runtime/models/PUNC
```

Identify input:

```powershell
python scripts/resolve_video.py "<video-url-or-local-path>"
```

Download a public Bilibili or Douyin video from the caller's workspace:

```powershell
python <skill-path>/scripts/download_video.py "<video-url>"
```

The downloader uses Python's standard library and the installed `ffmpeg`. Its JSON result includes the local MP4 `path`, source URL, and access method. Pass the path to `extract_audio.py`. Use `--materials "<task-materials-directory>"` for a batch job's designated directory.

Extract audio from a local video:

```powershell
python scripts/extract_audio.py "<video-file>" --output <视频目录>/处理资料/audio.wav
```

Normalize subtitles:

```powershell
python scripts/normalize_transcript.py "<subtitle-or-transcript-file>" --output <视频目录>/处理资料/transcript.md --format md
python scripts/normalize_transcript.py "<subtitle-or-transcript-file>" --output <视频目录>/处理资料/transcript.json --format json
```

Transcribe extracted audio:

```powershell
<workspace>\.video-summary-radar\runtime\venv\Scripts\python.exe scripts/transcribe.py <视频目录>/处理资料/audio.wav --backend chinese --output <视频目录>/处理资料/transcript.json --format json
```

Optional URL preparation with `yt-dlp`:

```powershell
yt-dlp --ignore-config --write-info-json --write-auto-subs --write-subs --sub-langs "zh.*,en.*" --skip-download -o "<视频目录>/处理资料/%(id)s.%(ext)s" "<video-url>"
```

## Transcript Rules

- Prefer human-created subtitles over auto-generated subtitles.
- Prefer Chinese subtitles. Preserve the original speech language in `口播稿.txt`; write the report in Chinese and disclose any translation. Translations are separate optional artifacts, never presented as the original speech.
- Preserve timestamps in evidence JSON/Markdown whenever possible; omit them from the pure TXT.
- Keep the raw or normalized transcript as a local evidence file, but do not make it the default reading experience. The main package must be a semantic reconstruction.
- If transcript quality is poor, say so briefly in the final output and avoid overconfident claims.
- For slide, code, chart, UI, or comparison-heavy videos, capture and describe only the visual details required to understand the argument. Attach 3-8 key frames only when text description would lose essential information.
- If the main content remains unavailable after applicable subtitle, browser, direct download, and local transcription attempts, return the reliable evidence plus `内容缺口与来源`. State the failed stage and reason, and request only the missing local file, subtitles, visual evidence, or transcription setup. Do not present a title or description as recovered video content.

## Final Output Rules

Follow `references/output-templates.md` and its fixed five report sections. The report must explain the problem, overall conclusion, supporting examples/reasoning, the most valuable material and its limits without requiring video playback. 时间戳仅用于溯源。Value judgments are AI editorial selection: distinguish them from the author's claims. Do not invent facts, prescriptions, audience hooks or interaction prompts.

## File Output

默认在调用者工作区保存：

```text
.video-summary-radar/outputs/视频标题__平台-视频ID/
├── 口播稿.txt
├── 视频总结.md
└── 处理资料/
    ├── 视频信息.json
    └── 字幕、带时间戳转录、媒体、截图、日志等
```

确认 URL 的平台、视频 ID 及分 P 后执行（从实际工作区运行，脚本使用安装位置的绝对路径）：

```powershell
python <skill-path>/scripts/prepare_output.py --title "视频标题" --platform douyin --video-id 7700609860844473663 --url "<video-url>"
python <skill-path>/scripts/normalize_transcript.py "<视频目录>/处理资料/transcript.json" --output "<视频目录>/口播稿.txt" --format txt
```

- `prepare_output.py` 返回目录和交付路径。标题非法字符替换为下划线，截到 60 字；身份由平台+ID+可选 `--part` 确定，同一父目录下重复解析复用第一次的目录名，不因标题更新或日期变化另建目录。
- 本地视频用 `--local-file "<path>" --title "标题"`，脚本用文件内容 SHA-256 的前 20 位标识；路径改变但字节相同仍复用目录。已知在线来源时优先使用在线身份。未知 URL 身份时先解析，不用时间戳冒充视频身份。
- 已有交付默认保留；内容相同可重复导出。新版本先写到 `处理资料/口播稿候选.txt`、`处理资料/视频总结候选.md`；对比后仅在用户明确要求更新原稿时替换。TXT 脚本的 `--overwrite` 仅用于已授权替换，不自动启用。
- 首次解析必须真实取得口播才生成 TXT；无口播或正文未取得时不生成空白/伪造 TXT，在报告的处理状态和缺口中说明。部分转录可保存 TXT，但报告明确标注已取得的范围及缺段，不能称完整口播。
- 处理状态固定为 `已解析`、`部分解析` 或 `未取得正文`。完成度依据实际证据范围，不写未测量的百分比；画面必要但缺失也属于部分解析。
- 历史文件先列迁移清单，再按真实证据归整；保留原文和处理记录在 `处理资料/`，修复索引与相对链接。仅有标题或页面 AI 章节不能补造口播。

## 已有产物检索

查找已解析的视频时，先读调用工作区 `.video-summary-radar/outputs/产物索引.md`，按标签、标题、摘要、作者筛选，再读命中的总结；需要精确引用才读口播，必要时核对处理资料。只读查询可用 `scripts/index_outputs.py --query "关键词"`。明确指定忽略工作区中的路径，避免普通仓库搜索漏掉产物；索引维护和全文查找见 `references/retrieval.md`。

## 批量任务协作

上游 `creator-intelligence` 提供 `digest-jobs.json` 时，按相同单视频标准处理：

1. 只处理作业 URL，不根据标题搜索替代视频。
2. 新作业的 `output_path` 为 `digests/视频标题__平台-视频ID/视频总结.md`；在其旁保存 `口播稿.txt` 和 `处理资料/`。以作业给定路径为准；历史 `content-package.md` 路径仍可读取，不擅自重命名已有批次。
3. 对新目录可用 `prepare_output.py --output-root "<任务目录>/digests"` 建立身份记录。使用 `download_video.py` 时，传入 `--materials "<materials_path>"`，将媒体写入作业的 `处理资料/`。
4. 取得部分内容可以交付有明确状态的总结；将失败阶段、缺失范围及原因返回上游，不能冒充已成功完整解析。批量索引链接实际存在的交付。
5. 每份总结包含相同检索元数据，完成后以整个产物根目录重建索引，使批次内的视频也可被统一查到。自定义批次在默认 outputs 外时用其父目录作为 --output-root。批量只返回视频内容与证据，不逐条询问二次创作选项。
6. 所有采集继续遵守匿名边界，失败不得切换到个人 Chrome、共享登录态或自动导入账号的后端。

本 skill 不做跨视频规律分析、爆款评分或账号选题推荐；这些由 `creator-intelligence` 根据多个总结和采集证据完成。
