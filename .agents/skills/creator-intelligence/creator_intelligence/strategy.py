"""基于内容包证据和账号画像生成可复刻选题策略。"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from creator_intelligence.batch import video_key
from creator_intelligence.models import AccountProfile, ContentFeature, RankedVideo, TopicRecommendation


MINIMUM_PATTERN_SAMPLE = 5


@dataclass(frozen=True)
class StrategyResult:
    """封装策略分析的推荐、样本规律、警告和样本状态。"""

    recommendations: tuple[TopicRecommendation, ...]
    observations: tuple[str, ...]
    sufficient_sample: bool
    warnings: tuple[str, ...]


def analyze_strategy(
    profile: AccountProfile, ranked: list[RankedVideo], features: list[ContentFeature]
) -> StrategyResult:
    """汇总成功内容包并生成证据驱动的选题推荐。"""
    ranked_by_key = {video_key(item.video): item for item in ranked}
    matched = [feature for feature in features if feature.stable_video_key in ranked_by_key]
    warnings = tuple(f"未找到采集元数据：{feature.stable_video_key}" for feature in features if feature not in matched)
    recommendations = build_recommendations(profile, ranked_by_key, matched)
    sufficient = len(matched) >= MINIMUM_PATTERN_SAMPLE
    observations = build_observations(matched) if sufficient else ()
    if not sufficient:
        warnings += (f"有效内容包仅 {len(matched)} 条，至少 {MINIMUM_PATTERN_SAMPLE} 条才输出高频规律。",)
    return StrategyResult(tuple(recommendations), observations, sufficient, warnings)


def build_recommendations(
    profile: AccountProfile, ranked_by_key: dict[str, RankedVideo], features: list[ContentFeature]
) -> list[TopicRecommendation]:
    """把每条已蒸馏视频转换为按四项分量排序的推荐。"""
    max_hot = max((item.hot_score for item in ranked_by_key.values()), default=0.0)
    recommendations: list[TopicRecommendation] = []
    for feature in features:
        ranked = ranked_by_key[feature.stable_video_key]
        topic = feature.topic_angle or ranked.video.title
        heat = round((ranked.hot_score / max_hot * 100.0) if max_hot > 0 else 0.0, 2)
        replicability = calculate_replicability(feature)
        match = calculate_profile_match(profile, topic)
        evidence = round(feature.completeness * 100.0, 2)
        total = round(0.35 * heat + 0.30 * replicability + 0.20 * match + 0.15 * evidence, 2)
        confidence = calculate_confidence(feature.completeness, len(features))
        recommendations.append(
            TopicRecommendation(
                topic=topic,
                recent_heat_score=heat,
                replicability_score=replicability,
                profile_match_score=match,
                evidence_completeness_score=evidence,
                total_score=total,
                confidence=confidence,
                evidence_urls=feature.evidence_urls,
                title_directions=(f"{topic}：先别急着跟风，先用这一招验证", f"我用一个案例拆解 {topic}"),
                outline=("开头：指出受众正在付出的成本或误区", "中段：复刻原视频的论点—案例—转折结构", "结尾：给出可执行检查表并提出讨论问题"),
                risks=_risks(feature, profile),
            )
        )
    return sorted(recommendations, key=lambda item: (-item.total_score, item.topic))


def calculate_replicability(feature: ContentFeature) -> float:
    """依据钩子、结构、爆点和互动引导四类证据计算可复刻性。"""
    evidence = (feature.hook, feature.structure, feature.highlights, feature.interaction)
    return round(sum(1 for item in evidence if item.strip()) / len(evidence) * 100.0, 2)


def calculate_profile_match(profile: AccountProfile, topic: str) -> float:
    """使用账号领域和受众词与选题切口的词交集计算匹配度。"""
    profile_terms = _terms(f"{profile.domain} {profile.audience} {profile.content_format}")
    topic_terms = _terms(topic)
    if not profile_terms or not topic_terms:
        return 0.0
    overlap = len(profile_terms & topic_terms)
    return round(min(100.0, overlap / len(profile_terms) * 100.0), 2)


def calculate_confidence(completeness: float, sample_count: int) -> float:
    """以证据完整度和最多五条样本的覆盖率计算保守置信度。"""
    return round(min(completeness, min(sample_count, MINIMUM_PATTERN_SAMPLE) / MINIMUM_PATTERN_SAMPLE) * 100.0, 2)


def build_observations(features: list[ContentFeature]) -> tuple[str, ...]:
    """仅在样本充足时输出基于高频选题切口的描述性观察。"""
    topics = [feature.topic_angle for feature in features if feature.topic_angle]
    if not topics:
        return ()
    common_topic, count = Counter(topics).most_common(1)[0]
    return (f"在 {len(features)} 条有效内容包中，“{common_topic}”出现 {count} 次，是当前样本的高频切口。",)


def _terms(value: str) -> set[str]:
    """抽取用于轻量匹配的中文双字词和英文词。"""
    terms: set[str] = set(re.findall(r"[A-Za-z][A-Za-z0-9_-]{1,}|[\u4e00-\u9fff]{2}", value.lower()))
    return {term for term in terms if term not in {"内容", "视频", "用户", "创作者"}}


def _risks(feature: ContentFeature, profile: AccountProfile) -> tuple[str, ...]:
    """根据证据缺失和账号禁忌生成合规复刻提示。"""
    risks = ["复刻选题角度与叙事结构，不照抄原文、画面或未验证事实。"]
    if feature.completeness < 1.0:
        risks.append("内容包存在缺失章节，发布前需回看原视频核验细节。")
    if profile.exclusions:
        risks.append(f"避开账号禁忌：{'、'.join(profile.exclusions)}。")
    return tuple(risks)
