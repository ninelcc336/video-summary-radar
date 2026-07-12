#!/usr/bin/env python3
"""Check and optionally install dependencies for video-content-digest."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import site
import subprocess
import sys
import sysconfig
from dataclasses import dataclass


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
        "windows": "winget install Gyan.FFmpeg",
        "macos": "brew install ffmpeg",
        "linux": "Install ffmpeg with your distribution package manager, e.g. sudo apt install ffmpeg",
    },
    "yt-dlp": {
        "windows": "python -m pip install yt-dlp",
        "macos": "python -m pip install yt-dlp",
        "linux": "python -m pip install yt-dlp",
    },
}


@dataclass
class PackageStatus:
    package: str
    module: str
    installed: bool
    location: str | None


def detect_platform_key() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


def python_install_location() -> dict:
    purelib = sysconfig.get_paths().get("purelib")
    scripts = sysconfig.get_paths().get("scripts")
    return {
        "python": sys.executable,
        "pip_command": f"{sys.executable} -m pip",
        "site_packages": purelib,
        "scripts": scripts,
        "user_site": site.getusersitepackages(),
    }


def package_status(package: str, module: str) -> PackageStatus:
    spec = importlib.util.find_spec(module)
    location = None
    if spec is not None:
        location = spec.origin or (spec.submodule_search_locations[0] if spec.submodule_search_locations else None)
    return PackageStatus(package=package, module=module, installed=spec is not None, location=location)


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


def run_pip_install(packages: list[str]) -> None:
    if not packages:
        return
    command = [sys.executable, "-m", "pip", "install", *packages]
    subprocess.run(command, check=True)


def render_text(report: dict) -> str:
    lines: list[str] = []
    lines.append("Video Content Digest environment check")
    lines.append("")
    lines.append(f"Mode: {report['mode']}")
    lines.append(f"Python: {report['python_environment']['python']}")
    lines.append(f"pip: {report['python_environment']['pip_command']}")
    lines.append(f"site-packages: {report['python_environment']['site_packages']}")
    lines.append(f"scripts: {report['python_environment']['scripts']}")
    lines.append("")

    lines.append("System tools:")
    for item in report["system_tools"]:
        state = "ok" if item["installed"] else "missing"
        suffix = f" ({item['path']})" if item["path"] else ""
        lines.append(f"- {item['command']}: {state}{suffix}")
        if not item["installed"]:
            lines.append(f"  install suggestion: {item['install_suggestion']}")
    lines.append("")

    lines.append("Python packages:")
    for item in report["python_packages"]:
        state = "ok" if item["installed"] else "missing"
        suffix = f" ({item['location']})" if item["location"] else ""
        lines.append(f"- {item['package']}: {state}{suffix}")
    lines.append("")

    if report["installed_packages"]:
        lines.append("Installed in this run:")
        for package in report["installed_packages"]:
            lines.append(f"- {package}")
        lines.append("")

    lines.append("Install location:")
    lines.append(f"- Python packages are installed into: {report['python_environment']['site_packages']}")
    lines.append(f"- Console scripts are installed into: {report['python_environment']['scripts']}")
    lines.append("")

    lines.append("Uninstall commands:")
    for package in report["uninstall_packages"]:
        lines.append(f"- {report['python_environment']['pip_command']} uninstall {package}")
    lines.append("")

    if report["missing_python_packages"] and not report["install_requested"]:
        joined = " ".join(report["missing_python_packages"])
        lines.append("To install missing Python packages:")
        lines.append(f"- {report['python_environment']['pip_command']} install {joined}")
        lines.append("")

    lines.append("Notes:")
    lines.append("- This script only auto-installs Python packages when --install is provided.")
    lines.append("- ffmpeg is a system dependency; install it manually using the suggestion above if missing.")
    if report["mode"] == "chinese":
        lines.append("- FunASR model files are not downloaded by this script; prepare local model directories separately.")
    return "\n".join(lines)


def build_report(mode: str, install: bool) -> dict:
    mode = normalize_mode(mode)
    packages = selected_packages(mode)
    before = [package_status(package, module) for package, module in packages.items()]
    missing_before = [item.package for item in before if not item.installed]

    installed_packages: list[str] = []
    if install and missing_before:
        run_pip_install(missing_before)
        installed_packages = missing_before

    after = [package_status(package, module) for package, module in packages.items()]
    missing_after = [item.package for item in after if not item.installed]

    platform_key = detect_platform_key()
    tools = []
    for command, suggestions in SYSTEM_TOOLS.items():
        status = command_status(command)
        status["install_suggestion"] = suggestions[platform_key]
        tools.append(status)

    return {
        "mode": mode,
        "install_requested": install,
        "python_environment": python_install_location(),
        "system_tools": tools,
        "python_packages": [item.__dict__ for item in after],
        "missing_python_packages": missing_after,
        "installed_packages": installed_packages,
        "uninstall_packages": list(packages.keys()),
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

    return 1 if report["missing_python_packages"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
