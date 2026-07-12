from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from creator_intelligence.analyzer import AnalysisResult, analyze_ranked_videos
from creator_intelligence.markdown_renderer import render_markdown_report
from creator_intelligence.models import MetricCoverage, RankedVideo, SourceStatus, VideoModel
from creator_intelligence.ranker import rank_videos
from creator_intelligence.time_window import parse_range


@dataclass(frozen=True)
class ReportResult:
    markdown: str
    ranked_videos: list[RankedVideo]
    analysis: AnalysisResult
    statuses: list[SourceStatus]
    warnings: list[str]


def generate_report(
    range_value: str,
    input_path: str | Path | None = None,
    videos: list[VideoModel] | None = None,
    statuses: list[SourceStatus] | None = None,
    now: datetime | None = None,
) -> ReportResult:
    generated_at = now or datetime.now(timezone.utc)
    window = parse_range(range_value, generated_at)
    if input_path is not None:
        if videos is not None or statuses is not None:
            raise ValueError("provide either input_path or in-memory data")
        videos, statuses = load_collection(input_path)
    if videos is None:
        raise ValueError("input data is required")
    statuses = statuses or []
    ranked = rank_videos(videos, window, generated_at)
    analysis = analyze_ranked_videos(ranked)
    warnings = [f"{status.platform}: {status.reason}" for status in statuses if status.state != "available"]
    markdown = render_markdown_report(ranked, analysis, window, generated_at, statuses, warnings)
    return ReportResult(markdown, ranked, analysis, statuses, warnings)


def load_collection(path: str | Path) -> tuple[list[VideoModel], list[SourceStatus]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("collection must be a JSON object")
    videos = [_video_from_payload(item) for item in payload.get("videos", [])]
    statuses = [_status_from_payload(item) for item in payload.get("statuses", [])]
    return videos, statuses


def write_report(markdown: str, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return path


def default_report_path(generated_at: datetime | None = None) -> Path:
    value = generated_at or datetime.now(timezone.utc)
    return Path("reports") / f"creator-intelligence-{value.date().isoformat()}.md"


def _video_from_payload(item: object) -> VideoModel:
    if not isinstance(item, dict):
        raise ValueError("collection video must be an object")
    coverage = item.get("metric_coverage", {})
    if not isinstance(coverage, dict):
        raise ValueError("metric_coverage must be an object")
    caveats = item.get("data_caveats", [])
    if not isinstance(caveats, list):
        raise ValueError("data_caveats must be a list")
    return VideoModel(
        platform=str(item.get("platform", "")),
        creator_id=str(item.get("creator_id", "")),
        creator_name=str(item.get("creator_name", "")),
        domain=str(item.get("domain", "主题发现")),
        video_id=str(item.get("video_id", "")),
        title=str(item.get("title", "")),
        url=str(item.get("url", "")),
        published_at=_parse_datetime(item.get("published_at")),
        duration_seconds=int(item.get("duration_seconds", 0)),
        views=int(item.get("views", 0)),
        likes=int(item.get("likes", 0)),
        comments=int(item.get("comments", 0)),
        shares=int(item.get("shares", 0)),
        favorites=int(item.get("favorites", 0)),
        raw=item.get("raw", {}) if isinstance(item.get("raw", {}), dict) else {},
        source_adapter=str(item.get("source_adapter", "unknown")),
        collected_at=_parse_datetime(item.get("collected_at"), allow_none=True),
        metric_coverage=MetricCoverage(**{key: bool(coverage.get(key, False)) for key in MetricCoverage.__dataclass_fields__}),
        data_caveats=tuple(str(value) for value in caveats),
    )


def _status_from_payload(item: object) -> SourceStatus:
    if not isinstance(item, dict):
        raise ValueError("collection status must be an object")
    return SourceStatus(
        platform=str(item.get("platform", "")),
        adapter=str(item.get("adapter", "unknown")),
        state=str(item.get("state", "failed")),  # type: ignore[arg-type]
        reason=str(item.get("reason", "")),
        collected_at=_parse_datetime(item.get("collected_at"), allow_none=True),
        result_count=int(item.get("result_count", 0)),
    )


def _parse_datetime(value: object, allow_none: bool = False) -> datetime | None:
    if value is None and allow_none:
        return None
    if not value:
        raise ValueError("timestamp is required")
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
