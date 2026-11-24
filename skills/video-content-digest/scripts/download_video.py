#!/usr/bin/env python3
"""从 B 站和抖音的公开播放器直连下载视频，返回媒体路径与来源 JSON。"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from http.client import HTTPException
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

from prepare_output import prepare_output
from resolve_video import classify_url


BILI_REFERER = "https://www.bilibili.com/"
DOUYIN_REFERER = "https://open.douyin.com/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
DEFAULT_ROOT = Path(".video-summary-radar/outputs")


@dataclass(frozen=True)
class MediaSource:
    platform: str
    video_id: str
    title: str
    canonical_url: str
    referer: str
    video_url: str
    audio_url: str = ""
    part: str = ""


class DownloadError(Exception):
    def __init__(self, stage: str, reason: str, status: str = "failed") -> None:
        """保留失败环节及是否遇到平台限制，供技能记录。"""
        super().__init__(reason)
        self.stage = stage
        self.status = status


class ShareRedirect(HTTPRedirectHandler):
    def __init__(self, platform: str) -> None:
        """记录短链接所属平台。"""
        self.platform = platform

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        """分享短链只跟随同一平台的网页跳转。"""
        target = urlsplit(newurl)
        if target.scheme != "https" or classify_url(target.hostname or "") != self.platform:
            raise DownloadError("resolve_url", "短链接跳到了平台之外的地址或非 HTTPS 地址")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


@contextmanager
def open_resource(url: str, headers: dict[str, str], stage: str, opener=urlopen):
    """匿名打开资源，并保留 HTTP 拒绝、限流及网络错误的失败环节。"""
    try:
        with opener(Request(url, headers={"User-Agent": USER_AGENT, **headers}), timeout=30) as response:
            yield response
    except HTTPError as exc:
        code = exc.code
        exc.close()
        if code in {403, 412, 429}:
            raise DownloadError(stage, f"平台拒绝请求或限流（HTTP {code}）", "blocked") from None
        if code in {401, 451}:
            raise DownloadError(stage, f"资源访问受限（HTTP {code}）", "restricted") from None
        raise DownloadError(stage, f"平台返回 HTTP {code}") from None
    except (URLError, HTTPException, ConnectionError, TimeoutError) as exc:
        raise DownloadError(stage, f"网络请求中断（{type(exc).__name__}）") from None


def get_json(url: str, referer: str, stage: str, *, origin: str = "") -> dict:
    """读取平台公开接口的 JSON，并识别 HTML 拦截页。"""
    headers = {"Referer": referer, "Accept": "application/json"}
    if origin:
        headers["Origin"] = origin
    with open_resource(url, headers, stage) as response:
        body = response.read().decode("utf-8", errors="replace").strip()
    if not body.startswith("{"):
        reason = "平台返回空响应" if not body else "平台返回了非 JSON 响应"
        raise platform_error(stage, reason, body if body.startswith("<") else "")
    try:
        return json.loads(body)
    except ValueError:
        raise DownloadError(stage, "平台返回了无效 JSON") from None


def platform_error(stage: str, reason: str, message: str = "") -> DownloadError:
    """区分平台明确提示的访问限制与普通接口失败。"""
    message = message.casefold()
    if any(marker in message for marker in ("验证码", "风控", "请求过于频繁", "访问过于频繁", "安全验证", "captcha", "verifycenter")):
        return DownloadError(stage, "平台要求安全验证或限制请求", "blocked")
    if any(marker in message for marker in ("请先登录", "登录后", "仅自己可见", "付费", "购买后", "login required")):
        return DownloadError(stage, "平台要求登录或限制该内容的访问", "restricted")
    return DownloadError(stage, reason)


def resolve_url(url: str) -> tuple[str, str, str]:
    """从长链或同平台短链提取视频 ID，保留 B 站分 P 参数。"""
    parsed = urlsplit(url)
    platform = classify_url(parsed.hostname or "")
    if parsed.scheme not in {"http", "https"} or platform not in {"bilibili", "douyin"}:
        raise DownloadError("resolve_url", "请输入 B 站或抖音的单视频链接")
    query = parse_qs(parsed.query, keep_blank_values=True)
    if parsed.hostname in {"b23.tv", "v.douyin.com"}:
        opener = build_opener(ShareRedirect(platform)).open
        with open_resource(url, {}, "resolve_url", opener) as response:
            parsed = urlsplit(response.url)
            title = ""
            if response.headers.get_content_type() == "text/html":
                head = response.read(16 * 1024).decode("utf-8", errors="replace")
                match = re.search(r"<title\b[^>]*>(.*?)</title>", head, re.IGNORECASE | re.DOTALL)
                title = match[1].strip() if match else ""
            challenge_path = {"captcha", "verifycenter"}.intersection(parsed.path.casefold().split("/"))
            challenge_title = re.fullmatch(
                r"(?:安全验证|验证码|请输入验证码|请求过于频繁|访问过于频繁|captcha|security verification)"
                r"(?:\s*[-_|｜]\s*(?:抖音|哔哩哔哩|bilibili))?", title, re.IGNORECASE,
            )
            if challenge_path or challenge_title:
                raise DownloadError("resolve_url", "短链接跳转到了平台验证或限流页面", "blocked")
        query = {**parse_qs(parsed.query, keep_blank_values=True), **query}
    if platform == "bilibili":
        match = re.fullmatch(r"/video/(BV[A-Za-z0-9]{10}|av[0-9]+)/?", parsed.path)
        if match:
            return platform, match[1], query.get("p", ["1"])[0]
    else:
        match = re.fullmatch(r"/(?:share/)?video/([0-9]+)/?", parsed.path)
        video_id = match[1] if match else query.get("modal_id", [""])[0]
        if re.fullmatch(r"[0-9]+", video_id):
            return platform, video_id, ""
    raise DownloadError("resolve_url", "链接中没有可识别的单视频 ID")


def get_bilibili_data(endpoint: str, query: dict, stage: str) -> dict:
    """读取 B 站公开接口，并处理平台返回的业务状态码。"""
    result = get_json(f"https://api.bilibili.com{endpoint}?{urlencode(query)}", BILI_REFERER, stage)
    code = result.get("code")
    if code in {-352, -412, -509, -799, 429}:
        raise DownloadError(stage, f"B 站触发风控或限流（{code}）", "blocked")
    if code in {-101, -403, -10403}:
        raise DownloadError(stage, f"B 站限制该资源的匿名访问（{code}）", "restricted")
    if code != 0 or not isinstance(result.get("data"), dict):
        raise platform_error(stage, f"B 站未返回数据（{code}）", str(result.get("message") or ""))
    return result["data"]


def bilibili_source(video_id: str, part: str) -> MediaSource:
    """按目标分 P 获取 B 站 DASH 轨道，或使用单段媒体。"""
    if not part.isascii() or not part.isdecimal() or len(part) > 6 or int(part) < 1:
        raise DownloadError("resolve_url", "B 站分 P 必须是正整数")
    key = {"aid": video_id[2:]} if video_id.startswith("av") else {"bvid": video_id}
    view = get_bilibili_data("/x/web-interface/view", key, "metadata")
    bvid = view.get("bvid") or ""
    if not re.fullmatch(r"BV[A-Za-z0-9]{10}", bvid) or ("bvid" in key and bvid != video_id):
        raise DownloadError("metadata", "B 站未返回目标视频的 BV 号")
    rights = view.get("rights") or {}
    if any(rights.get(name) for name in ("pay", "ugc_pay", "arc_pay", "ugc_pay_preview")):
        raise DownloadError("metadata", "B 站视频需要付费或仅开放试看", "restricted")
    pages = view.get("pages") or []
    page = next((item for item in pages if item["page"] == int(part)), None)
    if page is None:
        raise DownloadError("metadata", f"B 站视频没有第 {part} P")
    part = str(page["page"]) if len(pages) > 1 else ""
    canonical_url = f"{BILI_REFERER}video/{bvid}" + (f"?p={part}" if part else "")
    play = get_bilibili_data("/x/player/playurl", {
        "bvid": bvid, "cid": page["cid"], "qn": 64, "fnval": 16, "fnver": 0, "fourk": 0,
    }, "playback")
    if play.get("is_preview"):
        raise DownloadError("playback", "B 站播放器仅返回试看内容", "restricted")
    dash = play.get("dash") or {}
    video_tracks = [track for track in dash.get("video") or [] if track["id"] <= 64]
    audio_tracks = dash.get("audio") or []
    audio_url = ""
    if video_tracks and audio_tracks:
        video = max(video_tracks, key=lambda t: (t["id"], t.get("codecid") == 7, t.get("bandwidth", 0)))
        audio = max(audio_tracks, key=lambda t: t.get("bandwidth", 0))
        video_url = video.get("baseUrl") or video["base_url"]
        audio_url = audio.get("baseUrl") or audio["base_url"]
    elif len(play.get("durl") or []) == 1:
        video_url = play["durl"][0]["url"]
    else:
        raise DownloadError("playback", "B 站未返回可用的独立音视频轨道或单段媒体")
    return MediaSource("bilibili", bvid, view["title"], canonical_url, BILI_REFERER, video_url, audio_url, part)


def douyin_source(video_id: str) -> MediaSource:
    """通过抖音官方嵌入播放器的匿名接口取得原样播放地址。"""
    query = urlencode({"aweme_id": video_id, "aid": 6383})
    result = get_json(f"https://www.douyin.com/aweme/v1/web/aweme/detail/?{query}",
                      DOUYIN_REFERER, "playback", origin=DOUYIN_REFERER.rstrip("/"))
    detail = result.get("aweme_detail") or {}
    if result.get("status_code") != 0 or detail.get("aweme_id") != video_id:
        raise platform_error("playback", "抖音未返回目标视频的公开播放信息", str(result.get("status_msg") or ""))
    status = detail.get("status") or {}
    if any(status.get(name) for name in ("private_status", "part_see", "is_prohibited", "is_delete")):
        raise DownloadError("playback", "抖音视频已删除或限制访问", "restricted")
    video = detail.get("video") or {}
    if detail.get("images") or detail.get("image_post_info"):
        raise DownloadError("playback", "该抖音链接对应图文作品")
    urls = (video.get("play_addr") or {}).get("url_list") or []
    video_url = next((url for url in urls if url.startswith("https://")), None)
    if not video_url:
        raise DownloadError("playback", "抖音未返回公开的 HTTPS 媒体地址")
    return MediaSource("douyin", video_id, detail.get("desc") or "抖音视频",
                       f"https://www.douyin.com/video/{video_id}", DOUYIN_REFERER, video_url)


def download_track(url: str, referer: str, target: Path) -> None:
    """流式下载完整资源，拒绝网页、空文件和截断响应。"""
    if urlsplit(url).scheme != "https":
        raise DownloadError("download", "平台未返回 HTTPS 媒体地址")
    with open_resource(url, {"Referer": referer}, "download") as response:
        content_type = response.headers.get_content_type()
        if content_type.startswith("text/") or content_type == "application/json":
            body = response.read(64 * 1024).decode("utf-8", errors="replace")
            raise platform_error("download", "媒体地址返回了页面或 JSON", body)
        if content_type.startswith("image/"):
            raise DownloadError("download", "媒体地址返回了图片")
        if response.status != 200:
            raise DownloadError("download", f"媒体地址未返回完整文件（HTTP {response.status}）")
        with target.open("wb") as stream:
            shutil.copyfileobj(response, stream, length=1024 * 1024)
            size = stream.tell()
        length = response.headers.get("Content-Length", "")
        if not size or (length.isdecimal() and size != int(length)):
            raise DownloadError("download", "媒体为空或未下载完整")


def save_media(source: MediaSource, path: Path, ffmpeg: str) -> None:
    """下载到临时目录，用 FFmpeg 检查及封装后再交付 MP4。"""
    with TemporaryDirectory(prefix=".video-download-", dir=path.parent) as scratch:
        temp = Path(scratch)
        video = temp / "video.media"
        output = temp / "source.mp4"
        download_track(source.video_url, source.referer, video)
        command = [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-xerror", "-i", str(video)]
        if source.audio_url:
            audio = temp / "audio.media"
            download_track(source.audio_url, source.referer, audio)
            command.extend(["-i", str(audio), "-map", "0:v:0", "-map", "1:a:0"])
        else:
            command.extend(["-map", "0:v:0", "-map", "0:a:0?"])
        command.extend(["-c", "copy", "-movflags", "+faststart", str(output)])
        result = subprocess.run(command, capture_output=True, encoding="utf-8", errors="replace")
        if result.returncode:
            raise DownloadError("mux", f"FFmpeg 无法读取或封装媒体（{result.stderr.strip()}）")
        output.replace(path)


def main() -> int:
    """解析单条 URL，在技能的处理资料目录中保存媒体并报告结果。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="B 站或抖音单视频 URL，可使用分享短链接")
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument("--output-root", type=Path, default=DEFAULT_ROOT, help="视频产物根目录")
    destination.add_argument("--materials", type=Path, help="写入已指定的处理资料目录（例如批量作业）")
    args = parser.parse_args()

    stage = "resolve_url"
    try:
        platform, video_id, part = resolve_url(args.url)
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raise DownloadError("environment", "PATH 中找不到 FFmpeg")
        stage = "playback"
        source = bilibili_source(video_id, part) if platform == "bilibili" else douyin_source(video_id)
        stage = "output"
        if args.materials:
            materials = args.materials.resolve()
            materials.mkdir(parents=True, exist_ok=True)
        else:
            directory = prepare_output(args.output_root.resolve(), source.title, source.platform,
                                       source.video_id, source.canonical_url, source.part)
            materials = directory / "处理资料"
        suffix = f"-p{source.part}" if source.part else ""
        path = materials / f"直连-{source.platform}-{source.video_id}{suffix}.mp4"
        reused = path.is_file() and path.stat().st_size > 0
        if not reused:
            save_media(source, path, ffmpeg)
    except DownloadError as exc:
        print(json.dumps({"status": exc.status, "stage": exc.stage, "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "failed", "stage": stage, "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps({
        "status": "downloaded", "platform": source.platform, "video_id": source.video_id, "part": source.part,
        "title": source.title, "source_url": args.url, "canonical_url": source.canonical_url, "path": str(path),
        "channel": "platform-direct", "access": "anonymous-http", "reused": reused,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    raise SystemExit(main())
