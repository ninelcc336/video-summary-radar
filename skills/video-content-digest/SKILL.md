---
name: video-content-digest
description: Convert YouTube, Bilibili, Douyin/TikTok-style short video links, generic video URLs, or local video file paths into Chinese content packages. Use this skill whenever the user provides a video link or local video path and asks for video summaries, key points, timestamped timelines, quotes, transcripts, WeChat public account drafts, Xiaohongshu drafts, content repurposing, video notes, content breakdowns, or social media copy based on video content.
---

# Video Content Digest

## Purpose

Turn one video input into a Chinese content package that lets a reader understand the video without watching it. The default package has two reading layers:

- 结论速览：约一分钟读完的问题、结论、方法、证据和限制。
- 完整内容还原：按主题和论证逻辑重组口播、字幕与必要画面信息，不机械复述镜头顺序。

The default output is for accurate understanding, not social-media repurposing. 公众号、小红书、标题或二次剪辑建议 are generated only when the user explicitly asks for them.

Prefer factual extraction over creative invention. Keep source evidence separate from editorial analysis; every claim must come from the video transcript, captions, visible page content, key frames, title, description, or user-provided context.

## Workflow

1. Identify the input with `scripts/resolve_video.py` and read `references/platform-notes.md`.
2. For URL inputs, inspect available browser-capable tools, plugins, and skills before considering local transcription. When present, prefer the following evidence order:
   - browser access using the user's existing session (for example Codex Chrome, `agent-browser`, or `agent-reach`), limited to visible public page content, captions, chapters, descriptions, key frames, and playable content;
   - public page metadata and subtitles via `yt-dlp`;
   - local audio extraction and FunASR transcription only when the first two sources do not sufficiently recover the main content.
   Do not inspect cookies or session stores, bypass login/access controls, or perform social actions. If a browser page requires login, ask the user to sign in or provide a local file/subtitle export. Do not download video merely to make the browser path work.
3. Build an evidence inventory before writing: title/description, subtitles or ASR, chapter summaries, and necessary visual evidence such as slides, code, UI steps, charts, or before/after states. Resolve conflicts with this priority: clear visual original text or clear speech > human subtitles > automatic subtitles or ASR > page chapter summaries. Record unresolved conflicts instead of silently merging them.
4. Use local transcription only if the evidence inventory cannot recover the main content. Treat less than roughly 60% usable coverage of the main content as insufficient.
   - Then check dependencies with `scripts/check_env.py --mode chinese`.
   - The bootstrap prerequisite is Python 3.10 or newer. If Python is missing, explain that the user must install it from the official Python distribution before continuing.
   - The checker is read-only unless `--install` is explicitly provided after user confirmation.
   - All Python packages, models, cache files, configuration, and the manifest are stored under `<workspace>/.video-summary-radar/runtime/`. Never write to the installed skill directory or the system Python.
   - The only transcription backend is FunASR Chinese mode. `ffmpeg` is checked but never installed or uninstalled by this skill, and FunASR models are never downloaded automatically.
   - If the user declines the required installation or files, deliver all reliable evidence and a `待确认信息` section rather than inventing missing content.
5. If the user asks to uninstall or delete this skill:
   - Report the exact `<workspace>/.video-summary-radar/runtime/` paths first.
   - Do not automatically delete the runtime, models, cache, configuration, or project files.
   - Offer manual deletion commands for `<workspace>/.video-summary-radar/runtime/venv`, `cache`, `config`, and `manifest.json`.
   - Preserve `<workspace>/.video-summary-radar/runtime/models/` and workspace outputs unless the user separately requests their deletion.
   - `ffmpeg` is managed separately by the system package manager and is never removed by this skill.
6. Normalize subtitles or transcripts with `scripts/normalize_transcript.py`. Save the normalized transcript as a local companion artifact even when it is not displayed in the main package.
7. Read `references/output-templates.md` before writing the final output.
8. Read `references/quality-checklist.md` before finalizing.

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

Extract audio from a local video:

```powershell
python scripts/extract_audio.py "<video-file>" --output .video-summary-radar/outputs/audio.wav
```

Normalize subtitles:

```powershell
python scripts/normalize_transcript.py "<subtitle-or-transcript-file>" --output .video-summary-radar/outputs/transcript.md --format md
python scripts/normalize_transcript.py "<subtitle-or-transcript-file>" --output .video-summary-radar/outputs/transcript.json --format json
```

Transcribe extracted audio:

```powershell
<workspace>\.video-summary-radar\runtime\venv\Scripts\python.exe scripts/transcribe.py .video-summary-radar/outputs/audio.wav --backend chinese --output .video-summary-radar/outputs/transcript.json --format json
```

Optional URL preparation with `yt-dlp`:

```powershell
yt-dlp --write-info-json --write-auto-subs --write-subs --sub-langs "zh.*,en.*" --skip-download -o ".video-summary-radar/outputs/%(title).200s/%(title).200s.%(ext)s" "<video-url>"
```

## Transcript Rules

- Prefer human-created subtitles over auto-generated subtitles.
- Prefer Chinese subtitles. If only English subtitles exist, translate the final content into Chinese and mention that the source transcript was English.
- Preserve timestamps whenever possible.
- Keep the raw or normalized transcript as a local evidence file, but do not make it the default reading experience. The main package must be a semantic reconstruction.
- If transcript quality is poor, say so briefly in the final output and avoid overconfident claims.
- For slide, code, chart, UI, or comparison-heavy videos, capture and describe only the visual details required to understand the argument. Attach 3-8 key frames only when text description would lose essential information.
- If the main content remains unavailable after browser and subtitle attempts, return the reliable evidence plus `待确认信息`; ask for a local file, exported subtitles, screenshots, or approval to prepare local transcription as appropriate.

## Final Output Rules

Use Chinese by default and follow the exact section order from `references/output-templates.md` unless the user requests another format. Organize the main reconstruction by problem, conclusion, method, evidence/case, and limitation; use timestamps only as evidence markers, never as an instruction to replay the video.

The package must let a reader answer, without watching the source: what problem the video addresses, its conclusion, how it argues or demonstrates the conclusion, what evidence it uses, and what remains uncertain.

For quotes, preserve original wording and attach an evidence time only when it materially helps provenance. If lightly polished, do not change the meaning.

Generate creative repurposing only when explicitly requested, under `创作复用（按需）`. Do not exaggerate results, numbers, or causal claims beyond the evidence.

## File Output

When the user wants files, save Markdown to:

```text
.video-summary-radar/outputs/<safe-video-title>-content-package.md
```

Also save transcript files when generated:

```text
.video-summary-radar/outputs/<safe-video-title>-transcript.md
.video-summary-radar/outputs/<safe-video-title>-transcript.json
```

The transcript is an evidence companion, not a substitute for the content package. When visual evidence is essential, save the selected key frames beside the package and link them from `关键画面与操作`.

If the title is unknown, use a timestamped name such as:

```text
.video-summary-radar/outputs/video-content-YYYYMMDD-HHMMSS.md
```

## 批量任务协作

当上游 `creator-intelligence` 提供 `digest-jobs.json` 时，仍按单视频流程处理每条作业：

1. 只处理作业中的 `url`，不根据标题搜索替代视频。
2. 将内容包写到作业的 `output_path`，通常为上游任务目录中的 `digests/<stable-key>/content-package.md`，而不是本 skill 默认的 `.video-summary-radar/outputs/` 路径。
3. 保持本 skill 的固定 Markdown 章节、来源链接、字幕/转写来源、时间戳和质量限制说明。
4. 不能下载、取得字幕或完成转写时，返回具体失败阶段与原因给上游；不要生成无来源的内容包。

本 skill 不做跨视频规律分析、爆款评分或账号选题推荐；这些任务由 `creator-intelligence` 根据多个内容包和采集证据完成。
