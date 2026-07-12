from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from creator_intelligence.models import RankedVideo


STOPWORDS = {"的", "了", "和", "与", "一个", "一遍", "我用", "如何", "为什么", "the", "and", "for", "with", "to", "of", "in"}
MINIMUM_PATTERN_SAMPLE = 5


@dataclass(frozen=True)
class AnalysisResult:
    total_videos: int
    average_engagement_rate: float
    top_keywords: list[tuple[str, int]]
    duration_buckets: list[tuple[str, int]]
    publish_hour_buckets: list[tuple[str, int]]
    platform_counts: list[tuple[str, int]]
    domain_counts: list[tuple[str, int]]
    observations: list[str]
    sufficient_sample: bool


def analyze_ranked_videos(ranked_videos: list[RankedVideo]) -> AnalysisResult:
    keywords = Counter[str]()
    durations = Counter[str]()
    hours = Counter[str]()
    platforms = Counter[str]()
    domains = Counter[str]()
    for item in ranked_videos:
        video = item.video
        keywords.update(_extract_keywords(video.title))
        durations[_duration_bucket(video.duration_seconds)] += 1
        hours[_hour_bucket(video.published_at.hour)] += 1
        platforms[video.platform] += 1
        domains[video.domain] += 1

    total = len(ranked_videos)
    average = sum(item.engagement_rate for item in ranked_videos) / total if total else 0.0
    result = AnalysisResult(
        total_videos=total,
        average_engagement_rate=average,
        top_keywords=keywords.most_common(8),
        duration_buckets=durations.most_common(),
        publish_hour_buckets=hours.most_common(),
        platform_counts=platforms.most_common(),
        domain_counts=domains.most_common(),
        observations=[],
        sufficient_sample=total >= MINIMUM_PATTERN_SAMPLE,
    )
    return AnalysisResult(**{**result.__dict__, "observations": _build_observations(result)})


def _extract_keywords(title: str) -> list[str]:
    tokens: list[str] = []
    for token in re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z0-9_-]{2,}", title.lower()):
        if re.fullmatch(r"[\u4e00-\u9fff]{5,}", token):
            tokens.extend(_split_chinese_phrase(token))
        else:
            tokens.append(token)
    return [token for token in tokens if token not in STOPWORDS]


def _split_chinese_phrase(phrase: str) -> list[str]:
    compact = re.sub(r"[的了和与]", "", phrase)
    return [compact[index : index + 2] for index in range(0, len(compact) - 1, 2)]


def _duration_bucket(seconds: int) -> str:
    if seconds < 60:
        return "60秒以内"
    if seconds < 180:
        return "1-3分钟"
    if seconds < 600:
        return "3-10分钟"
    if seconds < 1800:
        return "10-30分钟"
    return "30分钟以上"


def _hour_bucket(hour: int) -> str:
    if 0 <= hour < 6:
        return "凌晨"
    if 6 <= hour < 12:
        return "上午"
    if 12 <= hour < 18:
        return "下午"
    return "晚间"


def _build_observations(result: AnalysisResult) -> list[str]:
    if not result.sufficient_sample:
        return [f"样本不足（当前 {result.total_videos} 条，至少需要 {MINIMUM_PATTERN_SAMPLE} 条），不输出爆款规律结论。"]
    observations: list[str] = []
    if result.top_keywords:
        observations.append(f"高热度标题更常出现这些关键词：{'、'.join(word for word, _ in result.top_keywords[:5])}。")
    if result.duration_buckets:
        observations.append(f"高热度视频时长主要集中在：{result.duration_buckets[0][0]}。")
    if result.publish_hour_buckets:
        observations.append(f"发布时间表现较突出的时段是：{result.publish_hour_buckets[0][0]}。")
    if result.average_engagement_rate >= 0.08:
        observations.append("可用互动指标显示整体互动率较高。")
    return observations
