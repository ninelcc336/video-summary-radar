from __future__ import annotations

import html
import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from creator_intelligence.models import MetricCoverage, SourceStatus, VideoModel
from creator_intelligence.time_window import TimeWindow, is_inside_window


@dataclass(frozen=True)
class DiscoveryRequest:
    topic: str
    platforms: tuple[str, ...]
    window: TimeWindow
    limit: int = 10

    def __post_init__(self) -> None:
        if not self.topic.strip():
            raise ValueError("topic is required")
        if self.limit < 1 or self.limit > 50:
            raise ValueError("limit must be between 1 and 50")


@dataclass(frozen=True)
class CollectionResult:
    videos: list[VideoModel]
    statuses: list[SourceStatus]


class PublicAdapter(Protocol):
    platform: str

    def collect(self, request: DiscoveryRequest, now: datetime) -> CollectionResult: ...


class YouTubePublicAdapter:
    platform = "youtube"
    adapter_name = "public-yt-dlp"

    def collect(self, request: DiscoveryRequest, now: datetime) -> CollectionResult:
        if shutil.which("yt-dlp") is None:
            return _unavailable(self.platform, self.adapter_name, "未检测到 yt-dlp", now)
        command = ["yt-dlp", "--dump-json", f"ytsearch{request.limit}:{request.topic}"]
        try:
            completed = subprocess.run(command, capture_output=True, check=False, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            return _failed(self.platform, self.adapter_name, "yt-dlp 搜索超时", now)
        except OSError as exc:
            return _failed(self.platform, self.adapter_name, str(exc), now)
        if completed.returncode != 0:
            return _failed(self.platform, self.adapter_name, completed.stderr.strip() or "yt-dlp 搜索失败", now)

        videos: list[VideoModel] = []
        for line in completed.stdout.splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            video = self._to_video(item, now)
            if video is not None and is_inside_window(video.published_at, request.window):
                videos.append(video)
        return CollectionResult(videos, [SourceStatus(self.platform, self.adapter_name, "available", collected_at=now, result_count=len(videos))])

    def _to_video(self, item: dict, now: datetime) -> VideoModel | None:
        video_id = str(item.get("id") or "")
        title = str(item.get("title") or "")
        if not video_id or not title:
            return None
        published_at = _published_at(item.get("timestamp"), item.get("upload_date"))
        if published_at is None:
            return None
        view_known = item.get("view_count") is not None
        likes_known = item.get("like_count") is not None
        comments_known = item.get("comment_count") is not None
        return VideoModel(
            platform=self.platform,
            creator_id=str(item.get("channel_id") or item.get("uploader_id") or "unknown"),
            creator_name=str(item.get("channel") or item.get("uploader") or "未知创作者"),
            domain="主题发现",
            video_id=video_id,
            title=title,
            url=str(item.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}"),
            published_at=published_at,
            duration_seconds=_as_int(item.get("duration")),
            views=_as_int(item.get("view_count")),
            likes=_as_int(item.get("like_count")),
            comments=_as_int(item.get("comment_count")),
            raw=item,
            source_adapter=self.adapter_name,
            collected_at=now,
            metric_coverage=MetricCoverage(views=view_known, likes=likes_known, comments=comments_known),
            data_caveats=() if view_known else ("平台未返回播放量",),
        )


class BilibiliPublicAdapter:
    platform = "bilibili"
    adapter_name = "public-bilibili-api"
    endpoint = "https://api.bilibili.com/x/web-interface/search/all/v2"

    def collect(self, request: DiscoveryRequest, now: datetime) -> CollectionResult:
        query = urlencode({"keyword": request.topic, "page": 1, "order": "click"})
        http_request = Request(f"{self.endpoint}?{query}", headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.bilibili.com/"})
        try:
            with urlopen(http_request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 - external public endpoint errors are report data.
            return _failed(self.platform, self.adapter_name, f"B站公开搜索不可用：{exc}", now)

        videos: list[VideoModel] = []
        for section in payload.get("data", {}).get("result", []):
            if section.get("result_type") != "video":
                continue
            for item in section.get("data", []):
                video = self._to_video(item, now)
                if video is not None and is_inside_window(video.published_at, request.window):
                    videos.append(video)
                    if len(videos) >= request.limit:
                        break
        return CollectionResult(videos, [SourceStatus(self.platform, self.adapter_name, "available", collected_at=now, result_count=len(videos))])

    def _to_video(self, item: dict, now: datetime) -> VideoModel | None:
        bvid = str(item.get("bvid") or item.get("id") or "")
        timestamp = item.get("pubdate")
        published_at = _published_at(timestamp, None)
        if not bvid or published_at is None:
            return None
        title = html.unescape(str(item.get("title") or ""))
        title = title.replace("<em class=\"keyword\">", "").replace("</em>", "")
        if not title:
            return None
        play_known = item.get("play") is not None
        return VideoModel(
            platform=self.platform,
            creator_id=str(item.get("mid") or "unknown"),
            creator_name=str(item.get("author") or "未知创作者"),
            domain="主题发现",
            video_id=bvid,
            title=title,
            url=str(item.get("arcurl") or f"https://www.bilibili.com/video/{bvid}"),
            published_at=published_at,
            duration_seconds=_duration_seconds(str(item.get("duration") or "0")),
            views=_parse_count(item.get("play")),
            likes=_parse_count(item.get("like")),
            comments=_parse_count(item.get("review")),
            raw=item,
            source_adapter=self.adapter_name,
            collected_at=now,
            metric_coverage=MetricCoverage(views=play_known, likes=item.get("like") is not None, comments=item.get("review") is not None),
            data_caveats=("B站公开搜索结果的互动指标可能不完整",),
        )


def collect_public(request: DiscoveryRequest, now: datetime | None = None) -> CollectionResult:
    collected_at = now or datetime.now(timezone.utc)
    adapters: dict[str, PublicAdapter] = {"youtube": YouTubePublicAdapter(), "bilibili": BilibiliPublicAdapter()}
    videos: list[VideoModel] = []
    statuses: list[SourceStatus] = []
    for platform in request.platforms:
        adapter = adapters.get(platform)
        if adapter is None:
            result = _unavailable(platform, "public-adapter", "该平台没有稳定的公开采集入口", collected_at)
        else:
            result = adapter.collect(request, collected_at)
        videos.extend(result.videos)
        statuses.extend(result.statuses)
    return CollectionResult(videos, statuses)


def _unavailable(platform: str, adapter: str, reason: str, now: datetime) -> CollectionResult:
    return CollectionResult([], [SourceStatus(platform, adapter, "unavailable", reason, now)])


def _failed(platform: str, adapter: str, reason: str, now: datetime) -> CollectionResult:
    return CollectionResult([], [SourceStatus(platform, adapter, "failed", reason, now)])


def _published_at(timestamp: object, upload_date: object) -> datetime | None:
    if timestamp is not None:
        try:
            return datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            pass
    value = str(upload_date or "")
    if len(value) == 8 and value.isdigit():
        return datetime.strptime(value, "%Y%m%d").replace(tzinfo=timezone.utc)
    return None


def _as_int(value: object) -> int:
    try:
        return max(0, int(float(value or 0)))
    except (TypeError, ValueError):
        return 0


def _parse_count(value: object) -> int:
    raw = str(value or "0").replace(",", "").strip()
    try:
        multiplier = 10_000 if raw.endswith("万") else 100_000_000 if raw.endswith("亿") else 1
        return max(0, int(float(raw.rstrip("万亿")) * multiplier))
    except ValueError:
        return 0


def _duration_seconds(value: str) -> int:
    try:
        parts = [int(part) for part in value.split(":")]
    except ValueError:
        return 0
    total = 0
    for part in parts:
        total = total * 60 + part
    return total
