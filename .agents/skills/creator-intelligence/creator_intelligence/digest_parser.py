"""将 video-content-digest 的固定 Markdown 内容包转换为策略特征。"""

from __future__ import annotations

import re
from pathlib import Path

from creator_intelligence.models import ContentFeature, DigestJob


SECTION_NAMES = ("选题角度", "开头钩子", "内容结构", "视频爆点", "互动引导", "时间线")


def parse_content_package(job: DigestJob, path: Path) -> ContentFeature:
    """解析单个内容包，保留原始章节而不推断缺失信息。"""
    text = path.read_text(encoding="utf-8")
    sections = {name: section_text(text, name) for name in SECTION_NAMES}
    return ContentFeature(
        stable_video_key=job.stable_video_key,
        topic_angle=sections["选题角度"],
        hook=sections["开头钩子"],
        structure=sections["内容结构"],
        highlights=sections["视频爆点"],
        interaction=sections["互动引导"],
        timeline=sections["时间线"],
        evidence_urls=(job.video.url,),
        completeness=evidence_completeness(sections),
    )


def section_text(markdown: str, heading: str) -> str:
    """提取指定二级或三级标题至下一个同级或更高标题之间的文本。"""
    match = re.search(rf"^(?P<level>##{{2,3}})\s+{re.escape(heading)}\s*$", markdown, flags=re.MULTILINE)
    if match is None:
        return ""
    level = len(match.group("level"))
    following = markdown[match.end() :]
    boundary = re.search(rf"^#{{1,{level}}}\s+", following, flags=re.MULTILINE)
    value = following[: boundary.start() if boundary else None].strip()
    return value


def evidence_completeness(sections: dict[str, str]) -> float:
    """按六个固定内容包章节的可用性计算证据完整度。"""
    populated = sum(1 for name in SECTION_NAMES if sections.get(name, "").strip())
    return populated / len(SECTION_NAMES)
