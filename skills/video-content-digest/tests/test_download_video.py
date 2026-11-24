import sys
from contextlib import contextmanager
from email.message import Message
from io import BytesIO
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import download_video as downloader


@pytest.mark.parametrize(("short_url", "redirect_url", "expected"), [
    ("https://b23.tv/example?p=2", "https://www.bilibili.com/video/BV1wD4y1o7AS",
     ("bilibili", "BV1wD4y1o7AS", "2")),
    ("https://v.douyin.com/example/", "https://www.iesdouyin.com/share/video/123456/",
     ("douyin", "123456", "")),
])
def test_resolve_short_url(monkeypatch, short_url, redirect_url, expected):
    """短链保留原链接的分 P，普通视频标题可以包含验证码字样。"""
    @contextmanager
    def redirect(*args):
        with BytesIO("<title>验证码背后的技术</title>".encode()) as page:
            page.url = redirect_url
            page.headers = Message()
            page.headers["Content-Type"] = "text/html; charset=utf-8"
            yield page

    monkeypatch.setattr(downloader, "open_resource", redirect)
    assert downloader.resolve_url(short_url) == expected


def test_short_url_stops_on_http_200_challenge(monkeypatch):
    """页面 URL 中已有视频 ID 时，仍需识别返回 200 的安全验证页。"""
    @contextmanager
    def redirect(*args):
        with BytesIO("<html><head><title>安全验证</title></head></html>".encode()) as page:
            page.url = "https://www.douyin.com/video/123456"
            page.headers = Message()
            page.headers["Content-Type"] = "text/html; charset=utf-8"
            yield page

    monkeypatch.setattr(downloader, "open_resource", redirect)
    with pytest.raises(downloader.DownloadError) as caught:
        downloader.resolve_url("https://v.douyin.com/example/")
    assert caught.value.status == "blocked"
    assert caught.value.stage == "resolve_url"


def test_bilibili_selects_requested_part_and_compatible_tracks(monkeypatch):
    """请求 P2 对应的 CID，按清晰度及编码选择视频，并获取音轨。"""
    def get_json(url, referer, stage):
        assert referer == downloader.BILI_REFERER
        if stage == "metadata":
            return {"code": 0, "data": {"title": "示例", "bvid": "BV1wD4y1o7AS",
                    "pages": [{"page": 1, "cid": 10}, {"page": 2, "cid": 20}]}}
        assert parse_qs(urlsplit(url).query)["cid"] == ["20"]
        return {"code": 0, "data": {"dash": {
            "video": [
                {"id": 80, "codecid": 7, "baseUrl": "https://example.test/1080"},
                {"id": 64, "codecid": 12, "baseUrl": "https://example.test/hevc"},
                {"id": 64, "codecid": 7, "base_url": "https://example.test/avc"},
            ],
            "audio": [{"bandwidth": 10, "baseUrl": "https://example.test/audio"}],
        }}}

    monkeypatch.setattr(downloader, "get_json", get_json)
    source = downloader.bilibili_source("BV1wD4y1o7AS", "2")
    assert source.part == "2"
    assert source.canonical_url.endswith("?p=2")
    assert source.video_url == "https://example.test/avc"
    assert source.audio_url == "https://example.test/audio"


def test_douyin_stops_on_challenge(monkeypatch):
    """明确要求验证码时，返回风控状态供后续流程停止请求。"""
    monkeypatch.setattr(downloader, "get_json", lambda *args, **kwargs: {
        "status_code": 1, "status_msg": "请输入验证码",
    })
    with pytest.raises(downloader.DownloadError) as caught:
        downloader.douyin_source("123456")
    assert caught.value.status == "blocked"
    assert caught.value.stage == "playback"


def test_truncated_download_does_not_publish_mp4(monkeypatch, tmp_path):
    """媒体中断后清除临时下载，最终路径不会留下一份坏文件。"""
    @contextmanager
    def response(*args):
        with BytesIO(b"part") as body:
            body.status = 200
            body.headers = Message()
            body.headers["Content-Type"] = "video/mp4"
            body.headers["Content-Length"] = "8"
            yield body

    monkeypatch.setattr(downloader, "open_resource", response)
    source = downloader.MediaSource("douyin", "123456", "示例", "https://www.douyin.com/video/123456",
                                    downloader.DOUYIN_REFERER, "https://example.test/video")
    with pytest.raises(downloader.DownloadError, match="未下载完整"):
        downloader.save_media(source, tmp_path / "source.mp4", "ffmpeg")
    assert not list(tmp_path.iterdir())
