from __future__ import annotations

import math
from datetime import datetime, timezone

from creator_intelligence.models import RankedVideo, VideoModel
from creator_intelligence.time_window import TimeWindow, is_inside_window


def rank_videos(videos: list[VideoModel], window: TimeWindow, now: datetime | None = None) -> list[RankedVideo]:
    reference_time = now or window.end_at
    ranked = [
        RankedVideo(
            video=video,
            hot_score=calculate_hot_score(video, reference_time),
            engagement_rate=calculate_engagement_rate(video),
        )
        for video in videos
        if is_inside_window(video.published_at, window)
    ]
    return sorted(ranked, key=lambda item: (item.video.platform, -item.hot_score, -item.video.views))


def calculate_engagement_rate(video: VideoModel) -> float:
    if video.views <= 0:
        return 0.0
    interactions = video.likes + video.comments + video.shares + video.favorites
    return interactions / video.views


def calculate_hot_score(video: VideoModel, now: datetime | None = None) -> float:
    reference_time = now or datetime.now(timezone.utc)
    age_hours = max((reference_time - video.published_at).total_seconds() / 3600, 1)
    velocity_score = math.log10(video.views / age_hours + 1) * 10 if video.metric_coverage.views else 0.0
    engagement_score = min(calculate_engagement_rate(video), 0.2) * 100
    return velocity_score + engagement_score
