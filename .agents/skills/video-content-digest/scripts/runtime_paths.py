#!/usr/bin/env python3
"""Resolve the user-managed runtime paths for video-content-digest."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


APP_DIR_NAME = "VideoSummaryRadar"
SKILL_DIR_NAME = "video-content-digest"
PROJECT_RUNTIME_DIR_NAME = ".video-content-digest"
HOME_ENV_VAR = "VIDEO_DIGEST_HOME"
SCOPE_ENV_VAR = "VIDEO_DIGEST_SCOPE"


@dataclass(frozen=True)
class RuntimePaths:
    scope: str
    home: Path
    project_root: Path | None
    venv: Path
    runtime_python: Path
    runtime_pip: Path
    models: Path
    cache: Path
    config: Path
    manifest: Path


def platform_key(platform: str | None = None) -> str:
    value = platform or sys.platform
    if value.startswith("win"):
        return "windows"
    if value == "darwin":
        return "macos"
    return "linux"


def default_home(platform: str | None = None, environ: dict[str, str] | None = None) -> Path:
    env = os.environ if environ is None else environ
    override = env.get(HOME_ENV_VAR)
    if override:
        return Path(override).expanduser().resolve()

    current_platform = platform_key(platform)
    if current_platform == "windows":
        base = env.get("LOCALAPPDATA") or env.get("APPDATA") or str(Path.home())
        return (Path(base) / APP_DIR_NAME / SKILL_DIR_NAME).resolve()
    if current_platform == "macos":
        return (Path.home() / "Library" / "Application Support" / APP_DIR_NAME / SKILL_DIR_NAME).resolve()

    base = env.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share")
    return (Path(base) / APP_DIR_NAME / SKILL_DIR_NAME).resolve()


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def find_project_root(start: Path | None = None) -> Path | None:
    current = (start or skill_root()).expanduser().resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def detect_scope(
    scope: str | None = None,
    skill_path: Path | None = None,
    environ: dict[str, str] | None = None,
) -> tuple[str, Path | None]:
    env = os.environ if environ is None else environ
    selected = (scope or env.get(SCOPE_ENV_VAR) or "auto").strip().lower()
    if selected not in {"auto", "global", "project"}:
        raise ValueError(f"Unsupported {SCOPE_ENV_VAR}: {selected}. Use auto, global, or project.")
    project_root = find_project_root(skill_path or skill_root())
    if selected == "global":
        return "global", None
    if selected == "project":
        if project_root is None:
            raise RuntimeError("无法定位项目根目录，请设置 VIDEO_DIGEST_HOME 或 VIDEO_DIGEST_SCOPE=global。")
        return "project", project_root
    if project_root is not None:
        return "project", project_root
    return "global", None


def runtime_paths(
    home: Path | str | None = None,
    scope: str | None = None,
    skill_path: Path | None = None,
) -> RuntimePaths:
    selected_scope, project_root = detect_scope(scope, skill_path)
    override = os.environ.get(HOME_ENV_VAR)
    if home is not None:
        root = Path(home).expanduser().resolve()
    elif override:
        root = Path(override).expanduser().resolve()
    elif selected_scope == "project":
        root = (project_root / PROJECT_RUNTIME_DIR_NAME).resolve()
    else:
        root = default_home()
    if platform_key() == "windows":
        runtime_python = root / "venv" / "Scripts" / "python.exe"
        runtime_pip = root / "venv" / "Scripts" / "pip.exe"
    else:
        runtime_python = root / "venv" / "bin" / "python"
        runtime_pip = root / "venv" / "bin" / "pip"
    return RuntimePaths(
        scope=selected_scope,
        home=root,
        project_root=project_root,
        venv=root / "venv",
        runtime_python=runtime_python,
        runtime_pip=runtime_pip,
        models=root / "models",
        cache=root / "cache",
        config=root / "config",
        manifest=root / "manifest.json",
    )
