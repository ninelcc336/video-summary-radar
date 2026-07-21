"""批量蒸馏候选的去重、状态更新和 manifest 读写。"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Literal

from creator_intelligence.models import DigestJob, DigestManifest, MetricCoverage, RankedVideo, VideoModel
from creator_intelligence.profile import parse_profile_payload, profile_to_payload


def video_key(video: VideoModel) -> str:
    """返回跨标题变动仍稳定的“平台:视频标识”关联键。"""
    return f"{video.platform}:{video.video_id}"


def select_digest_jobs(
    ranked: list[RankedVideo], mode: Literal["top", "all"], limit: int, now: datetime
) -> list[DigestJob]:
    """去重并按热度选择待蒸馏视频，避免重复转写成本。"""
    if mode not in {"top", "all"}:
        raise ValueError("mode must be top or all")
    if limit < 1:
        raise ValueError("limit must be positive")
    ordered = sorted(ranked, key=lambda item: (-item.hot_score, item.video.url))
    unique: dict[str, RankedVideo] = {}
    for item in ordered:
        unique.setdefault(video_key(item.video), item)
    candidates = list(unique.values()) if mode == "all" else list(unique.values())[:limit]
    return [
        DigestJob(
            video=item.video,
            stable_video_key=video_key(item.video),
            state="pending",
            updated_at=now,
        )
        for item in candidates
    ]


def mark_job_succeeded(manifest: DigestManifest, key: str, package_path: str, now: datetime) -> DigestManifest:
    """将目标作业标记为成功而不改变其余作业状态。"""
    return _replace_job(
        manifest,
        key,
        lambda job: replace(job, state="succeeded", package_path=package_path, failure_stage="", failure_reason="", updated_at=now),
    )


def mark_job_failed(manifest: DigestManifest, key: str, stage: str, reason: str, now: datetime) -> DigestManifest:
    """记录单条作业的失败阶段与原因，并让批次继续执行。"""
    if not stage.strip() or not reason.strip():
        raise ValueError("failed job requires stage and reason")
    return _replace_job(
        manifest,
        key,
        lambda job: replace(job, state="failed", failure_stage=stage, failure_reason=reason, updated_at=now),
    )


def _replace_job(manifest: DigestManifest, key: str, transform) -> DigestManifest:
    """以不可变方式替换 manifest 中指定的单个作业。"""
    replaced = False
    jobs: list[DigestJob] = []
    for job in manifest.jobs:
        if job.stable_video_key == key:
            jobs.append(transform(job))
            replaced = True
        else:
            jobs.append(job)
    if not replaced:
        raise KeyError(f"unknown digest job: {key}")
    return replace(manifest, jobs=tuple(jobs))


def manifest_to_payload(manifest: DigestManifest) -> dict[str, object]:
    """将 manifest 及嵌套视频元数据序列化为 JSON。"""
    return {
        "profile": profile_to_payload(manifest.profile),
        "created_at": manifest.created_at.isoformat(),
        "jobs": [_job_to_payload(job) for job in manifest.jobs],
    }


def write_manifest(manifest: DigestManifest, path: Path) -> Path:
    """把 manifest 写入 UTF-8 JSON 并返回绝对路径。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest_to_payload(manifest), ensure_ascii=False, indent=2), encoding="utf-8")
    return path.resolve()


def load_manifest(path: Path) -> DigestManifest:
    """加载 manifest，并恢复其账号画像、视频及时间字段。"""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("profile"), dict) or not isinstance(payload.get("jobs"), list):
        raise ValueError("digest manifest 格式不正确")
    return DigestManifest(
        profile=parse_profile_payload(payload["profile"]),
        jobs=tuple(_job_from_payload(item) for item in payload["jobs"]),
        created_at=_parse_datetime(payload.get("created_at")),
    )


def _job_to_payload(job: DigestJob) -> dict[str, object]:
    """序列化单条作业和关联视频。"""
    video = job.video
    return {
        "stable_video_key": job.stable_video_key,
        "state": job.state,
        "package_path": job.package_path,
        "failure_stage": job.failure_stage,
        "failure_reason": job.failure_reason,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "video": {
            "platform": video.platform, "creator_id": video.creator_id, "creator_name": video.creator_name,
            "domain": video.domain, "video_id": video.video_id, "title": video.title, "url": video.url,
            "published_at": video.published_at.isoformat(), "duration_seconds": video.duration_seconds,
            "views": video.views, "likes": video.likes, "comments": video.comments, "shares": video.shares,
            "favorites": video.favorites, "raw": video.raw, "source_adapter": video.source_adapter,
            "collected_at": video.collected_at.isoformat() if video.collected_at else None,
            "metric_coverage": video.metric_coverage.__dict__, "data_caveats": list(video.data_caveats),
        },
    }


def _job_from_payload(payload: object) -> DigestJob:
    """从 JSON 数据重建单条作业及其视频模型。"""
    if not isinstance(payload, dict) or not isinstance(payload.get("video"), dict):
        raise ValueError("digest job 格式不正确")
    video_data = payload["video"]
    coverage = video_data.get("metric_coverage", {})
    if not isinstance(coverage, dict):
        raise ValueError("metric_coverage 格式不正确")
    video = VideoModel(
        platform=str(video_data.get("platform", "")), creator_id=str(video_data.get("creator_id", "")),
        creator_name=str(video_data.get("creator_name", "")), domain=str(video_data.get("domain", "")),
        video_id=str(video_data.get("video_id", "")), title=str(video_data.get("title", "")), url=str(video_data.get("url", "")),
        published_at=_parse_datetime(video_data.get("published_at")), duration_seconds=int(video_data.get("duration_seconds", 0)),
        views=int(video_data.get("views", 0)), likes=int(video_data.get("likes", 0)), comments=int(video_data.get("comments", 0)),
        shares=int(video_data.get("shares", 0)), favorites=int(video_data.get("favorites", 0)),
        raw=video_data.get("raw", {}) if isinstance(video_data.get("raw", {}), dict) else {},
        source_adapter=str(video_data.get("source_adapter", "unknown")),
        collected_at=_parse_datetime(video_data.get("collected_at"), allow_none=True),
        metric_coverage=MetricCoverage(**{name: bool(coverage.get(name, False)) for name in MetricCoverage.__dataclass_fields__}),
        data_caveats=tuple(str(item) for item in video_data.get("data_caveats", [])),
    )
    return DigestJob(
        video=video, stable_video_key=str(payload.get("stable_video_key", "")), state=str(payload.get("state", "pending")),
        package_path=str(payload.get("package_path", "")), failure_stage=str(payload.get("failure_stage", "")),
        failure_reason=str(payload.get("failure_reason", "")), updated_at=_parse_datetime(payload.get("updated_at"), allow_none=True),
    )


def _parse_datetime(value: object, allow_none: bool = False) -> datetime | None:
    """解析带时区 ISO 8601 时间戳。"""
    if value is None and allow_none:
        return None
    if not value:
        raise ValueError("timestamp is required")
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed
