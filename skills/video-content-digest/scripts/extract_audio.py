#!/usr/bin/env python3
"""Extract mono WAV audio from a video file with ffmpeg."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def extract_audio(input_path: Path, output_path: Path, sample_rate: int) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is not available on PATH")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Local video file")
    parser.add_argument("--output", required=True, help="Output WAV path")
    parser.add_argument("--sample-rate", type=int, default=16000, help="Output sample rate")
    args = parser.parse_args()

    extract_audio(Path(args.input).expanduser().resolve(), Path(args.output).expanduser().resolve(), args.sample_rate)
    print(str(Path(args.output).expanduser().resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
