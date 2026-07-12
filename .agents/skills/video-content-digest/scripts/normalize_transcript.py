#!/usr/bin/env python3
"""Normalize SRT, VTT, or plain transcript files into Markdown or JSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


TIME_RE = re.compile(
    r"(?P<start>\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}|\d{1,2}:\d{2}[,.]\d{1,3})\s*-->\s*"
    r"(?P<end>\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}|\d{1,2}:\d{2}[,.]\d{1,3})"
)


def clean_time(value: str) -> str:
    value = value.replace(",", ".")
    parts = value.split(":")
    if len(parts) == 2:
        value = "00:" + value
    return value.split(".")[0]


def clean_text(lines: list[str]) -> str:
    text = " ".join(line.strip() for line in lines if line.strip())
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_timed_blocks(content: str) -> list[dict]:
    lines = content.replace("\ufeff", "").splitlines()
    segments: list[dict] = []
    i = 0
    while i < len(lines):
        match = TIME_RE.search(lines[i])
        if not match:
            i += 1
            continue

        start = clean_time(match.group("start"))
        end = clean_time(match.group("end"))
        i += 1
        text_lines: list[str] = []
        while i < len(lines):
            current = lines[i].strip()
            if not current:
                i += 1
                break
            next_is_timestamp = i + 1 < len(lines) and TIME_RE.search(lines[i + 1])
            if TIME_RE.search(lines[i]) or (current.isdigit() and next_is_timestamp):
                break
            text_lines.append(lines[i])
            i += 1

        text = clean_text(text_lines)
        if text:
            segments.append({"start": start, "end": end, "text": text})
    return segments


def parse_plain_text(content: str) -> list[dict]:
    paragraphs = [clean_text(block.splitlines()) for block in re.split(r"\n\s*\n", content)]
    return [{"start": "", "end": "", "text": paragraph} for paragraph in paragraphs if paragraph]


def parse_transcript(path: Path) -> list[dict]:
    content = path.read_text(encoding="utf-8", errors="replace")
    segments = parse_timed_blocks(content)
    if segments:
        return segments
    return parse_plain_text(content)


def to_markdown(segments: list[dict]) -> str:
    lines = ["# Transcript", ""]
    for segment in segments:
        if segment["start"]:
            lines.append(f"- [{segment['start']} - {segment['end']}] {segment['text']}")
        else:
            lines.append(f"- {segment['text']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="SRT, VTT, or plain text transcript")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--format", choices=["json", "md"], default="md")
    args = parser.parse_args()

    segments = parse_transcript(Path(args.input).expanduser().resolve())
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
