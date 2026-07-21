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


def test_non_chinese_backend_is_rejected(tmp_path):
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"fake")
    with pytest.raises(ValueError, match="chinese"):
        transcribe_audio(audio, "light", "zh", None, None, None)


def test_chinese_uses_skill_local_asr_model_by_default(tmp_path, monkeypatch):
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"fake")
    expected = tmp_path / "SenseVoiceSmall"
    expected.mkdir()

    monkeypatch.setattr(
        "transcription_backends.model_paths",
        lambda: {"asr": expected, "vad": tmp_path / "FSMN-VAD", "punc": tmp_path / "PUNC"},
    )

    def fake_funasr(audio_path, asr_model, vad_model, punc_model, language):
        assert audio_path == audio
        assert asr_model == str(expected)
        assert vad_model is None
        assert punc_model is None
        assert language == "zh"
        return [{"text": "你好"}]

    monkeypatch.setattr("transcription_backends._transcribe_funasr", fake_funasr)
    assert transcribe_audio(audio, "chinese", "zh", None, None, None) == [{"text": "你好"}]


def test_chinese_requires_local_asr_model(tmp_path, monkeypatch):
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"fake")
    missing = tmp_path / "missing-model"
    monkeypatch.setattr(
        "transcription_backends.model_paths",
        lambda: {"asr": missing, "vad": tmp_path / "FSMN-VAD", "punc": tmp_path / "PUNC"},
    )
    with pytest.raises(FileNotFoundError, match="FunASR 模型路径不存在"):
        transcribe_audio(audio, "chinese", "zh", None, None, None)
