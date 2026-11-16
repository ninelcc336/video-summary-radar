#!/usr/bin/env python3
"""从采集结果和账号画像创建可执行的批量蒸馏任务目录。"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from creator_intelligence.batch import load_manifest, select_digest_jobs, write_manifest  # noqa: E402
from creator_intelligence.models import DigestManifest  # noqa: E402
from creator_intelligence.pipeline import load_collection  # noqa: E402
from creator_intelligence.profile import load_profile, write_profile  # noqa: E402
from creator_intelligence.ranker import rank_videos  # noqa: E402
from creator_intelligence.time_window import parse_range  # noqa: E402


def main() -> int:
    """冻结输入并生成易读路径；重复准备时保留已有路径、状态及创建时间。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", required=True, help="采集产生的 collection JSON")
    parser.add_argument("--profile", required=True, help="账号画像 JSON")
    parser.add_argument("--range", choices=["1d", "7d", "30d"], default="7d")
    parser.add_argument("--mode", choices=["top", "all"], default="top")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    collection_path = Path(args.collection).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    videos, _ = load_collection(collection_path)
    profile = load_profile(Path(args.profile).resolve())
    ranked = rank_videos(videos, parse_range(args.range, now), now)
    jobs = select_digest_jobs(ranked, args.mode, args.limit, now)
    previous_path = output_dir / "digest-manifest.json"
    previous = load_manifest(previous_path) if previous_path.is_file() else None
    existing = {job.stable_video_key: job for job in previous.jobs} if previous else {}
    prepared_jobs = []
    for job in jobs:
        if job.stable_video_key in existing:
            prepared_jobs.append(replace(existing[job.stable_video_key], video=job.video))
            continue
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", job.video.video_id):
            raise ValueError("视频 ID 包含不支持的路径字符")
        title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", job.video.title).strip(" .")[:60].rstrip(" .") or "未命名视频"
        prepared_jobs.append(replace(job, package_path=f"digests/{title}__{job.video.platform}-{job.video.video_id}/视频总结.md"))
    manifest = DigestManifest(profile=profile, jobs=tuple(prepared_jobs), created_at=previous.created_at if previous else now)
    if collection_path != output_dir / "collection.json":
        shutil.copyfile(collection_path, output_dir / "collection.json")
    write_profile(profile, output_dir / "account-profile.json")
    write_manifest(manifest, output_dir / "digest-manifest.json")
    jobs_payload = {
        "jobs": [
            {
                "stable_video_key": job.stable_video_key,
                "url": job.video.url,
                "title": job.video.title,
                "platform": job.video.platform,
                "state": job.state,
                "output_path": job.package_path,
                "transcript_path": str(Path(job.package_path).with_name("口播稿.txt")).replace("\\", "/"),
                "materials_path": str(Path(job.package_path).parent / "处理资料").replace("\\", "/"),
            }
            for job in manifest.jobs
        ]
    }
    (output_dir / "digest-jobs.json").write_text(json.dumps(jobs_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
