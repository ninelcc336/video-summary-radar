"""将内容策略分析结果渲染为中文 Markdown 报告。"""

from __future__ import annotations

from creator_intelligence.models import DigestManifest, TopicRecommendation
from creator_intelligence.strategy import StrategyResult


def render_strategy_report(manifest: DigestManifest, result: StrategyResult) -> str:
    """生成包含蒸馏索引、规律、推荐和限制的固定章节报告。"""
    lines = [
        "# 创作者内容策略报告",
        "",
        f"- 账号定位：{manifest.profile.platform} / {manifest.profile.domain} / {manifest.profile.audience}",
        f"- 任务创建时间：{manifest.created_at.isoformat(timespec='seconds')}",
        "",
        "## 批量蒸馏索引",
        "",
        "| 视频 | 平台 | 热度状态 | 蒸馏状态 | 内容包 | 失败原因 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for job in manifest.jobs:
        package = job.package_path or "-"
        reason = job.failure_reason or "-"
        lines.append(
            f"| {_escape(job.video.title)} | {job.video.platform} | {job.video.views:,} 播放 | {job.state} | {_escape(package)} | {_escape(reason)} |"
        )
    if not manifest.jobs:
        lines.append("| - | - | - | - | - | 没有候选视频 |")

    lines.extend(["", "## 创作者与样本规律", ""])
    if result.sufficient_sample:
        lines.extend(f"- {observation}" for observation in result.observations)
    else:
        lines.append("- 样本不足，未输出高频规律结论。")

    lines.extend(["", "## 可复刻爆款选题池", ""])
    if result.recommendations:
        for index, item in enumerate(result.recommendations, start=1):
            lines.extend(_render_recommendation(index, item))
    else:
        lines.append("当前没有可用内容包，暂不生成选题推荐。")

    lines.extend(["", "## 优先级行动清单", ""])
    for index, item in enumerate(result.recommendations[:5], start=1):
        lines.append(f"{index}. 优先制作“{item.topic}”（总分 {item.total_score:.2f}，置信度 {item.confidence:.2f}）。")
    if not result.recommendations:
        lines.append("- 先补齐成功蒸馏的内容包，再生成行动清单。")

    lines.extend(["", "## 数据覆盖与限制", ""])
    lines.extend(f"- {warning}" for warning in result.warnings)
    failed = [job for job in manifest.jobs if job.state == "failed"]
    if failed:
        lines.append(f"- 失败作业数：{len(failed)}；详情见“批量蒸馏索引”。")
    if not result.warnings and not failed:
        lines.append("- 仅基于任务目录中有来源链接和内容包证据的数据生成结论。")
    lines.append("")
    return "\n".join(lines)


def _render_recommendation(index: int, item: TopicRecommendation) -> list[str]:
    """渲染单条可复刻选题的评分、证据和执行建议。"""
    lines = [
        f"### {index}. {_escape(item.topic)}",
        "",
        f"- 综合分：{item.total_score:.2f}；置信度：{item.confidence:.2f}",
        f"- 评分：近期热度 {item.recent_heat_score:.2f} / 可复刻性 {item.replicability_score:.2f} / 账号匹配 {item.profile_match_score:.2f} / 证据完整度 {item.evidence_completeness_score:.2f}",
        f"- 证据：{'、'.join(f'[来源]({url})' for url in item.evidence_urls)}",
        "- 标题方向：",
    ]
    lines.extend(f"  - {_escape(title)}" for title in item.title_directions)
    lines.append("- 内容大纲：")
    lines.extend(f"  - {_escape(step)}" for step in item.outline)
    lines.append("- 风险与避坑：")
    lines.extend(f"  - {_escape(risk)}" for risk in item.risks)
    lines.append("")
    return lines


def _escape(value: str) -> str:
    """转义 Markdown 表格中的竖线，避免结构被用户内容破坏。"""
    return value.replace("|", "\\|")
