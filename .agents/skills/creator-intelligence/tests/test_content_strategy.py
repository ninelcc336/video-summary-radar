"""内容策略模块的单元与端到端回归测试。"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

from creator_intelligence.batch import (
    load_manifest,
    mark_job_failed,
    select_digest_jobs,
    write_manifest,
)
from creator_intelligence.digest_parser import parse_content_package
from creator_intelligence.models import AccountProfile, DigestManifest
from creator_intelligence.profile import load_profile, parse_profile_payload, write_profile
from creator_intelligence.strategy import analyze_strategy

SKILL_DIR = Path(__file__).resolve().parents[1]
PREPARE_SCRIPT = SKILL_DIR / "scripts" / "prepare_digest_batch.py"
STRATEGY_SCRIPT = SKILL_DIR / "scripts" / "run_content_strategy.py"


def test_profile_requires_source() -> None:
    """账号画像缺少对话描述和主页链接时必须拒绝。"""
    with pytest.raises(ValueError, match="账号画像必须提供"):
        AccountProfile(platform="bilibili", domain="AI 工具", audience="创作者")


def test_profile_round_trip_keeps_exclusions(tmp_path: Path) -> None:
    """账号画像 JSON 快照必须保留对话来源和禁忌话题。"""
    profile = parse_profile_payload({
        "platform": "bilibili", "domain": "AI 工具", "audience": "独立开发者",
        "source_text": "做实操评测", "exclusions": ["投资建议", "投资建议"],
    })
    assert load_profile(write_profile(profile, tmp_path / "profile.json")) == profile


def test_profile_rejects_non_http_url() -> None:
    """本地文件 URL 不能作为可公开访问的账号主页链接。"""
    with pytest.raises(ValueError, match="http"):
        parse_profile_payload({"platform": "bilibili", "domain": "AI", "audience": "创作者", "profile_url": "file:///secret"})


def test_batch_deduplicates_and_isolates_failures(sample_ranked_videos, now: datetime) -> None:
    """top 模式按稳定键去重，失败只应影响目标作业。"""
    jobs = select_digest_jobs(sample_ranked_videos, mode="top", limit=2, now=now)
    assert [job.stable_video_key for job in jobs] == ["bilibili:BV1", "youtube:abc"]
    profile = AccountProfile("bilibili", "AI 工具", "独立开发者", source_text="测试账号")
    manifest = DigestManifest(profile, tuple(jobs), now)
    failed = mark_job_failed(manifest, "youtube:abc", "digest", "无字幕", now)
    assert next(job for job in failed.jobs if job.stable_video_key == "youtube:abc").state == "failed"
    assert next(job for job in failed.jobs if job.stable_video_key == "bilibili:BV1").state == "pending"


def test_parser_extracts_fixed_sections(tmp_path: Path, sample_ranked_videos, now: datetime) -> None:
    """内容包解析只提取固定章节，并保留作业来源链接。"""
    job = select_digest_jobs(sample_ranked_videos, mode="top", limit=1, now=now)[0]
    package = tmp_path / "content-package.md"
    package.write_text("### 选题角度\n低成本验证 AI 工具\n\n### 开头钩子\n00:03 别再盲买工具\n", encoding="utf-8")
    feature = parse_content_package(job, package)
    assert feature.topic_angle == "低成本验证 AI 工具"
    assert "00:03" in feature.hook
    assert feature.evidence_urls == (job.video.url,)
    assert feature.completeness == pytest.approx(2 / 6)


def test_strategy_hides_pattern_conclusion_for_small_sample(sample_ranked_videos, tmp_path: Path, now: datetime) -> None:
    """少于五条有效内容包时不得生成高频规律。"""
    job = select_digest_jobs(sample_ranked_videos, mode="top", limit=1, now=now)[0]
    package = tmp_path / "content-package.md"
    package.write_text("### 选题角度\nAI 工具实操\n\n### 开头钩子\n问题\n", encoding="utf-8")
    feature = parse_content_package(job, package)
    profile = AccountProfile("bilibili", "AI 工具", "独立开发者", source_text="测试账号")
    result = analyze_strategy(profile, sample_ranked_videos, [feature])
    assert result.sufficient_sample is False
    assert result.observations == ()
    assert result.recommendations[0].evidence_completeness_score > 0


def test_cli_creates_and_analyzes_digest_run(tmp_path: Path, sample_video, now: datetime) -> None:
    """两个 CLI 应生成可追溯任务文件、分析 JSON 和五章节报告。"""
    collection = tmp_path / "collection.json"
    profile = tmp_path / "profile.json"
    collection.write_text(json.dumps({
        "request": {"range": "7d"}, "videos": [{
            "platform": sample_video.platform, "creator_id": sample_video.creator_id,
            "creator_name": sample_video.creator_name, "domain": sample_video.domain,
            "video_id": sample_video.video_id, "title": sample_video.title, "url": sample_video.url,
            "published_at": datetime.now(sample_video.published_at.tzinfo).isoformat(),
            "duration_seconds": sample_video.duration_seconds, "views": sample_video.views,
            "likes": sample_video.likes, "comments": sample_video.comments, "shares": 0, "favorites": 0,
            "source_adapter": "fixture", "collected_at": datetime.now(sample_video.published_at.tzinfo).isoformat(),
            "metric_coverage": {"views": True, "likes": True, "comments": True, "shares": False, "favorites": False},
            "data_caveats": [],
        }], "statuses": []
    }, ensure_ascii=False), encoding="utf-8")
    profile.write_text(json.dumps({"platform": "bilibili", "domain": "AI 工具", "audience": "独立开发者", "source_text": "测试"}, ensure_ascii=False), encoding="utf-8")
    run_dir = tmp_path / "run"
    prepared = subprocess.run(
        [sys.executable, str(PREPARE_SCRIPT), "--collection", str(collection), "--profile", str(profile), "--output-dir", str(run_dir)],
        capture_output=True, text=True,
    )
    assert prepared.returncode == 0, prepared.stderr
    manifest = load_manifest(run_dir / "digest-manifest.json")
    job = manifest.jobs[0]
    package = run_dir / job.package_path
    package.parent.mkdir(parents=True)
    package.write_text(
        "### 选题角度\nAI 工具实操\n\n### 开头钩子\n00:03 先看误区\n\n### 内容结构\n问题到案例\n\n### 视频爆点\n反常识\n\n### 互动引导\n评论讨论\n\n### 时间线\n00:03 钩子\n",
        encoding="utf-8",
    )
    completed = subprocess.run([sys.executable, str(STRATEGY_SCRIPT), "--run-dir", str(run_dir)], capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr
    report = (run_dir / "report.md").read_text(encoding="utf-8")
    for heading in ("批量蒸馏索引", "创作者与样本规律", "可复刻爆款选题池", "优先级行动清单", "数据覆盖与限制"):
        assert f"## {heading}" in report
    assert json.loads((run_dir / "analysis.json").read_text(encoding="utf-8"))["recommendations"]


def test_skill_docs_describe_batch_contract() -> None:
    """两个 skill 文档必须说明批量协作接口和单视频边界。"""
    creator_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    digest_text = (SKILL_DIR.parent / "video-content-digest" / "SKILL.md").read_text(encoding="utf-8")
    for value in ("prepare_digest_batch.py", "digest-manifest.json", "run_content_strategy.py", "可复刻爆款选题"):
        assert value in creator_text
    assert "单视频" in digest_text
    assert "content-package.md" in digest_text
