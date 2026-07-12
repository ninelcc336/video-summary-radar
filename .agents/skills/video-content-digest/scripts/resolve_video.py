#!/usr/bin/env python3
"""Identify a video input as a known platform URL, generic URL, or local file."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlparse


VIDEO_EXTENSIONS = {
    ".3gp",
    ".avi",
    ".flv",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp4",
    ".mpeg",
    ".mpg",
    ".webm",
    ".wmv",
}


def classify_url(host: str) -> str:
    host = host.lower().lstrip("www.")
    if host in {"youtu.be", "youtube.com", "m.youtube.com", "music.youtube.com"} or host.endswith(".youtube.com"):
        return "youtube"
    if host in {"b23.tv", "bilibili.com", "m.bilibili.com"} or host.endswith(".bilibili.com"):
        return "bilibili"
    if host in {"douyin.com", "iesdouyin.com", "v.douyin.com"} or host.endswith(".douyin.com"):
        return "douyin"
    if host in {"tiktok.com", "vm.tiktok.com"} or host.endswith(".tiktok.com"):
        return "tiktok"
    return "generic-url"


def resolve_video(value: str) -> dict:
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return {
            "kind": "url",
            "platform": classify_url(parsed.netloc),
            "input": value,
            "host": parsed.netloc,
            "exists": None,
        }

    path = Path(value).expanduser()
    absolute_path = path.resolve()
    exists = absolute_path.exists()
    suffix = absolute_path.suffix.lower()
    return {
        "kind": "local-file" if suffix in VIDEO_EXTENSIONS else "local-path",
        "platform": "local",
        "input": value,
        "path": str(absolute_path),
        "exists": exists,
        "extension": suffix,
        "is_video_extension": suffix in VIDEO_EXTENSIONS,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Video URL or local path")
    parser.add_argument("--pretty", action="store_true", help="Print formatted JSON")
    args = parser.parse_args()

    result = resolve_video(os.path.expandvars(args.input))
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
