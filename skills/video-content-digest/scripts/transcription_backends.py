#!/usr/bin/env python3
"""FunASR Chinese transcription backend for local video audio."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from runtime_paths import model_paths


SUPPORTED_BACKENDS = {"chinese"}


def format_time(seconds: float | int | None) -> str:
    total = max(0, int(float(seconds or 0)))
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _format_timestamp(value: Any, milliseconds: bool = False) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, str) and ":" in value:
        return value.split(".", 1)[0]
    number = float(value)
    return format_time(number / 1000 if milliseconds else number)


def normalize_segment(raw: dict[str, Any], backend: str, language: str | None) -> dict:
    timestamp = raw.get("timestamp") or raw.get("timestamps")
    start = raw.get("start")
    end = raw.get("end")
    if timestamp and isinstance(timestamp, (list, tuple)) and len(timestamp) >= 2:
        if isinstance(timestamp[0], (list, tuple)):
            start, end = timestamp[0][0], timestamp[-1][1]
        else:
            start, end = timestamp[0], timestamp[1]

    numeric_times = [value for value in (start, end) if isinstance(value, (int, float))]
    milliseconds = bool(numeric_times and max(numeric_times) >= 1000)

    text = str(raw.get("text") or raw.get("sentence") or "").strip()
    text = re.sub(r"<\|[^|]+\|>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return {
        "start": _format_timestamp(start, milliseconds),
        "end": _format_timestamp(end, milliseconds),
        "text": text,
        "language": raw.get("language") or language,
        "backend": backend,
    }


def _require_model_path(name: str, value: str | None, required: bool = False) -> str | None:
    if not value:
        if required:
            raise RuntimeError("chinese 后端需要本地 FunASR ASR 模型目录。")
        return None
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"FunASR 模型路径不存在：{path}")
    return str(path)


def _transcribe_funasr(
    audio_path: Path,
    asr_model: str | None,
    vad_model: str | None,
    punc_model: str | None,
    language: str | None,
) -> list[dict]:
    asr_path = _require_model_path("asr", asr_model, required=True)
    vad_path = _require_model_path("vad", vad_model)
    punc_path = _require_model_path("punc", punc_model)

    try:
        from funasr import AutoModel
        import torch
    except ImportError as exc:
        raise RuntimeError("缺少 FunASR 或 PyTorch。请先运行 scripts/check_env.py --mode chinese --install。") from exc

    device = "cuda" if torch.cuda.is_available() else "cpu"
    kwargs = {"model": asr_path, "device": device, "disable_update": True}
    if vad_path:
        kwargs["vad_model"] = vad_path
    if punc_path:
        kwargs["punc_model"] = punc_path

    model = AutoModel(**kwargs)
    generated = model.generate(input=str(audio_path), batch_size_s=300)
    if isinstance(generated, dict):
        generated = [generated]

    results = []
    for item in generated or []:
        if not isinstance(item, dict):
            continue
        sentence_info = item.get("sentence_info")
        if isinstance(sentence_info, list) and sentence_info:
            results.extend(normalize_segment(sentence, "chinese", language or "zh") for sentence in sentence_info)
        else:
            results.append(normalize_segment(item, "chinese", language or "zh"))
    return [item for item in results if item["text"]]


def transcribe_audio(
    audio_path: Path,
    backend: str,
    language: str | None,
    asr_model: str | None,
    vad_model: str | None,
    punc_model: str | None,
) -> list[dict]:
    if backend not in SUPPORTED_BACKENDS:
        raise ValueError(f"Unsupported backend: {backend}. Supported backends: chinese")
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file does not exist: {audio_path}")

    defaults = model_paths()
    asr_model = asr_model or str(defaults["asr"])
    vad_model = vad_model or (str(defaults["vad"]) if defaults["vad"].exists() else None)
    punc_model = punc_model or (str(defaults["punc"]) if defaults["punc"].exists() else None)
    return _transcribe_funasr(audio_path, asr_model, vad_model, punc_model, language)
