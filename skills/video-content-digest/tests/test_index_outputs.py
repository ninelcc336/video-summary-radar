"""验证索引检索、交付链接和中间资料排除行为。"""

import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from index_outputs import load_entries, render_index  # noqa: E402


def write_summary(path: Path, title: str, tags: list[str], status: str = "已解析", block_tags: bool = False) -> None:
    """创建带真实测试元数据的最小总结，支持两种标签语法。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tag_text = ("\n" + "\n".join("  - " + json.dumps(tag, ensure_ascii=False) for tag in tags)
                if block_tags else " " + json.dumps(tags, ensure_ascii=False))
    path.write_text(f'---\ntitle: {json.dumps(title, ensure_ascii=False)}\ncategory: "AI内容创作"\n'
                    f'tags:{tag_text}\nsummary: "可视参考与提示词组合。"\n---\n\n# 视频总结\n\n'
                    f'## 视频信息\n\n- 作者：测试作者\n- 平台：douyin\n- 处理状态：{status}\n\n'
                    '## 整体概括\n正文包含一个不在索引中的独有词。\n', encoding="utf-8")


def test_index_includes_batch_and_partial_but_excludes_materials(tmp_path):
    """批次和部分解析可检索，证据与历史副本不混入索引，缺稿不链接。"""
    single = tmp_path / "图鉴__douyin-1" / "视频总结.md"
    batch = tmp_path / "某作者合集" / "digests" / "工具__douyin-2" / "视频总结.md"
    write_summary(single, "参考图鉴", ["运镜", "提示词", "Remotion"], block_tags=True)
    (single.parent / "口播稿.txt").write_text("真实口播", encoding="utf-8")
    write_summary(batch, "工作流机会", ["工作流", "定制交付", "Agent"], status="部分解析")
    write_summary(single.parent / "处理资料" / "视频总结.md", "历史草稿", ["历史", "旧稿", "资料"])
    write_summary(tmp_path / "处理记录" / "旧副本" / "视频总结.md", "旧副本", ["旧", "副本", "记录"])
    entries = load_entries(tmp_path)
    assert {entry["title"] for entry in entries} == {"参考图鉴", "工作流机会"}
    partial = next(entry for entry in entries if entry["status"] == "部分解析")
    assert partial["transcript_path"] == ""
    rendered = render_index(entries)
    assert "运镜、提示词、Remotion" in rendered
    assert "可视参考与提示词组合" in rendered
    assert rendered.count("[口播稿]") == 1
    assert "部分解析" in rendered
    import re
    for target in re.findall(r"\]\(([^)]+)\)", rendered):
        assert (tmp_path / unquote(target)).exists(), target


def test_query_matches_multiple_terms_without_rewriting_index(tmp_path):
    """查询在元数据范围内忽略大小写并取交集，不读取口播或改写索引。"""
    summary = tmp_path / "图鉴__douyin-1" / "视频总结.md"
    write_summary(summary, "参考图鉴", ["运镜", "提示词", "Remotion"])
    index = tmp_path / "产物索引.md"
    index.write_text("原索引内容", encoding="utf-8")
    command = [sys.executable, str(SCRIPTS / "index_outputs.py"), "--output-root", str(tmp_path)]
    hit = subprocess.run([*command, "--query", "运镜 remotion"], capture_output=True, text=True)
    assert hit.returncode == 0, hit.stderr
    assert "参考图鉴" in hit.stdout
    for query in ("运镜 不存在", "独有词"):
        miss = subprocess.run([*command, "--query", query], capture_output=True, text=True)
        assert miss.returncode == 0, miss.stderr
        assert "参考图鉴" not in miss.stdout
    assert index.read_text(encoding="utf-8") == "原索引内容"
    built = subprocess.run(command, capture_output=True, text=True)
    assert built.returncode == 0, built.stderr
    assert "参考图鉴" in index.read_text(encoding="utf-8")
    assert summary.read_text(encoding="utf-8").startswith("---")


def test_invalid_metadata_does_not_replace_existing_index(tmp_path):
    """缺少或无效元数据报出问题文件，避免生成看似完整但漏项的索引。"""
    summary = tmp_path / "图鉴__douyin-1" / "视频总结.md"
    write_summary(summary, "参考图鉴", ["运镜", "提示词", "动效"])
    index = tmp_path / "产物索引.md"
    index.write_text("保留旧索引", encoding="utf-8")
    original = summary.read_text(encoding="utf-8")
    for broken in ("# 缺少元数据", original.replace('"提示词", "动效"', '"运镜", "动效"'),
                   original.replace('summary: "可视参考与提示词组合。"', 'summary: ""')):
        summary.write_text(broken, encoding="utf-8")
        result = subprocess.run([sys.executable, str(SCRIPTS / "index_outputs.py"), "--output-root", str(tmp_path)],
                                capture_output=True, text=True)
        assert result.returncode != 0
        assert str(summary) in result.stderr
        assert index.read_text(encoding="utf-8") == "保留旧索引"
