# Platform Notes

## YouTube

- Use `yt-dlp` for metadata and subtitles.
- Prefer manually uploaded subtitles over auto-generated subtitles.
- If only English subtitles exist, keep source meaning and produce Chinese output.

Useful command:

```bash
yt-dlp --write-info-json --write-auto-subs --write-subs --sub-langs "zh.*,en.*" --skip-download -o "outputs/%(title).200s/%(title).200s.%(ext)s" "<url>"
```

## Bilibili

- `yt-dlp` often retrieves metadata and may retrieve subtitles depending on the video.
- If subtitles are unavailable, download/extract audio only when permitted by the environment and user intent.
- Titles, descriptions, uploader names, and chapters can help label the final timeline, but the main claims must come from transcript content.

## Douyin

- Shared links may redirect through short URLs. Resolve the final URL before classification when possible.
- Public download behavior changes often; prefer `yt-dlp` first, then fall back to user-provided local file or transcript.
- Short videos need fewer timeline items and stronger platform copy hooks.

## Local Video

- Treat the provided path as source of truth.
- Use `ffmpeg` to extract audio.
- If the file name contains a meaningful title, use it as the default title.

## Transcription backend selection

- Use `light` with faster-whisper tiny/base when disk space and setup time matter most.
- Use `chinese` with local FunASR models for Mandarin-first content. The ASR model path is required; FSMN-VAD and punctuation models are optional.
- FunASR model files are not downloaded automatically. Prepare them separately and pass their local directories to `--asr-model`, `--vad-model`, and `--punc-model`.
- On Windows CPU deployments, keep `torch` and `torchaudio` on matching versions; the project setup uses `2.11.0+cpu`.
- The current lightweight Chinese setup uses `models/SenseVoiceSmall` with `models/FSMN-VAD`; it does not include a separate punctuation model.
- Record the selected backend and model source in the final content package.

## Privacy and Access

- Do not bypass private, paywalled, login-only, or restricted content.
- If a URL requires user login or permission, ask for a local file, exported subtitles, or transcript.
