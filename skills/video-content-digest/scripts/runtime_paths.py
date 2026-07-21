#!/usr/bin/env python3
"""解析工作区私有运行环境、模型与缓存路径。"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


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
    """将 Python 平台标识转换为跨平台文档使用的统一名称。"""
    value = platform or sys.platform
    if value.startswith("win"):
        return "windows"
    if value == "darwin":
        return "macos"
    return "linux"


def skill_root() -> Path:
    """返回只读安装目录，供脚本读取技能源码与参考资料。"""
    return Path(__file__).resolve().parents[1]


def workspace_root() -> Path:
    """返回调用技能的项目工作区，而非技能安装目录。"""
    return Path.cwd().resolve()


def runtime_home() -> Path:
    """返回可覆盖的工作区私有运行目录，避免写入安装目录。"""
    configured = os.environ.get("VIDEO_SUMMARY_RADAR_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return workspace_root() / ".video-summary-radar" / "runtime"


def runtime_paths() -> RuntimePaths:
    """构造当前工作区的 Python 运行时、模型与缓存路径集合。"""
    root = runtime_home()
    if platform_key() == "windows":
        runtime_python = root / "venv" / "Scripts" / "python.exe"
        runtime_pip = root / "venv" / "Scripts" / "pip.exe"
    else:
        runtime_python = root / "venv" / "bin" / "python"
        runtime_pip = root / "venv" / "bin" / "pip"
    return RuntimePaths(
        scope="workspace",
        home=root,
        project_root=workspace_root(),
        venv=root / "venv",
        runtime_python=runtime_python,
        runtime_pip=runtime_pip,
        models=root / "models",
        cache=root / "cache",
        config=root / "config",
        manifest=root / "manifest.json",
    )


def model_paths(paths: RuntimePaths | None = None) -> dict[str, Path]:
    active = paths or runtime_paths()
    return {
        "asr": active.models / "SenseVoiceSmall",
        "vad": active.models / "FSMN-VAD",
        "punc": active.models / "PUNC",
    }
