#!/usr/bin/env python3
"""通过合法公开入口采集视频搜索结果，并输出统一 collection JSON。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from creator_intelligence.sources import DiscoveryRequest, collect_public  # noqa: E402
from creator_intelligence.time_window import parse_range  # noqa: E402


def _video_payload(video):
    return {
        "platform": video.platform,
        "creator_id": video.creator_id,
        "creator_name": video.creator_name,
        "domain": video.domain,
        "video_id": video.video_id,
        "title": video.title,
        "url": video.url,
        "published_at": video.published_at.isoformat(),
        "duration_seconds": video.duration_seconds,
        "views": video.views,
        "likes": video.likes,
        "comments": video.comments,
        "shares": video.shares,
        "favorites": video.favorites,
        "source_adapter": video.source_adapter,
        "collected_at": video.collected_at.isoformat() if video.collected_at else None,
        "metric_coverage": video.metric_coverage.__dict__,
        "data_caveats": list(video.data_caveats),
        "raw": video.raw,
    }


def _status_payload(status):
    return {
        "platform": status.platform,
        "adapter": status.adapter,
        "state": status.state,
        "reason": status.reason,
        "collected_at": status.collected_at.isoformat() if status.collected_at else None,
        "result_count": status.result_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--range", choices=["1d", "7d", "30d"], default="7d")
    parser.add_argument("--platform", default="youtube,bilibili")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    request = DiscoveryRequest(args.topic, tuple(item.strip() for item in args.platform.split(",") if item.strip()), parse_range(args.range, now), args.limit)
    result = collect_public(request, now)
    payload = {
        "request": {"topic": args.topic, "range": args.range, "platforms": list(request.platforms), "limit": args.limit},
        "requested_at": now.isoformat(),
        "videos": [_video_payload(video) for video in result.videos],
        "statuses": [_status_payload(status) for status in result.statuses],
    }
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
