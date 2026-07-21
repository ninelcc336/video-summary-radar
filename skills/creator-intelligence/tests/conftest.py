"""Creator Intelligence 内容策略测试的共享 fixture。"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from creator_intelligence.models import MetricCoverage, RankedVideo, VideoModel


@pytest.fixture
def now() -> datetime:
    """返回固定且带时区的测试参考时间。"""
    return datetime(2026, 7, 21, 12, tzinfo=timezone.utc)


@pytest.fixture
def sample_video(now: datetime) -> VideoModel:
    """构造一个完整指标覆盖的视频模型。"""
    return VideoModel(
        platform="youtube", creator_id="creator", creator_name="创作者", domain="AI 工具",
        video_id="abc", title="低成本验证 AI 工具", url="https://www.youtube.com/watch?v=abc",
        published_at=now - timedelta(days=1), duration_seconds=300, views=10000, likes=500,
        comments=50, source_adapter="fixture", collected_at=now,
        metric_coverage=MetricCoverage(views=True, likes=True, comments=True),
    )


@pytest.fixture
def sample_ranked_videos(sample_video: VideoModel, now: datetime) -> list[RankedVideo]:
    """构造包含重复视频的热度排序结果，验证去重稳定性。"""
    duplicate = RankedVideo(sample_video, hot_score=80.0, engagement_rate=0.055)
    bilibili = VideoModel(
        platform="bilibili", creator_id="bili", creator_name="B站创作者", domain="AI 工具",
        video_id="BV1", title="AI 工具实操", url="https://www.bilibili.com/video/BV1",
        published_at=now - timedelta(hours=12), duration_seconds=120, views=8000, likes=800,
        comments=40, source_adapter="fixture", collected_at=now,
        metric_coverage=MetricCoverage(views=True, likes=True, comments=True),
    )
    return [duplicate, RankedVideo(bilibili, hot_score=90.0, engagement_rate=0.105), duplicate]
