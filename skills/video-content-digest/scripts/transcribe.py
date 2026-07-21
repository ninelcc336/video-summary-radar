#!/usr/bin/env python3
"""Transcribe audio with the FunASR Chinese backend only."""

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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", help="Audio file path")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--format", choices=["json", "md"], default="json")
    parser.add_argument("--backend", choices=["chinese"], default="chinese")
    parser.add_argument("--language", default="zh", help="Optional language code")
    parser.add_argument("--asr-model", default=None, help="FunASR ASR 模型目录")
    parser.add_argument("--vad-model", default=None, help="可选的 FunASR FSMN-VAD 模型目录")
    parser.add_argument("--punc-model", default=None, help="可选的 FunASR 标点模型目录")
    args = parser.parse_args()

    audio_path = Path(args.audio).expanduser().resolve()
    segments = transcribe_audio(
        audio_path,
        args.backend,
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
