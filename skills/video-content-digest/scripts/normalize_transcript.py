#!/usr/bin/env python3
"""Normalize SRT, VTT, plain text, or ASR JSON into TXT, Markdown, or JSON."""

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
    """Parse supported subtitle text or the JSON emitted by the local ASR runner."""
    content = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".json":
        raw_segments = json.loads(content)
        if not isinstance(raw_segments, list) or any(
            not isinstance(item, dict) or not isinstance(item.get("text"), str) for item in raw_segments
        ):
            raise ValueError("转录 JSON 必须为包含 text 字符串的分段列表，不能使用页面信息或摘要")
        return [
            {"start": str(item.get("start") or ""), "end": str(item.get("end") or ""),
             "text": clean_text([item["text"]])}
            for item in raw_segments if item["text"].strip()
        ]
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
    """导出逐段转录；默认拒绝覆盖不同内容，空转录不生成稿件。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="SRT, VTT, or plain text transcript")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--format", choices=["json", "md", "txt"], default="md")
    parser.add_argument("--overwrite", action="store_true", help="明确允许替换已有文件")
    args = parser.parse_args()

    segments = parse_transcript(Path(args.input).expanduser().resolve())
    if not segments:
        parser.error("没有可导出的转录文本")
    output = Path(args.output).expanduser().resolve()

    if args.format == "json":
        rendered = json.dumps(segments, ensure_ascii=False, indent=2)
    elif args.format == "txt":
        rendered = "\n\n".join(segment["text"] for segment in segments) + "\n"
    else:
        rendered = to_markdown(segments)
    if output.exists() and output.read_text(encoding="utf-8") != rendered and not args.overwrite:
        parser.error("已有文件内容不同；请写入处理资料中的候选稿，或确认替换后使用 --overwrite")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")

    print(str(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
