#!/usr/bin/env python3
"""Resolve runtime and model paths relative to this skill directory."""

from __future__ import annotations

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
    value = platform or sys.platform
    if value.startswith("win"):
        return "windows"
    if value == "darwin":
        return "macos"
    return "linux"


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def runtime_paths() -> RuntimePaths:
    root = skill_root() / "lib"
    if platform_key() == "windows":
        runtime_python = root / "venv" / "Scripts" / "python.exe"
        runtime_pip = root / "venv" / "Scripts" / "pip.exe"
    else:
        runtime_python = root / "venv" / "bin" / "python"
        runtime_pip = root / "venv" / "bin" / "pip"
    return RuntimePaths(
        scope="skill-local",
        home=root,
        project_root=None,
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
