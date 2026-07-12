#!/usr/bin/env python3
"""Transcribe audio with the light or Chinese-first backend."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from transcription_backends import transcribe_audio


def to_markdown(segments: list[dict]) -> str:
    lines = ["# Transcript", ""]
    for segment in segments:
        start = segment.get("start", "")
        end = segment.get("end", "")
        lines.append(f"- [{start} - {end}] {segment['text']}")
    lines.append("")
    return "\n".join(lines)


def transcribe(audio_path: Path, model_name: str, language: str | None) -> list[dict]:
    """Backward-compatible faster-whisper entry point."""
    return transcribe_audio(audio_path, "light", model_name, language, None, None, None)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", help="Audio file path")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--format", choices=["json", "md"], default="json")
    parser.add_argument("--backend", choices=["light", "chinese"], default="chinese")
    parser.add_argument("--model", default="small", help="faster-whisper model name for light backend")
    parser.add_argument("--language", default=None, help="Optional language code, e.g. zh or en")
    parser.add_argument("--asr-model", default=None, help="Local FunASR ASR model directory")
    parser.add_argument("--vad-model", default=None, help="Optional local FunASR FSMN-VAD model directory")
    parser.add_argument("--punc-model", default=None, help="Optional local FunASR punctuation model directory")
    args = parser.parse_args()

    audio_path = Path(args.audio).expanduser().resolve()
    segments = transcribe_audio(
        audio_path,
        args.backend,
        args.model,
        args.language,
        args.asr_model,
        args.vad_model,
        args.punc_model,
    )
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "json":
        output.write_text(json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        output.write_text(to_markdown(segments), encoding="utf-8")

    print(str(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
