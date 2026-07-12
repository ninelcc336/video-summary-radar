import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_env  # noqa: E402


def test_light_dependencies_use_faster_whisper():
    assert check_env.selected_packages("light") == {
        "yt-dlp": "yt_dlp",
        "faster-whisper": "faster_whisper",
    }


def test_chinese_dependencies_use_funasr():
    assert check_env.selected_packages("chinese") == {
        "yt-dlp": "yt_dlp",
        "funasr": "funasr",
        "torch": "torch",
        "torchaudio": "torchaudio",
    }


def test_legacy_modes_are_supported():
    assert check_env.normalize_mode("api") == "light"
    assert check_env.normalize_mode("local") == "chinese"
