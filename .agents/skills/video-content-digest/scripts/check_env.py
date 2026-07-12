#!/usr/bin/env python3
"""Check and optionally install dependencies for video-content-digest."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shlex
import shutil
import subprocess
import sys
import sysconfig
from dataclasses import dataclass
from pathlib import Path

from runtime_paths import RuntimePaths, platform_key, runtime_paths


PYTHON_PACKAGES = {
    "light": {
        "yt-dlp": "yt_dlp",
        "faster-whisper": "faster_whisper",
    },
    "chinese": {
        "yt-dlp": "yt_dlp",
        "funasr": "funasr",
        "torch": "torch",
        "torchaudio": "torchaudio",
    },
}

MODE_ALIASES = {
    "api": "light",
    "local": "chinese",
}

SYSTEM_TOOLS = {
    "ffmpeg": {
        "purpose": "提取视频音频",
        "windows": {
            "install": "winget install Gyan.FFmpeg",
            "uninstall": "winget uninstall Gyan.FFmpeg",
            "locate": "where.exe ffmpeg",
        },
        "macos": {
            "install": "brew install ffmpeg",
            "uninstall": "brew uninstall ffmpeg",
            "locate": "which ffmpeg && brew --prefix ffmpeg",
        },
        "linux": "Install ffmpeg with your distribution package manager, e.g. sudo apt install ffmpeg",
    },
}

MIN_PYTHON = (3, 10)
WINDOWS_TORCH_CPU_INDEX = "https://download.pytorch.org/whl/cpu"
WINDOWS_TORCH_PACKAGES = ("torch==2.11.0+cpu", "torchaudio==2.11.0+cpu")


@dataclass
class PackageStatus:
    package: str
    module: str
    installed: bool
    location: str | None
    version: str | None = None


def detect_platform_key() -> str:
    return platform_key()


def python_prerequisite() -> dict:
    version = tuple(sys.version_info[:2])
    return {
        "installed": version >= MIN_PYTHON,
        "version": ".".join(str(item) for item in version),
        "required": ".".join(str(item) for item in MIN_PYTHON) + "+",
        "python": sys.executable,
    }


def _python_probe(executable: Path | str) -> dict:
    code = (
        "import importlib.metadata as m, importlib.util as u, json, sys, sysconfig; "
        "print(json.dumps({'version': '.'.join(map(str, sys.version_info[:3])), "
        "'site_packages': sysconfig.get_paths().get('purelib'), "
        "'scripts': sysconfig.get_paths().get('scripts')}, ensure_ascii=False))"
    )
    result = subprocess.run(
        [str(executable), "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {"version": None, "site_packages": None, "scripts": None}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"version": None, "site_packages": None, "scripts": None}


def python_install_location(paths: RuntimePaths) -> dict:
    executable = paths.runtime_python if paths.runtime_python.exists() else None
    probe = _python_probe(executable) if executable else {"version": None, "site_packages": None, "scripts": None}
    if not executable:
        probe["site_packages"] = (
            str(paths.venv / "Lib" / "site-packages")
            if detect_platform_key() == "windows"
            else str(paths.venv / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages")
        )
        probe["scripts"] = str(paths.venv / "Scripts") if detect_platform_key() == "windows" else str(paths.venv / "bin")
    return {
        "bootstrap_python": sys.executable,
        "runtime_python": str(paths.runtime_python),
        "pip_command": f"{paths.runtime_python} -m pip",
        "site_packages": probe.get("site_packages"),
        "scripts": probe.get("scripts"),
        "runtime_exists": paths.runtime_python.exists(),
        "scope": paths.scope,
        "project_root": str(paths.project_root) if paths.project_root else None,
        "home": str(paths.home),
        "venv": str(paths.venv),
    }


def package_status(package: str, module: str, executable: Path | str | None = None) -> PackageStatus:
    python = Path(executable) if executable else Path(sys.executable)
    if python.resolve() == Path(sys.executable).resolve():
        spec = importlib.util.find_spec(module)
        location = None
        if spec is not None:
            location = spec.origin or (spec.submodule_search_locations[0] if spec.submodule_search_locations else None)
        try:
            from importlib.metadata import version

            package_version = version(package) if spec is not None else None
        except Exception:
            package_version = None
        return PackageStatus(package, module, spec is not None, location, package_version)

    code = (
        "import importlib.metadata as m, importlib.util as u, json, sys; "
        f"module = {module!r}; package = {package!r}; spec = u.find_spec(module); "
        "location = (spec.origin or (next(iter(spec.submodule_search_locations), None) "
        "if spec and spec.submodule_search_locations else None)) if spec else None; "
        "version = None; "
        "\ntry: version = m.version(package)\nexcept Exception: pass; "
        "print(json.dumps({'installed': spec is not None, 'location': location, 'version': version}))"
    )
    if not python.exists():
        return PackageStatus(package, module, False, None, None)
    result = subprocess.run([str(python), "-c", code], check=False, capture_output=True, text=True)
    if result.returncode != 0:
        return PackageStatus(package, module, False, None, None)
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        data = {"installed": False, "location": None, "version": None}
    return PackageStatus(package, module, bool(data["installed"]), data.get("location"), data.get("version"))


def command_status(command: str) -> dict:
    path = shutil.which(command)
    return {
        "command": command,
        "installed": path is not None,
        "path": path,
    }


def selected_packages(mode: str) -> dict[str, str]:
    mode = MODE_ALIASES.get(mode, mode)
    if mode == "all":
        packages: dict[str, str] = {}
        for group in PYTHON_PACKAGES.values():
            packages.update(group)
        return packages
    return PYTHON_PACKAGES[mode]


def normalize_mode(mode: str) -> str:
    return MODE_ALIASES.get(mode, mode)


def ensure_runtime(paths: RuntimePaths) -> None:
    if not python_prerequisite()["installed"]:
        raise RuntimeError("需要 Python 3.10 或更高版本，当前引导 Python 不满足要求。")
    paths.home.mkdir(parents=True, exist_ok=True)
    if not paths.runtime_python.exists():
        subprocess.run([sys.executable, "-m", "venv", str(paths.venv)], check=True)
    for directory in (paths.models, paths.cache, paths.config):
        directory.mkdir(parents=True, exist_ok=True)


def run_pip_install_into_runtime(packages: list[str], paths: RuntimePaths) -> None:
    if not packages:
        return
    platform = detect_platform_key()
    regular = list(packages)
    torch_packages = [package for package in regular if package in {"torch", "torchaudio"}]
    if platform == "windows" and torch_packages:
        regular = [package for package in regular if package not in {"torch", "torchaudio"}]
        requested_torch = [package for package in WINDOWS_TORCH_PACKAGES if package.split("==", 1)[0] in torch_packages]
        subprocess.run(
            [str(paths.runtime_python), "-m", "pip", "install", *requested_torch, "--index-url", WINDOWS_TORCH_CPU_INDEX],
            check=True,
        )
    if regular:
        subprocess.run([str(paths.runtime_python), "-m", "pip", "install", *regular], check=True)


def model_report(mode: str, paths: RuntimePaths) -> dict:
    required = mode in {"chinese", "all"}
    asr = paths.models / "SenseVoiceSmall"
    vad = paths.models / "FSMN-VAD"
    return {
        "base_dir": str(paths.models),
        "asr": {"path": str(asr), "required": required, "exists": asr.is_dir()},
        "vad": {"path": str(vad), "required": False, "exists": vad.is_dir()},
        "punc": {"path": str(paths.models / "PUNC"), "required": False, "exists": (paths.models / "PUNC").is_dir()},
        "note": "FunASR 模型不会由此脚本自动下载。" if required else None,
    }


def write_manifest(paths: RuntimePaths, mode: str, packages: list[str]) -> None:
    manifest = {
        "app": "VideoSummaryRadar",
        "skill": "video-content-digest",
        "mode": mode,
        "managed_paths": [str(path) for path in (paths.venv, paths.cache, paths.config, paths.manifest)],
        "models_path": str(paths.models),
        "packages": packages,
        "platform": detect_platform_key(),
        "scope": paths.scope,
        "project_root": str(paths.project_root) if paths.project_root else None,
        "bootstrap_python": sys.executable,
    }
    paths.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def tool_commands(command: str, platform: str) -> dict:
    info = SYSTEM_TOOLS[command]
    if platform in {"windows", "macos"}:
        return info[platform]
    return {"install": str(info["linux"]), "uninstall": "请使用当前 Linux 发行版的包管理器卸载 ffmpeg。", "locate": "command -v ffmpeg"}


def _powershell_quote(value: Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def manual_cleanup_report(paths: RuntimePaths) -> dict:
    removable = [paths.venv, paths.cache, paths.config, paths.manifest]
    windows_command = (
        "Remove-Item -LiteralPath "
        + ",".join(_powershell_quote(path) for path in removable)
        + " -Recurse -Force -ErrorAction SilentlyContinue"
    )
    macos_command = "rm -rf -- " + " ".join(shlex.quote(str(path)) for path in removable)
    return {
        "manual_only": True,
        "paths_to_delete": [str(path) for path in removable],
        "preserved_paths": [str(paths.models), "<project-root>/outputs/"],
        "windows_command": windows_command,
        "macos_command": macos_command,
        "note": "Agent 不会自动删除这些路径；用户需要自行确认并执行。",
    }


def render_text(report: dict) -> str:
    lines: list[str] = []
    lines.append("Video Content Digest environment check")
    lines.append("")
    lines.append(f"Mode: {report['mode']}")
    lines.append(f"Bootstrap Python: {report['python_environment']['bootstrap_python']}")
    lines.append(f"Runtime Python: {report['python_environment']['runtime_python']}")
    lines.append(f"pip: {report['python_environment']['pip_command']}")
    lines.append(f"site-packages: {report['python_environment']['site_packages']}")
    lines.append(f"scripts: {report['python_environment']['scripts']}")
    lines.append(f"Runtime home: {report['python_environment']['home']}")
    lines.append(f"Scope: {report['python_environment']['scope']}")
    if report["python_environment"]["project_root"]:
        lines.append(f"Project root: {report['python_environment']['project_root']}")
    lines.append(f"Python prerequisite: {'ok' if report['python_prerequisite']['installed'] else 'missing'} ({report['python_prerequisite']['required']})")
    lines.append("")

    lines.append("System tools:")
    for item in report["system_tools"]:
        state = "ok" if item["installed"] else "missing"
        suffix = f" ({item['path']})" if item["path"] else ""
        lines.append(f"- {item['command']}: {state}{suffix}")
        if not item["installed"]:
            lines.append(f"  purpose: {item['purpose']}")
            lines.append(f"  install: {item['install_commands']['install']}")
            lines.append(f"  uninstall: {item['install_commands']['uninstall']}")
            lines.append(f"  locate: {item['install_commands']['locate']}")
    lines.append("")

    lines.append("Python packages:")
    for item in report["python_packages"]:
        state = "ok" if item["installed"] else "missing"
        suffix = f" ({item['location']})" if item["location"] else ""
        version = f" v{item['version']}" if item.get("version") else ""
        lines.append(f"- {item['package']}: {state}{version}{suffix}")
    lines.append("")

    if report["installed_packages"]:
        lines.append("Installed in this run:")
        for package in report["installed_packages"]:
            lines.append(f"- {package}")
        lines.append("")

    lines.append("Install location:")
    lines.append(f"- Python packages: {report['python_environment']['site_packages']}")
    lines.append(f"- Console scripts: {report['python_environment']['scripts']}")
    lines.append(f"- Models: {report['models']['base_dir']}")
    lines.append(f"- Cache: {report['cache']}")
    lines.append("")

    lines.append("Manual dependency cleanup (no automatic deletion):")
    for path in report["cleanup"]["paths_to_delete"]:
        lines.append(f"- Delete manually: {path}")
    lines.append(f"- Preserve models: {report['models']['base_dir']}")
    lines.append("- Preserve project outputs: <project-root>/outputs/")
    lines.append(f"- Windows PowerShell: {report['cleanup']['windows_command']}")
    lines.append(f"- macOS shell: {report['cleanup']['macos_command']}")
    lines.append("")

    if report["missing_python_packages"] and not report["install_requested"]:
        lines.append("After explicit user confirmation, install missing Python packages with:")
        lines.append(f"- {sys.executable} scripts/check_env.py --mode {report['mode']} --install")
        lines.append("")

    lines.append("Models:")
    asr = report["models"]["asr"]
    asr_state = "ok" if asr["exists"] else ("required/missing" if asr["required"] else "not required")
    lines.append(f"- ASR: {asr['path']} ({asr_state})")
    lines.append(f"- VAD: {report['models']['vad']['path']} ({'ok' if report['models']['vad']['exists'] else 'optional/missing'})")

    lines.append("Notes:")
    lines.append("- This script only installs Python packages into the user-managed venv when --install is provided.")
    lines.append("- ffmpeg is a system dependency; this script never installs or uninstalls it.")
    if report["mode"] == "chinese":
        lines.append("- FunASR model files are not downloaded by this script; prepare local model directories separately.")
    return "\n".join(lines)


def build_report(mode: str, install: bool) -> dict:
    mode = normalize_mode(mode)
    packages = selected_packages(mode)
    paths = runtime_paths()
    before = [package_status(package, module, paths.runtime_python) for package, module in packages.items()]
    missing_before = [item.package for item in before if not item.installed]

    installed_packages: list[str] = []
    if install and (missing_before or not paths.manifest.exists()):
        ensure_runtime(paths)
        if missing_before:
            run_pip_install_into_runtime(missing_before, paths)
            installed_packages = missing_before
        write_manifest(paths, mode, list(packages.keys()))

    after = [package_status(package, module, paths.runtime_python) for package, module in packages.items()]
    missing_after = [item.package for item in after if not item.installed]

    platform_key = detect_platform_key()
    tools = []
    for command, suggestions in SYSTEM_TOOLS.items():
        status = command_status(command)
        status["purpose"] = suggestions["purpose"]
        status["install_commands"] = tool_commands(command, platform_key)
        tools.append(status)

    return {
        "mode": mode,
        "install_requested": install,
        "python_prerequisite": python_prerequisite(),
        "python_environment": python_install_location(paths),
        "system_tools": tools,
        "python_packages": [item.__dict__ for item in after],
        "missing_python_packages": missing_after,
        "installed_packages": installed_packages,
        "models": model_report(mode, paths),
        "cache": str(paths.cache),
        "cleanup": manual_cleanup_report(paths),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["light", "chinese", "all", "api", "local"],
        default="light",
        help="Dependency set to check; api/local are backward-compatible aliases",
    )
    parser.add_argument("--install", action="store_true", help="Install missing Python packages with pip")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    report = build_report(args.mode, args.install)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_text(report))

    model_missing = report["mode"] in {"chinese", "all"} and not report["models"]["asr"]["exists"]
    return 1 if report["missing_python_packages"] or not report["python_prerequisite"]["installed"] or model_missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
