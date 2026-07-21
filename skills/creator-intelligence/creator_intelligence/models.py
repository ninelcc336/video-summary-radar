from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


SUPPORTED_PLATFORMS = {"bilibili", "youtube", "douyin", "xiaohongshu"}
SourceState = Literal["available", "unavailable", "failed"]
DigestState = Literal["pending", "succeeded", "failed", "skipped"]


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


@dataclass(frozen=True)
class AccountProfile:
    """保存单次内容策略任务可追溯的自媒体账号画像。"""

    platform: str
    domain: str
    audience: str
    source_text: str = ""
    profile_url: str = ""
    content_format: str = ""
    business_goal: str = ""
    exclusions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """校验账号画像的核心字段与至少一种信息来源。"""
        required = (self.platform.strip(), self.domain.strip(), self.audience.strip())
        if not all(required):
            raise ValueError("账号画像缺少平台、领域或受众")
        if not (self.source_text.strip() or self.profile_url.strip()):
            raise ValueError("账号画像必须提供对话描述或账号链接")


@dataclass(frozen=True)
class DigestJob:
    """描述一个可独立执行、可失败隔离的视频内容蒸馏作业。"""

    video: VideoModel
    stable_video_key: str
    state: DigestState
    package_path: str = ""
    failure_stage: str = ""
    failure_reason: str = ""
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """校验作业标识、状态与失败字段的组合。"""
        if not self.stable_video_key.strip():
            raise ValueError("stable_video_key is required")
        if self.state not in {"pending", "succeeded", "failed", "skipped"}:
            raise ValueError(f"Unsupported digest state: {self.state}")
        if self.state == "failed" and not self.failure_reason.strip():
            raise ValueError("failed digest job requires failure_reason")


@dataclass(frozen=True)
class DigestManifest:
    """记录一个批量蒸馏任务的账号画像、作业和创建时间。"""

    profile: AccountProfile
    jobs: tuple[DigestJob, ...]
    created_at: datetime

    def __post_init__(self) -> None:
        """确保 manifest 内的视频稳定标识不重复。"""
        keys = [job.stable_video_key for job in self.jobs]
        if len(keys) != len(set(keys)):
            raise ValueError("digest manifest contains duplicate stable_video_key")


@dataclass(frozen=True)
class ContentFeature:
    """保存从单条内容包中提取且能回溯证据的视频特征。"""

    stable_video_key: str
    topic_angle: str
    hook: str
    structure: str
    highlights: str
    interaction: str
    timeline: str
    evidence_urls: tuple[str, ...]
    completeness: float

    def __post_init__(self) -> None:
        """限制证据完整度范围并确保特征可追溯。"""
        if not self.stable_video_key.strip():
            raise ValueError("content feature requires stable_video_key")
        if not self.evidence_urls:
            raise ValueError("content feature requires at least one evidence URL")
        if not 0.0 <= self.completeness <= 1.0:
            raise ValueError("content feature completeness must be between 0 and 1")


@dataclass(frozen=True)
class TopicRecommendation:
    """描述一个带评分、证据和执行建议的可复刻选题。"""

    topic: str
    recent_heat_score: float
    replicability_score: float
    profile_match_score: float
    evidence_completeness_score: float
    total_score: float
    confidence: float
    evidence_urls: tuple[str, ...]
    title_directions: tuple[str, ...]
    outline: tuple[str, ...]
    risks: tuple[str, ...]

    def __post_init__(self) -> None:
        """校验评分范围和推荐必要的证据。"""
        scores = (
            self.recent_heat_score,
            self.replicability_score,
            self.profile_match_score,
            self.evidence_completeness_score,
            self.total_score,
            self.confidence,
        )
        if not self.topic.strip() or not self.evidence_urls:
            raise ValueError("topic recommendation requires topic and evidence URLs")
        if any(score < 0.0 or score > 100.0 for score in scores):
            raise ValueError("topic recommendation scores must be between 0 and 100")
