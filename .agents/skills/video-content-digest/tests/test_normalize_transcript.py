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
