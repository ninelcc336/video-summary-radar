import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from normalize_transcript import parse_timed_blocks  # noqa: E402


def test_numeric_only_caption_is_preserved():
    content = "1\n00:00:01,000 --> 00:00:02,000\n2024\n"
    assert parse_timed_blocks(content) == [
        {"start": "00:00:01", "end": "00:00:02", "text": "2024"}
    ]


def test_srt_without_blank_lines_keeps_cues_separate():
    content = (
        "1\n00:00:01,000 --> 00:00:02,000\n第一句\n"
        "2\n00:00:02,000 --> 00:00:03,000\n第二句\n"
    )
    assert parse_timed_blocks(content) == [
        {"start": "00:00:01", "end": "00:00:02", "text": "第一句"},
        {"start": "00:00:02", "end": "00:00:03", "text": "第二句"},
    ]


def test_txt_export_preserves_speech_and_protects_edits(tmp_path):
    """TXT 不携带时间或报告信息，重复导出不覆盖人工修改。"""
    import json
    import subprocess
    source = tmp_path / "transcript.json"
    target = tmp_path / "口播稿.txt"
    source.write_text(json.dumps([{"start": "00:00:01", "end": "00:00:02", "text": "第一句，2024。"},
                                  {"text": "第二段：[听不清]。"}], ensure_ascii=False), encoding="utf-8")
    command = [sys.executable, str(SCRIPTS / "normalize_transcript.py"), str(source), "--output", str(target), "--format", "txt"]
    first = subprocess.run(command, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    assert target.read_text(encoding="utf-8") == "第一句，2024。\n\n第二段：[听不清]。\n"
    assert subprocess.run(command, capture_output=True).returncode == 0
    target.write_text("人工修订", encoding="utf-8")
    assert subprocess.run(command, capture_output=True).returncode != 0
    assert target.read_text(encoding="utf-8") == "人工修订"


def test_invalid_json_cannot_be_exported_as_speech(tmp_path):
    """页面元数据、损坏 JSON 和空转录都不能生成伪造口播。"""
    import subprocess
    for content in ('{"title": "视频摘要"}', '{broken', '[]'):
        source = tmp_path / "page.json"
        source.write_text(content, encoding="utf-8")
        target = tmp_path / "口播稿.txt"
        result = subprocess.run([sys.executable, str(SCRIPTS / "normalize_transcript.py"), str(source),
                                 "--output", str(target), "--format", "txt"], capture_output=True)
        assert result.returncode != 0
        assert not target.exists()
