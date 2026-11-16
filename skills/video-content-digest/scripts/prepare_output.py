#!/usr/bin/env python3
"""准备稳定的视频产物目录；不创建空稿件，也不覆盖已有交付。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def prepare_output(root: Path, title: str, platform: str, video_id: str, url: str = "", part: str = "") -> Path:
    """按平台、视频 ID 和分 P 复用首次命名的目录，并保存来源标识。"""
    for value in (platform, video_id, part or "main"):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", value):
            raise ValueError("平台、视频 ID 和分 P 只接受字母、数字、下划线和连字符（1–100 字符）")
    identity = f"{platform}:{video_id}" + (f":{part}" if part else "")
    suffix = f"__{platform}-{video_id}" + (f"-p{part}" if part else "")
    root.mkdir(parents=True, exist_ok=True)
    for candidate in root.iterdir():
        if not candidate.is_dir():
            continue
        marker = candidate / "处理资料" / "视频信息.json"
        if marker.is_file():
            if json.loads(marker.read_text(encoding="utf-8"))["identity"] == identity:
                return candidate
        elif candidate.name.endswith(suffix):
            target = candidate
            break
    else:
        safe_title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title).strip(" .")[:60].rstrip(" .") or "未命名视频"
        target = root / (safe_title + suffix)
    materials = target / "处理资料"
    materials.mkdir(parents=True, exist_ok=True)
    (materials / "视频信息.json").write_text(json.dumps({
        "schema_version": 1, "identity": identity, "title": title,
        "platform": platform, "video_id": video_id, "part": part, "url": url,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def main() -> int:
    """接收已确认的视频身份，返回两份交付与处理资料的绝对路径。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True)
    parser.add_argument("--platform")
    parser.add_argument("--video-id")
    parser.add_argument("--url", default="")
    parser.add_argument("--part", default="")
    parser.add_argument("--local-file", type=Path)
    parser.add_argument("--output-root", type=Path, default=Path(".video-summary-radar/outputs"))
    args = parser.parse_args()
    if args.local_file:
        if args.platform or args.video_id:
            parser.error("--local-file 与 --platform/--video-id 不能同时使用")
        digest = hashlib.sha256()
        with args.local_file.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        video_id = digest.hexdigest()[:20]
        platform = "local"
    else:
        if not args.platform or not args.video_id:
            parser.error("网络视频需要 --platform 和 --video-id；未知身份时使用 --local-file")
        platform, video_id = args.platform, args.video_id
    target = prepare_output(args.output_root.resolve(), args.title, platform, video_id, args.url, args.part)
    print(json.dumps({"directory": str(target), "transcript": str(target / "口播稿.txt"),
                      "summary": str(target / "视频总结.md"), "materials": str(target / "处理资料")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
