import sys
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from transcription_backends import normalize_segment, transcribe_audio  # noqa: E402


def test_normalize_segment_adds_backend_and_language():
    result = normalize_segment({"timestamp": [1000, 2500], "text": "你好"}, "chinese", "zh")
    assert result == {
        "start": "00:00:01",
        "end": "00:00:02",
        "text": "你好",
        "language": "zh",
        "backend": "chinese",
    }


def test_normalize_segment_removes_sensevoice_tags():
    result = normalize_segment({"text": "<|zh|><|Speech|>你好  世界"}, "chinese", "zh")
    assert result["text"] == "你好 世界"


def test_unknown_backend_is_rejected(tmp_path):
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"fake")
    with pytest.raises(ValueError, match="Unsupported backend"):
        transcribe_audio(audio, "quality", "small", None, None, None, None)


def test_chinese_requires_local_asr_model(tmp_path):
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"fake")
    with pytest.raises(RuntimeError, match="--asr-model"):
        transcribe_audio(audio, "chinese", "small", "zh", None, None, None)
