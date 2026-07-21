import os
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "transcribe.py"


def test_help_lists_only_chinese_backend():
    result = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "chinese" in result.stdout
    for obsolete in ("light", "all", "api", "local", "faster-whisper"):
        assert obsolete not in result.stdout
    assert "--asr-model" in result.stdout
    assert "--model" not in result.stdout


def test_chinese_without_model_fails_without_downloading(tmp_path):
    """隔离工作区运行时，验证缺模型时不会尝试隐式下载。"""
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"fake")
    environment = os.environ.copy()
    environment["VIDEO_SUMMARY_RADAR_RUNTIME_DIR"] = str(tmp_path / "runtime")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(audio), "--backend", "chinese", "--output", str(tmp_path / "out.json")],
        capture_output=True,
        text=True,
        env=environment,
    )
    assert result.returncode != 0
    assert "FunASR 模型路径不存在" in result.stderr
