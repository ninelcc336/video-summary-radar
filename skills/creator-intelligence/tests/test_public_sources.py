"""验证公开采集的匿名命令边界和失败处理，不访问真实平台。"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime

import pytest

from creator_intelligence import sources
from creator_intelligence.time_window import parse_range


def test_youtube_public_search_ignores_user_config(monkeypatch, now: datetime) -> None:
    """公开搜索必须禁用可隐式导入账号的配置，同时保留视频解析结果。"""
    calls = []

    def run_anonymous(command, **kwargs):
        """在外部命令边界拒绝加载用户配置，并返回一条公开元数据。"""
        calls.append(command)
        assert "--ignore-config" in command
        assert not any(arg.startswith(("--cookies", "--username", "--password")) for arg in command)
        return subprocess.CompletedProcess(command, 0, json.dumps({
            "id": "public-video", "title": "公开视频", "timestamp": now.timestamp(),
            "channel_id": "public-creator", "view_count": 42,
        }), "")

    monkeypatch.setattr(sources.shutil, "which", lambda name: name)
    monkeypatch.setattr(sources.subprocess, "run", run_anonymous)
    request = sources.DiscoveryRequest("AI 工具", ("youtube",), parse_range("7d", now), 1)

    result = sources.YouTubePublicAdapter().collect(request, now)

    assert len(calls) == 1
    assert [(video.video_id, video.views) for video in result.videos] == [("public-video", 42)]
    assert result.statuses[0].state == "available"
    assert result.statuses[0].result_count == 1


@pytest.mark.parametrize("reason", ["Sign in to confirm", "HTTP Error 429: Too Many Requests"])
def test_youtube_access_failure_does_not_retry_with_an_account(monkeypatch, now: datetime, reason: str) -> None:
    """登录要求或限流只产生可追溯失败，不追加账号参数或发起第二次请求。"""
    calls = []

    def fail_anonymously(command, **kwargs):
        """模拟平台拒绝匿名请求，并记录所有后续命令以发现账号回退。"""
        calls.append(command)
        return subprocess.CompletedProcess(command, 1, "", reason)

    monkeypatch.setattr(sources.shutil, "which", lambda name: name)
    monkeypatch.setattr(sources.subprocess, "run", fail_anonymously)
    request = sources.DiscoveryRequest("AI 工具", ("youtube",), parse_range("7d", now), 1)

    result = sources.YouTubePublicAdapter().collect(request, now)

    assert len(calls) == 1
    assert result.videos == []
    assert result.statuses[0].state == "failed"
    assert result.statuses[0].reason == reason
