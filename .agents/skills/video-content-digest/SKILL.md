---
name: video-content-digest
description: Convert YouTube, Bilibili, Douyin/TikTok-style short video links, generic video URLs, or local video file paths into Chinese content packages. Use this skill whenever the user provides a video link or local video path and asks for video summaries, key points, timestamped timelines, quotes, transcripts, WeChat public account drafts, Xiaohongshu drafts, content repurposing, video notes, content breakdowns, or social media copy based on video content.
---

# Video Content Digest

## Purpose

Turn one video input into a structured Chinese content package:

- 视频摘要
- 核心观点
- 内容拆解
- 时间线
- 金句
- 公众号初稿
- 小红书初稿

Prefer factual extraction over creative invention. Polished writing is allowed, but claims must come from the video transcript, captions, title, description, or user-provided context.

## Workflow

1. Check dependencies with `scripts/check_env.py --mode chinese`.
   - The bootstrap prerequisite is Python 3.10 or newer. If Python is missing, explain that the user must install it from the official Python distribution before continuing.
   - The checker is read-only unless `--install` is explicitly provided after user confirmation.
   - All Python packages, models, cache files, configuration, and the manifest are stored under this skill's `lib/` directory. Never install into the system Python.
   - The only transcription backend is FunASR Chinese mode.
   - `ffmpeg` is checked but never installed or uninstalled by this skill. Show platform-specific package-manager commands instead.
   - This skill does not automatically download FunASR model files.
   - After installation, report the runtime Python, package directory, model directory, cache directory, and manual cleanup instructions.
2. If the user asks to uninstall or delete this skill:
   - Report the exact `lib/` runtime paths first.
   - Do not automatically delete the runtime, models, cache, configuration, or project files.
   - Offer manual deletion commands for `lib/venv`, `lib/cache`, `lib/config`, and `lib/manifest.json`.
   - Preserve `lib/models/` and project `outputs/` unless the user separately requests their deletion.
   - `ffmpeg` is managed separately by the system package manager and is never removed by this skill.
3. Identify the input with `scripts/resolve_video.py`.
4. Get metadata and transcript:
   - For YouTube, Bilibili, Douyin, and generic URLs, try `yt-dlp` first for metadata and subtitles.
   - For local files, use the local path directly.
   - If usable subtitles are unavailable, extract audio with `scripts/extract_audio.py` and transcribe with the local FunASR backend.
5. Normalize subtitles or transcripts with `scripts/normalize_transcript.py`.
6. Read `references/output-templates.md` before writing the final output.
7. Read `references/platform-notes.md` when handling platform-specific URL behavior.
8. Read `references/quality-checklist.md` before finalizing.

## Runtime and Commands

The managed runtime is always relative to the current skill directory:

```text
<skill-root>/lib/
├── venv/
├── models/
├── cache/
├── config/
└── manifest.json
```

The path is resolved by `scripts/runtime_paths.py`; installation scope does not change it.

Check dependencies without changing the environment:

```powershell
python scripts/check_env.py --mode chinese
```

After the user explicitly confirms the reported dependencies and install location:

```powershell
python scripts/check_env.py --mode chinese --install
```

The script creates `lib/venv/` automatically. It never installs Python itself, installs `ffmpeg`, or downloads FunASR models.

For CPU-only Windows FunASR setup, the installer uses matching PyTorch packages from the CPU index when needed:

```powershell
<skill-root>\lib\venv\Scripts\python.exe -m pip install funasr yt-dlp
<skill-root>\lib\venv\Scripts\python.exe -m pip install torch==2.11.0+cpu torchaudio==2.11.0+cpu --index-url https://download.pytorch.org/whl/cpu
```

These are troubleshooting commands only. Prefer `check_env.py --install` so the target environment is selected automatically.

The required ASR model path is:

```text
<skill-root>/lib/models/SenseVoiceSmall
```

Optional model paths are:

```text
<skill-root>/lib/models/FSMN-VAD
<skill-root>/lib/models/PUNC
```

Identify input:

```powershell
python scripts/resolve_video.py "<video-url-or-local-path>"
```

Extract audio from a local video:

```powershell
python scripts/extract_audio.py "<video-file>" --output outputs/audio.wav
```

Normalize subtitles:

```powershell
python scripts/normalize_transcript.py "<subtitle-or-transcript-file>" --output outputs/transcript.md --format md
python scripts/normalize_transcript.py "<subtitle-or-transcript-file>" --output outputs/transcript.json --format json
```

Transcribe extracted audio:

```powershell
<skill-root>\lib\venv\Scripts\python.exe scripts/transcribe.py outputs/audio.wav --backend chinese --output outputs/transcript.json --format json
```

Optional URL preparation with `yt-dlp`:

```powershell
yt-dlp --write-info-json --write-auto-subs --write-subs --sub-langs "zh.*,en.*" --skip-download -o "outputs/%(title).200s/%(title).200s.%(ext)s" "<video-url>"
```

## Transcript Rules

- Prefer human-created subtitles over auto-generated subtitles.
- Prefer Chinese subtitles. If only English subtitles exist, translate the final content into Chinese and mention that the source transcript was English.
- Preserve timestamps whenever possible.
- If transcript quality is poor, say so briefly in the final output and avoid overconfident claims.
- If the video cannot be downloaded or transcribed, use available page metadata and ask the user for a transcript or local file.

## Final Output Rules

Use Chinese by default and follow the exact section order from `references/output-templates.md` unless the user requests another format.

For long videos, keep the timeline compact but representative:

- Under 10 minutes: 5-10 timeline items.
- 10-60 minutes: 8-16 timeline items.
- Over 60 minutes: 12-24 timeline items grouped by topic.

The `内容拆解` section must cover:

1. 选题角度：主题切口、目标受众和与常见表达的差异。
2. 开头钩子：开场触发方式、原始表述或基于原文的轻度改写，并尽量附时间戳。
3. 内容结构：问题、论点、案例、结论和转折的组织方式。
4. 视频爆点：冲突、反常识、案例、数字或情绪峰值，并尽量附时间戳。
5. 互动引导：视频已有的行动号召，以及可复用的评论讨论问题。

For quotes:

- Include timestamps when available.
- Prefer memorable original wording.
- If lightly polished, do not change the meaning.

For the two platform drafts:

- `公众号初稿` should be structured, readable, and suitable for long-form publication while remaining a draft for later editing.
- `小红书初稿` should be conversational, hook-driven, scannable, and include tags while remaining a draft for later editing.
- Do not exaggerate results, numbers, or causal claims beyond the video.

## File Output

When the user wants files, save Markdown to:

```text
outputs/<safe-video-title>-content-package.md
```

Also save transcript files when generated:

```text
outputs/<safe-video-title>-transcript.md
outputs/<safe-video-title>-transcript.json
```

If the title is unknown, use a timestamped name such as:

```text
outputs/video-content-YYYYMMDD-HHMMSS.md
```

## 批量任务协作

当上游 `creator-intelligence` 提供 `digest-jobs.json` 时，仍按单视频流程处理每条作业：

1. 只处理作业中的 `url`，不根据标题搜索替代视频。
2. 将内容包写到作业的 `output_path`，通常为上游任务目录中的 `digests/<stable-key>/content-package.md`，而不是本 skill 默认的 `outputs/` 路径。
3. 保持本 skill 的固定 Markdown 章节、来源链接、字幕/转写来源、时间戳和质量限制说明。
4. 不能下载、取得字幕或完成转写时，返回具体失败阶段与原因给上游；不要生成无来源的内容包。

本 skill 不做跨视频规律分析、爆款评分或账号选题推荐；这些任务由 `creator-intelligence` 根据多个内容包和采集证据完成。
