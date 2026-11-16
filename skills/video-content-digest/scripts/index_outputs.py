#!/usr/bin/env python3
"""从视频总结的 YAML 元数据生成产物索引，或按关键词筛选已有视频。"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import quote


def read_entry(path: Path, root: Path) -> dict:
    """读取约定的简单 YAML 字段及视频信息，不扫描转录、媒体或历史副本。"""
    text = path.read_text(encoding="utf-8-sig")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.DOTALL)
    if not match:
        raise ValueError(f"{path}: 缺少 YAML 元数据")
    metadata = {}
    current = ""
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        field = re.fullmatch(r"([a-z_]+):\s*(.*)", line)
        tag = re.fullmatch(r"\s+-\s+(.+)", line)
        if field:
            current, raw = field.groups()
            if current in metadata:
                raise ValueError(f"{path}: 重复字段 {current}")
            metadata[current] = [] if current == "tags" and not raw else (
                json.loads(raw) if raw.startswith(('"', '[')) else raw
            )
        elif tag and current == "tags" and isinstance(metadata[current], list):
            raw = tag.group(1)
            metadata[current].append(json.loads(raw) if raw.startswith('"') else raw)
        else:
            raise ValueError(f"{path}: 元数据仅支持单行字段、JSON 字符串和标签列表")
    for name in ("title", "category", "summary"):
        if not isinstance(metadata.get(name), str) or not metadata[name].strip():
            raise ValueError(f"{path}: {name} 必须为非空字符串")
        metadata[name] = metadata[name].strip()
        if "\n" in metadata[name] or "\r" in metadata[name]:
            raise ValueError(f"{path}: {name} 必须为单行")
    tags = metadata.get("tags")
    if (not isinstance(tags, list) or not 3 <= len(tags) <= 8
            or any(not isinstance(tag, str) or not tag.strip() or '\n' in tag or '\r' in tag for tag in tags)):
        raise ValueError(f"{path}: tags 需要 3–8 个非空单行字符串")
    metadata["tags"] = list(dict.fromkeys(tag.strip() for tag in tags))
    if len(metadata["tags"]) != len(tags):
        raise ValueError(f"{path}: 标签重复")
    info = re.search(r"^## 视频信息\s*\n(.*?)(?=^## |\Z)", text[match.end():], re.MULTILINE | re.DOTALL)
    fields = dict(re.findall(r"^- (作者|平台|处理状态)[：:]\s*(.+)$", info.group(1), re.MULTILINE)) if info else {}
    status = fields.get("处理状态", "").strip()
    if status not in {"已解析", "部分解析", "未取得正文"}:
        raise ValueError(f"{path}: 视频信息中缺少有效处理状态")
    metadata.update(author=fields.get("作者", "未确认").strip(), platform=fields.get("平台", "未确认").strip(),
                    status=status, summary_path=path.relative_to(root).as_posix(),
                    transcript_path=(path.with_name("口播稿.txt").relative_to(root).as_posix()
                                     if path.with_name("口播稿.txt").is_file() else ""))
    return metadata


def load_entries(root: Path) -> list[dict]:
    """只读取单条和批次的规范总结，按分类和标题稳定排序。"""
    paths = list(root.glob("*/视频总结.md")) + list(root.glob("*/digests/*/视频总结.md"))
    return sorted((read_entry(path, root) for path in paths), key=lambda item: (item["category"], item["title"], item["summary_path"]))


def render_index(entries: list[dict]) -> str:
    """生成含分类、标签、摘要和真实交付链接的轻量 Markdown 索引。"""
    lines = ["# 视频蒸馏产物索引", "", "由视频总结元数据生成；更新总结后重新运行 index_outputs.py。",
             "先按分类、标签、标题或摘要筛选，再读总结；精确引用读口播，证据核对再进入处理资料。",
             "解析状态不代表逐字听校或外部事实核验，具体限制见对应总结。", "",
             f"共 {len(entries)} 条视频。", ""]
    category = None
    for entry in entries:
        if category != entry["category"]:
            if category is not None:
                lines.append("")
            category = entry["category"]
            lines.extend([f"## {category}", "", "| 视频 | 标签 | 一句话摘要 | 作者 / 平台 | 状态 | 交付 |",
                          "| --- | --- | --- | --- | --- | --- |"])
        transcript = f" / [口播稿]({quote(entry['transcript_path'])})" if entry["transcript_path"] else " / 未取得口播"
        cells = [entry["title"], "、".join(entry["tags"]), entry["summary"],
                 f"{entry['author']} / {entry['platform']}", entry["status"],
                 f"[总结]({quote(entry['summary_path'])}){transcript}"]
        lines.append("| " + " | ".join(value.replace("|", "\\|") for value in cells) + " |")
    lines.append("")
    batches = sorted({str(Path(entry["summary_path"]).parents[2]).replace("\\", "/")
                      for entry in entries if "/digests/" in entry["summary_path"]})
    if batches:
        lines.extend(["## 批次目录", ""])
        lines.extend(f"- [{batch}]({quote(batch + '/')})" for batch in batches)
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    """重建索引或仅输出关键词匹配项；查询不修改任何文件。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path(".video-summary-radar/outputs"))
    parser.add_argument("--query", help="空格分隔多个关键词，忽略大小写，全部匹配")
    args = parser.parse_args()
    root = args.output_root.resolve()
    if not root.is_dir():
        parser.error(f"产物目录不存在：{root}")
    entries = load_entries(root)
    if args.query is not None:
        words = args.query.casefold().split()
        entries = [entry for entry in entries if all(word in " ".join(
            [entry["title"], entry["category"], entry["summary"], entry["author"], entry["platform"], *entry["tags"]]
        ).casefold() for word in words)]
        print(render_index(entries))
    else:
        target = root / "产物索引.md"
        target.write_text(render_index(entries), encoding="utf-8")
        print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
