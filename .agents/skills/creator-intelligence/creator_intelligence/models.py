from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


SUPPORTED_PLATFORMS = {"bilibili", "youtube", "douyin", "xiaohongshu"}
SourceState = Literal["available", "unavailable", "failed"]


@dataclass(frozen=True)
class MetricCoverage:
    views: bool = True
    likes: bool = False
    comments: bool = False
    shares: bool = False
    favorites: bool = False


@dataclass(frozen=True)
class SourceStatus:
    platform: str
    adapter: str
    state: SourceState
    reason: str = ""
    collected_at: datetime | None = None
    result_count: int = 0

    def __post_init__(self) -> None:
        if self.platform not in SUPPORTED_PLATFORMS:
            raise ValueError(f"Unsupported platform: {self.platform}")


@dataclass(frozen=True)
class VideoModel:
    platform: str
    creator_id: str
    creator_name: str
    domain: str
    video_id: str
    title: str
    url: str
    published_at: datetime
    duration_seconds: int
    views: int
    likes: int = 0
    comments: int = 0
    shares: int = 0
    favorites: int = 0
    raw: dict[str, Any] = field(default_factory=dict)
    source_adapter: str = "unknown"
    collected_at: datetime | None = None
    metric_coverage: MetricCoverage = field(default_factory=MetricCoverage)
    data_caveats: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.platform not in SUPPORTED_PLATFORMS:
            raise ValueError(f"Unsupported platform: {self.platform}")
        required_text = {
            "creator_id": self.creator_id,
            "creator_name": self.creator_name,
            "domain": self.domain,
            "video_id": self.video_id,
            "title": self.title,
            "url": self.url,
            "source_adapter": self.source_adapter,
        }
        missing = [name for name, value in required_text.items() if not value]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        numeric_fields = {
            "duration_seconds": self.duration_seconds,
            "views": self.views,
            "likes": self.likes,
            "comments": self.comments,
            "shares": self.shares,
            "favorites": self.favorites,
        }
        invalid = [name for name, value in numeric_fields.items() if value < 0]
        if invalid:
            raise ValueError(f"Numeric fields cannot be negative: {', '.join(invalid)}")


@dataclass(frozen=True)
class RankedVideo:
    video: VideoModel
    hot_score: float
    engagement_rate: float
