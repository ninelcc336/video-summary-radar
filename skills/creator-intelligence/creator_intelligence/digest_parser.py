"""将 video-content-digest 的固定 Markdown 内容包转换为策略特征。"""

from __future__ import annotations

import re
from pathlib import Path

from creator_intelligence.models import ContentFeature, DigestJob


SECTION_NAMES = ("选题角度", "开头钩子", "内容结构", "视频爆点", "互动引导", "时间线")


def parse_content_package(job: DigestJob, path: Path) -> ContentFeature:
    """读取新版总结或历史六章节内容包；不推断钩子、互动和时间线。"""
    text = path.read_text(encoding="utf-8")
    overview = section_text(text, "整体概括")
    if overview:
        value = section_text(text, "最有价值的部分")
        body = section_text(text, "核心内容与必要展开")
        sources = section_text(text, "内容缺口与来源")
        info = section_text(text, "视频信息")
        if not re.search(r"处理状态[：:]\s*已解析(?:\s|$)", info.replace("**", "")):
            raise ValueError("部分解析的总结不能作为完整蒸馏成功样本")
        return ContentFeature(
            stable_video_key=job.stable_video_key, topic_angle=overview, hook="", structure=body,
            highlights=value, interaction="", timeline="", evidence_urls=(job.video.url,),
            completeness=sum(bool(item.strip()) for item in (info, overview, value, body, sources)) / 5,
        )
    sections = {name: section_text(text, name) for name in SECTION_NAMES}
    if not any(sections.values()):
        raise ValueError("未识别到视频总结或历史内容包章节")
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
    match = re.search(rf"^(?P<level>#{{2,3}})\s+{re.escape(heading)}\s*$", markdown, flags=re.MULTILINE)
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
