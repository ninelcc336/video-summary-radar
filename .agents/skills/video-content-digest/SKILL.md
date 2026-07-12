---
name: video-content-digest
description: Convert YouTube, Bilibili, Douyin/TikTok-style short video links, generic video URLs, or local video file paths into Chinese content packages. Use this skill whenever the user provides a video link or local video path and asks for video summaries, key points, timestamped timelines, quotes, transcripts, WeChat public account articles, Xiaohongshu posts, content repurposing, video notes, or social media copy based on video content.
---

# Video Content Digest

## Purpose

Turn one video input into a structured Chinese content package:

- 视频摘要
- 核心观点
- 时间轴
- 金句
- 公众号文章
- 小红书文案

Prefer factual extraction over creative invention. The generated writing can be polished, but claims must come from the video transcript, captions, title, description, or user-provided context.

## Workflow

1. Check dependencies with `scripts/check_env.py`.
   - Use `light` for the smallest local setup with faster-whisper.
   - Use `chinese` (the default transcription backend) for Mandarin-first content with FunASR.
   - Use `--install` only when the user explicitly agrees to install missing Python dependencies.
   - This skill does not automatically download FunASR model files; provide local model directories explicitly.
   - After installation, report where packages were installed and how to uninstall them.
2. Identify the input with `scripts/resolve_video.py`.
3. Get metadata and transcript:
   - For YouTube, Bilibili, Douyin, and generic URLs, try `yt-dlp` first for metadata and subtitles.
   - For local files, use the local path directly.
   - If usable subtitles are unavailable, extract audio with `scripts/extract_audio.py` and transcribe with the available ASR tool in the current environment.
4. Normalize subtitles or transcripts with `scripts/normalize_transcript.py`.
5. Read `references/output-templates.md` before writing the final output.
6. Read `references/platform-notes.md` when handling platform-specific URL behavior.
7. Read `references/quality-checklist.md` before finalizing.

## Recommended Commands

For an isolated project-local environment on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Run the commands below with the `.venv` Python so packages stay under the project directory.

Check dependencies without changing the environment:

```bash
python scripts/check_env.py --mode light
python scripts/check_env.py --mode chinese
```

Install missing Python dependencies only after user approval:

```bash
python scripts/check_env.py --mode light --install
python scripts/check_env.py --mode chinese --install
```

For CPU-only Windows FunASR setup, install the matching PyTorch packages from the CPU index when needed:

```powershell
python -m pip install funasr yt-dlp
python -m pip install torch==2.11.0+cpu torchaudio==2.11.0+cpu --index-url https://download.pytorch.org/whl/cpu
```

Dependency modes:

- `light`: installs/checks `yt-dlp` and `faster-whisper`. Use for low-storage local transcription.
- `chinese`: installs/checks `yt-dlp`, `funasr`, `torch`, and `torchaudio`. Use for Mandarin-first local transcription.
- `all`: installs/checks both local transcription backends.
- `api` and `local` remain accepted as compatibility aliases for older commands.

The dependency checker reports:

- Python executable and pip command.
- Python `site-packages` install location.
- console-script install location.
- missing system tools such as `ffmpeg`.
- uninstall commands for the selected Python packages.

Identify input:

```bash
python scripts/resolve_video.py "<video-url-or-local-path>"
```

Extract audio from a local video:

```bash
python scripts/extract_audio.py "<video-file>" --output outputs/audio.wav
```

Normalize subtitles:

```bash
python scripts/normalize_transcript.py "<subtitle-or-transcript-file>" --output outputs/transcript.md --format md
python scripts/normalize_transcript.py "<subtitle-or-transcript-file>" --output outputs/transcript.json --format json
```

Transcribe extracted audio locally when `faster-whisper` is installed:

```bash
python scripts/transcribe.py outputs/audio.wav --backend light --model base --output outputs/transcript.json --format json
python scripts/transcribe.py outputs/audio.wav --backend chinese --asr-model path/to/asr --vad-model path/to/fsmn-vad --punc-model path/to/punc --output outputs/transcript.json --format json
python scripts/transcribe.py outputs/audio.wav --backend chinese --asr-model path/to/asr --output outputs/transcript.md --format md

Example with the project-local models:

```powershell
.\.venv\Scripts\python.exe scripts/transcribe.py inputs/audio.wav --backend chinese --asr-model models/SenseVoiceSmall --vad-model models/FSMN-VAD --output outputs/transcript.json --format json
```
```

Optional URL preparation with `yt-dlp`:

```bash
yt-dlp --write-info-json --write-auto-subs --write-subs --sub-langs "zh.*,en.*" --skip-download -o "outputs/%(title).200s/%(title).200s.%(ext)s" "<video-url>"
```

## Transcript Rules

- Prefer human-created subtitles over auto-generated subtitles.
- Prefer Chinese subtitles. If only English subtitles exist, translate the final content into Chinese and mention that the source transcript was English.
- Preserve timestamps whenever possible.
- If transcript quality is poor, say so briefly in the final output and avoid overconfident claims.
- If the video cannot be downloaded or transcribed, use any available page metadata and ask the user for a transcript or local file.

## Final Output Rules

Use Chinese by default.

Use the exact section order from `references/output-templates.md` unless the user asks for a different format.

For long videos, keep the timeline compact but representative:

- Under 10 minutes: 5-10 timeline items.
- 10-60 minutes: 8-16 timeline items.
- Over 60 minutes: 12-24 timeline items grouped by topic.

For quotes:

- Include timestamp when available.
- Prefer memorable original wording.
- If lightly polished, do not change the meaning.

For WeChat and Xiaohongshu:

- WeChat article should be structured, readable, and suitable for long-form publication.
- Xiaohongshu copy should be more conversational, with a strong hook and tags.
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
