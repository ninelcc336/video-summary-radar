import sys
import json
import subprocess
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_env  # noqa: E402
from runtime_paths import default_home, detect_scope, runtime_paths  # noqa: E402


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


def test_default_dependency_mode_is_chinese():
    assert check_env.DEFAULT_MODE == "chinese"


def test_runtime_probe_outputs_json_for_installed_package():
    code = check_env.runtime_package_probe_code("pytest", "pytest")
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["installed"] is True
    assert report["version"]


def test_default_home_supports_windows_and_macos():
    windows = default_home("win32", {"LOCALAPPDATA": r"C:\\Users\\demo"})
    macos = default_home("darwin", {})
    assert windows.parts[-2:] == ("VideoSummaryRadar", "video-content-digest")
    assert "Application Support" in macos.parts
    assert macos.parts[-2:] == ("VideoSummaryRadar", "video-content-digest")


def test_environment_override_is_used(monkeypatch, tmp_path):
    monkeypatch.setenv("VIDEO_DIGEST_HOME", str(tmp_path / "custom-runtime"))
    paths = runtime_paths()
    assert paths.home == (tmp_path / "custom-runtime").resolve()
    assert paths.models == paths.home / "models"
    assert paths.cache == paths.home / "cache"


def test_scope_can_be_overridden():
    global_scope, global_root = detect_scope("global", skill_path=Path(__file__).resolve().parents[1])
    project_scope, project_root = detect_scope("project", skill_path=Path(__file__).resolve().parents[1])
    assert global_scope == "global"
    assert global_root is None
    assert project_scope == "project"
    assert project_root is not None


def test_ffmpeg_commands_are_platform_specific():
    windows = check_env.tool_commands("ffmpeg", "windows")
    macos = check_env.tool_commands("ffmpeg", "macos")
    assert windows["install"].startswith("winget install")
    assert windows["uninstall"].startswith("winget uninstall")
    assert macos["install"] == "brew install ffmpeg"
    assert macos["uninstall"] == "brew uninstall ffmpeg"


def test_first_check_reports_the_managed_runtime_target(monkeypatch, tmp_path):
    monkeypatch.setenv("VIDEO_DIGEST_HOME", str(tmp_path / "runtime"))
    report = check_env.build_report("light", install=False)
    assert report["python_environment"]["runtime_exists"] is False
    assert report["python_environment"]["runtime_python"].endswith("venv\\Scripts\\python.exe")
    assert report["python_environment"]["site_packages"].endswith("venv\\Lib\\site-packages")


def test_cleanup_report_is_manual_and_preserves_models(monkeypatch, tmp_path):
    monkeypatch.setenv("VIDEO_DIGEST_HOME", str(tmp_path / "runtime"))
    report = check_env.build_report("light", install=False)
    cleanup = report["cleanup"]
    assert cleanup["manual_only"] is True
    assert any(path.endswith("venv") for path in cleanup["paths_to_delete"])
    assert report["models"]["base_dir"] in cleanup["preserved_paths"]
    assert "Remove-Item" in cleanup["windows_command"]
    assert cleanup["macos_command"].startswith("rm -rf")


def test_install_commands_target_runtime_python(monkeypatch, tmp_path):
    paths = runtime_paths(tmp_path / "runtime", scope="global")
    paths.runtime_python.parent.mkdir(parents=True)
    paths.runtime_python.write_bytes(b"python")
    calls = []

    def fake_run(command, check):
        calls.append(command)

    monkeypatch.setattr(check_env.subprocess, "run", fake_run)
    check_env.run_pip_install_into_runtime(["yt-dlp"], paths)
    assert calls == [[str(paths.runtime_python), "-m", "pip", "install", "yt-dlp"]]
