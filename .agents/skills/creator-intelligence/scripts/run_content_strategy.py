#!/usr/bin/env python3
"""汇总批量内容包并生成可复刻爆款选题报告。"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from creator_intelligence.batch import load_manifest, mark_job_failed, mark_job_succeeded, write_manifest  # noqa: E402
from creator_intelligence.digest_parser import parse_content_package  # noqa: E402
from creator_intelligence.pipeline import load_collection  # noqa: E402
from creator_intelligence.ranker import rank_videos  # noqa: E402
from creator_intelligence.strategy import analyze_strategy  # noqa: E402
from creator_intelligence.strategy_renderer import render_strategy_report  # noqa: E402
from creator_intelligence.time_window import parse_range  # noqa: E402


def main() -> int:
    """解析任务目录、更新作业状态并写出分析 JSON 与 Markdown 报告。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="prepare_digest_batch.py 生成的任务目录")
    parser.add_argument("--range", choices=["1d", "7d", "30d"], default="7d")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    now = datetime.now(timezone.utc)
    manifest_path = run_dir / "digest-manifest.json"
    manifest = load_manifest(manifest_path)
    features = []
    for job in manifest.jobs:
        package_path = run_dir / job.package_path
        if job.state in {"failed", "skipped"}:
            continue
        if not package_path.is_file():
            manifest = mark_job_failed(manifest, job.stable_video_key, "content-package", "未找到内容包", now)
            continue
        try:
            feature = parse_content_package(job, package_path)
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            manifest = mark_job_failed(manifest, job.stable_video_key, "content-package", f"内容包解析失败：{exc}", now)
            continue
        features.append(feature)
        manifest = mark_job_succeeded(manifest, job.stable_video_key, job.package_path, now)

    videos, _ = load_collection(run_dir / "collection.json")
    ranked = rank_videos(videos, parse_range(args.range, now), now)
    result = analyze_strategy(manifest.profile, ranked, features)
    write_manifest(manifest, manifest_path)
    analysis_payload = {
        "profile": {
            "platform": manifest.profile.platform,
            "domain": manifest.profile.domain,
            "audience": manifest.profile.audience,
        },
        "sufficient_sample": result.sufficient_sample,
        "observations": list(result.observations),
        "warnings": list(result.warnings),
        "recommendations": [asdict(item) for item in result.recommendations],
    }
    (run_dir / "analysis.json").write_text(json.dumps(analysis_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "report.md").write_text(render_strategy_report(manifest, result), encoding="utf-8")
    print(run_dir / "report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
