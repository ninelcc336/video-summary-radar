from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from creator_intelligence.analyzer import AnalysisResult
from creator_intelligence.models import RankedVideo, SourceStatus
from creator_intelligence.time_window import TimeWindow


def render_markdown_report(
    ranked_videos: list[RankedVideo],
    analysis: AnalysisResult,
    window: TimeWindow,
    generated_at: datetime,
    statuses: list[SourceStatus] | None = None,
    warnings: list[str] | None = None,
) -> str:
    lines = [
        "# Creator Intelligence 爆款视频报告",
        "",
        f"- 统计范围：{window.label}（{window.start_at.date()} 至 {window.end_at.date()}）",
        f"- 生成时间：{generated_at.isoformat(timespec='seconds')}",
        f"- 入榜视频数：{len(ranked_videos)}",
        "",
        "## 各平台热度榜单",
        "",
    ]
    grouped: dict[str, list[RankedVideo]] = defaultdict(list)
    for item in ranked_videos:
        grouped[item.video.platform].append(item)
    if not grouped:
        lines.append("当前时间范围内没有可验证的视频数据。")
    for platform, items in grouped.items():
        lines.extend([f"### {platform}", "", "| 排名 | 博主 | 标题 | 发布时间 | 播放量 | 互动率 | 热度分 | 链接 |", "| --- | --- | --- | --- | ---: | ---: | ---: | --- |"])
        for index, item in enumerate(items, start=1):
            video = item.video
            lines.append(
                "| {rank} | {creator} | {title} | {published} | {views} | {rate} | {score:.2f} | [打开]({url}) |".format(
                    rank=index,
                    creator=_escape_table(video.creator_name),
                    title=_escape_table(video.title),
                    published=video.published_at.strftime("%Y-%m-%d %H:%M"),
                    views=f"{video.views:,}" if video.metric_coverage.views else "未提供",
                    rate=f"{item.engagement_rate:.2%}" if video.metric_coverage.likes else "指标不完整",
                    score=item.hot_score,
                    url=video.url,
                )
            )
        lines.append("")

    lines.extend(["## 跨平台参考榜单", "", "不同平台的绝对播放量不可直接等价；以下仅按已取得的播放量作参考。", ""])
    cross_platform = sorted(ranked_videos, key=lambda item: item.video.views, reverse=True)
    if cross_platform:
        lines.extend(["| 排名 | 平台 | 标题 | 播放量 | 链接 |", "| --- | --- | --- | ---: | --- |"])
        for index, item in enumerate(cross_platform, start=1):
            video = item.video
            lines.append(f"| {index} | {video.platform} | {_escape_table(video.title)} | {video.views:,} | [打开]({video.url}) |")
    else:
        lines.append("无可用于跨平台参考的数据。")

    lines.extend(["", "## 爆款规律分析", ""])
    for observation in analysis.observations or ["样本不足，暂无法形成稳定规律。"]:
        lines.append(f"- {observation}")
    if analysis.sufficient_sample:
        lines.extend(["", "## 维度分布", ""])
        lines.extend(_render_distribution("平台", analysis.platform_counts))
        lines.extend(_render_distribution("领域", analysis.domain_counts))
        lines.extend(_render_distribution("时长", analysis.duration_buckets))
        lines.extend(_render_distribution("发布时间", analysis.publish_hour_buckets))
        lines.extend(_render_distribution("标题关键词", analysis.top_keywords))

    lines.extend(["", "## 数据覆盖与限制", "", "| 平台 | 数据入口 | 状态 | 返回数量 | 采集时间 | 说明 |", "| --- | --- | --- | ---: | --- | --- |"])
    for status in statuses or []:
        collected = status.collected_at.isoformat(timespec="seconds") if status.collected_at else "未采集"
        reason = status.reason or "成功"
        lines.append(f"| {status.platform} | {status.adapter} | {status.state} | {status.result_count} | {collected} | {_escape_table(reason)} |")
    if not statuses:
        lines.append("| - | - | unavailable | 0 | - | 未提供数据源状态 |")
    if warnings:
        lines.extend(["", "### 采集警告", ""])
        lines.extend(f"- {warning}" for warning in warnings)
    lines.append("")
    return "\n".join(lines)


def _render_distribution(title: str, values: list[tuple[str, int]]) -> list[str]:
    lines = [f"### {title}", ""]
    lines.extend([f"- {name}: {count}" for name, count in values] or ["无数据。"]) 
    lines.append("")
    return lines


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|")
