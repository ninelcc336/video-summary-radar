"""账号画像的规范化与 JSON 快照读写。"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from creator_intelligence.models import AccountProfile


def parse_profile_payload(payload: dict[str, object]) -> AccountProfile:
    """将对话或配置传入的账号画像转换为经过校验的模型。"""
    raw_url = str(payload.get("profile_url", "")).strip()
    if raw_url and urlparse(raw_url).scheme not in {"http", "https"}:
        raise ValueError("账号链接必须使用 http 或 https")
    exclusions = payload.get("exclusions", [])
    if not isinstance(exclusions, list):
        raise ValueError("exclusions must be a list")
    normalized_exclusions = tuple(dict.fromkeys(str(item).strip() for item in exclusions if str(item).strip()))
    return AccountProfile(
        platform=str(payload.get("platform", "")).strip(),
        domain=str(payload.get("domain", "")).strip(),
        audience=str(payload.get("audience", "")).strip(),
        source_text=str(payload.get("source_text", "")).strip(),
        profile_url=raw_url,
        content_format=str(payload.get("content_format", "")).strip(),
        business_goal=str(payload.get("business_goal", "")).strip(),
        exclusions=normalized_exclusions,
    )


def profile_to_payload(profile: AccountProfile) -> dict[str, object]:
    """将账号画像转换为稳定的 UTF-8 JSON 数据结构。"""
    return {
        "platform": profile.platform,
        "domain": profile.domain,
        "audience": profile.audience,
        "source_text": profile.source_text,
        "profile_url": profile.profile_url,
        "content_format": profile.content_format,
        "business_goal": profile.business_goal,
        "exclusions": list(profile.exclusions),
    }


def write_profile(profile: AccountProfile, path: Path) -> Path:
    """把账号画像快照写入指定路径并返回其绝对路径。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile_to_payload(profile), ensure_ascii=False, indent=2), encoding="utf-8")
    return path.resolve()


def load_profile(path: Path) -> AccountProfile:
    """从 JSON 快照加载账号画像并重新执行输入校验。"""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("账号画像必须是 JSON 对象")
    return parse_profile_payload(payload)
