# Dependency Management

## Supported platforms

The supported delivery platforms are Windows and macOS. Linux remains a best-effort fallback for the Python runtime path and `ffmpeg` command suggestions.

The bootstrap Python must be version 3.10 or newer. This skill does not install Python automatically.

## Managed runtime locations

The skill never installs Python packages into the system interpreter or into the skill directory.

Project-level skill:

```text
<project-root>/.video-content-digest/
```

Global skill on Windows:

```text
%LOCALAPPDATA%\VideoSummaryRadar\video-content-digest\
```

Global skill on macOS:

```text
~/Library/Application Support/VideoSummaryRadar/video-content-digest/
```

Set `VIDEO_DIGEST_HOME` to use another location. The directory contains:

- `venv/`: the isolated Python environment;
- `models/`: user-provided FunASR models;
- `cache/`: temporary downloads and files;
- `config/`: skill-managed configuration;
- `manifest.json`: records the managed runtime.

The scope is detected from the nearest `.git` directory. Override detection with `VIDEO_DIGEST_SCOPE=project` or `VIDEO_DIGEST_SCOPE=global`.

## Installation behavior

`check_env.py` is read-only by default. The skill must first explain the missing dependencies, their purpose, the target paths, and the commands that will be run. Only after explicit user confirmation should it run:

```bash
python scripts/check_env.py --mode light --install
python scripts/check_env.py --mode chinese --install
```

The `--install` path creates the user runtime `venv` and installs only the selected Python dependency group there.

`ffmpeg` is a system dependency and is never installed automatically:

- Windows: `winget install Gyan.FFmpeg`;
- macOS: `brew install ffmpeg`.

If Homebrew is missing, tell the user to install Homebrew first. Do not invoke the Homebrew installer from the skill.

## Models

FunASR model files are never downloaded automatically. For the default Chinese setup, report these paths:

```text
<VIDEO_DIGEST_HOME>/models/SenseVoiceSmall
<VIDEO_DIGEST_HOME>/models/FSMN-VAD
```

The ASR model is required by the Chinese backend. VAD and punctuation models are optional when the backend supports operation without them.

## Removal guidance

When the user asks the Agent to uninstall or delete this skill:

- Report the detected scope and exact dependency/runtime paths first.
- Do not automatically delete the runtime, models, cache, config, or project files.
- Let the user manually delete only `venv/`, `cache/`, `config/`, and `manifest.json` when they confirm.
- Preserve project `outputs/` and user-provided models unless the user separately asks to remove them.
- Do not remove `ffmpeg`; show its package-manager command only if requested.

`check_env.py` prints manual commands for both platforms:

```text
Windows: Remove-Item -LiteralPath ... -Recurse -Force
macOS:   rm -rf -- ...
```

There is intentionally no deletion script in this skill.
