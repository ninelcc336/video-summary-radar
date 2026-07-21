import json
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_env  # noqa: E402
from runtime_paths import model_paths, runtime_paths  # noqa: E402


def test_only_chinese_dependencies_are_supported():
    assert check_env.selected_packages("chinese") == {
        "yt-dlp": "yt_dlp",
        "funasr": "funasr",
        "torch": "torch",
        "torchaudio": "torchaudio",
    }


def test_runtime_is_inside_workspace_private_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("VIDEO_SUMMARY_RADAR_RUNTIME_DIR", str(tmp_path / "runtime"))
    paths = runtime_paths()
    assert paths.scope == "workspace"
    assert paths.home == tmp_path / "runtime"
    assert paths.models == paths.home / "models"
    assert paths.cache == paths.home / "cache"


def test_model_paths_are_inside_the_runtime_models_directory():
    paths = runtime_paths()
    models = model_paths(paths)
    assert models["asr"] == paths.models / "SenseVoiceSmall"
    assert models["vad"] == paths.models / "FSMN-VAD"
    assert models["punc"] == paths.models / "PUNC"


def test_default_dependency_mode_is_chinese():
    assert check_env.DEFAULT_MODE == "chinese"


def test_unsupported_modes_are_rejected():
    with pytest.raises(ValueError, match="Only chinese is supported"):
        check_env.selected_packages("light")


def test_runtime_probe_outputs_json_for_installed_package():
    code = check_env.runtime_package_probe_code("pytest", "pytest")
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["installed"] is True
    assert report["version"]


def test_ffmpeg_commands_are_platform_specific():
    windows = check_env.tool_commands("ffmpeg", "windows")
    macos = check_env.tool_commands("ffmpeg", "macos")
    assert windows["install"].startswith("winget install")
    assert windows["uninstall"].startswith("winget uninstall")
    assert macos["install"] == "brew install ffmpeg"
    assert macos["uninstall"] == "brew uninstall ffmpeg"


def test_first_check_reports_the_workspace_runtime(monkeypatch, tmp_path):
    runtime_home = tmp_path / "runtime"
    monkeypatch.setenv("VIDEO_SUMMARY_RADAR_RUNTIME_DIR", str(runtime_home))
    report = check_env.build_report("chinese", install=False)
    assert report["python_environment"]["runtime_exists"] is False
    assert report["python_environment"]["home"] == str(runtime_home)
    if sys.platform.startswith("win"):
        assert report["python_environment"]["runtime_python"].endswith("venv\\Scripts\\python.exe")
        assert report["python_environment"]["site_packages"].endswith("venv\\Lib\\site-packages")
    else:
        assert report["python_environment"]["runtime_python"].endswith("venv/bin/python")
        assert "/site-packages" in report["python_environment"]["site_packages"]


def test_cleanup_report_is_manual_and_preserves_models():
    report = check_env.build_report("chinese", install=False)
    cleanup = report["cleanup"]
    assert cleanup["manual_only"] is True
    assert any(path.endswith("venv") for path in cleanup["paths_to_delete"])
    assert report["models"]["base_dir"] in cleanup["preserved_paths"]
    assert "Remove-Item" in cleanup["windows_command"]
    assert cleanup["macos_command"].startswith("rm -rf")


def test_install_commands_target_workspace_runtime(monkeypatch, tmp_path):
    monkeypatch.setenv("VIDEO_SUMMARY_RADAR_RUNTIME_DIR", str(tmp_path / "runtime"))
    paths = runtime_paths()
    paths.runtime_python.parent.mkdir(parents=True, exist_ok=True)
    paths.runtime_python.write_bytes(b"python")
    calls = []

    def fake_run(command, check):
        calls.append(command)

    monkeypatch.setattr(check_env.subprocess, "run", fake_run)
    check_env.run_pip_install_into_runtime(["yt-dlp"], paths)
    assert calls == [[str(paths.runtime_python), "-m", "pip", "install", "yt-dlp"]]
    paths.runtime_python.unlink()
