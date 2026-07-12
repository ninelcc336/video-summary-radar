# 视频转录后端两档配置 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `video-content-digest` 增加 `light` 与 `chinese` 两档转录后端，默认使用中文方案，同时保持现有 `faster-whisper` 流程兼容。

**Architecture:** 将后端实现集中在 `scripts/transcription_backends.py`，由 `transcribe.py` 负责命令行参数和统一 JSON/Markdown 输出。`light` 调用现有 faster-whisper，`chinese` 通过 FunASR 的本地模型路径调用 VAD、ASR 和可选标点恢复；未准备 FunASR 模型时明确报错，不自动下载。

**Tech Stack:** Python 3.10+、faster-whisper、FunASR、ffmpeg、pytest（测试环境可选）。

## Global Constraints

- 只保留 `light` 和 `chinese` 两档后端。
- 未指定后端时默认使用 `chinese`。
- 不自动下载 FunASR 模型；必须由用户提供本地模型目录或显式模型配置。
- 两个后端都输出 `start`、`end`、`text`、`language`、`backend` 字段。
- 旧的 `--model`、`--language` 和输出格式参数保持可用。
- 不修改内容包模板和平台解析逻辑之外的无关功能。

---

### Task 1: 抽取统一转录后端接口

**Files:**
- Create: `E:/ai-list/Video Summary Radar/.agents/skills/video-content-digest/scripts/transcription_backends.py`
- Modify: `E:/ai-list/Video Summary Radar/.agents/skills/video-content-digest/scripts/transcribe.py`
- Test: `E:/ai-list/Video Summary Radar/.agents/skills/video-content-digest/tests/test_transcription_backends.py`

**Interfaces:**
- `transcription_backends.transcribe_audio(audio_path: Path, backend: str, model_name: str, language: str | None, asr_model: str | None, vad_model: str | None, punc_model: str | None) -> list[dict]`
- 每个结果字典至少包含 `start: str`、`end: str`、`text: str`、`language: str | None`、`backend: str`。

- [ ] **Step 1: Write the failing tests**

测试 fake backend 输出会被规范化为统一字段，并测试非法 backend 返回 `ValueError`。

```python
def test_normalize_segment_adds_backend_and_language():
    result = normalize_segment({"timestamp": [1000, 2500], "text": "你好"}, "chinese", "zh")
    assert result == {
        "start": "00:00:01",
        "end": "00:00:02",
        "text": "你好",
        "language": "zh",
        "backend": "chinese",
    }


def test_unknown_backend_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="Unsupported backend"):
        transcribe_audio(tmp_path / "audio.wav", "quality", "small", None, None, None, None)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest .agents/skills/video-content-digest/tests/test_transcription_backends.py -q`

Expected: FAIL because the new module and normalization function do not exist.

- [ ] **Step 3: Implement the backend module**

实现以下内容：

1. `format_time(seconds)` 将秒数格式化为 `HH:MM:SS`。
2. `normalize_segment(raw, backend, language)` 同时支持秒数 timestamp、毫秒 timestamp 和已经存在的 `start/end`。
3. `_transcribe_faster_whisper(...)` 复用现有 `WhisperModel` 配置，并在结果中写入 `backend="light"`。
4. `_transcribe_funasr(...)` 在缺少 `funasr` 时抛出带安装命令的 `RuntimeError`；要求 `asr_model` 为本地路径或已准备好的模型目录，不提供时抛出明确错误；通过 `AutoModel(model=asr_model, vad_model=vad_model, punc_model=punc_model, device="auto")` 推理；将 FunASR 的 `timestamp`、`text`、`sentence_info` 等常见字段适配为统一结构。
5. `transcribe_audio(...)` 只接受 `light` 和 `chinese`，并按后端分派。

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest .agents/skills/video-content-digest/tests/test_transcription_backends.py -q`

Expected: PASS。

- [ ] **Step 5: Update the CLI without breaking old arguments**

在 `transcribe.py` 中新增：

```text
--backend {light,chinese}  默认 chinese
--asr-model PATH           FunASR ASR 本地模型目录
--vad-model PATH           可选 FSMN-VAD 本地模型目录
--punc-model PATH          可选标点模型目录
```

保留 `--model` 作为 `light` 的 faster-whisper 模型参数，保留 `--language`、`--output` 和 `--format`。Markdown 输出继续使用时间范围和文本；JSON 输出保留统一字段。

### Task 2: 按后端更新依赖检查

**Files:**
- Modify: `E:/ai-list/Video Summary Radar/.agents/skills/video-content-digest/scripts/check_env.py`
- Test: `E:/ai-list/Video Summary Radar/.agents/skills/video-content-digest/tests/test_check_env.py`

**Interfaces:**
- `check_env.py --mode light` 检查 `faster-whisper` 与 `ffmpeg`。
- `check_env.py --mode chinese` 检查 `funasr` 与 `ffmpeg`，并提示用户自行准备模型。
- `check_env.py --mode all` 检查两个后端。
- 兼容旧的 `--mode api` 和 `--mode local`，分别映射到 `light` 和 `chinese`，避免已有命令失效。

- [ ] **Step 1: Write the failing tests**

测试 `selected_packages("light")` 只返回 faster-whisper，`selected_packages("chinese")` 返回 funasr，并测试旧别名映射。

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest .agents/skills/video-content-digest/tests/test_check_env.py -q`

Expected: FAIL because current modes are `api` 和 `local`。

- [ ] **Step 3: Implement backend-aware dependency groups**

增加 `funasr: funasr` 依赖映射，增加 `normalize_mode()`，将 `api -> light`、`local -> chinese`，并在文本输出中说明 FunASR 模型不由脚本自动下载。

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest .agents/skills/video-content-digest/tests/test_check_env.py -q`

Expected: PASS。

### Task 3: 更新 skill 使用说明和安装文档

**Files:**
- Modify: `E:/ai-list/Video Summary Radar/.agents/skills/video-content-digest/SKILL.md`
- Modify: `E:/ai-list/Video Summary Radar/.agents/skills/video-content-digest/references/platform-notes.md`
- Modify: `E:/ai-list/Video Summary Radar/.agents/skills/video-content-digest/references/quality-checklist.md`

**Interfaces:**
- 文档中的命令必须与 Task 1 和 Task 2 的参数一致。

- [ ] **Step 1: Replace the single-backend workflow**

在工作流中说明默认 `chinese`，并列出 `light` 的低占用场景。明确 FunASR 需要用户提前准备本地模型，不自动下载。

- [ ] **Step 2: Add copy-paste commands**

加入以下可执行示例：

```bash
python scripts/check_env.py --mode light
python scripts/check_env.py --mode chinese
python scripts/transcribe.py audio.wav --backend light --model base --output outputs/transcript.json --format json
python scripts/transcribe.py audio.wav --backend chinese --asr-model path/to/asr --vad-model path/to/fsmn-vad --punc-model path/to/punc --output outputs/transcript.json --format json
```

- [ ] **Step 3: Add storage and quality notes**

记录实际后端、模型来源、语言和转录限制；补充轻量方案通常更省空间，但中文专有名词和复杂音频可能需要 FunASR 的提示。

### Task 4: 集成验证

**Files:**
- Test: `E:/ai-list/Video Summary Radar/.agents/skills/video-content-digest/tests/test_cli_smoke.py`

**Interfaces:**
- 使用不存在的 FunASR 模型路径时，CLI 必须返回非零退出码并显示模型准备提示。
- 使用非法 backend 时，CLI 必须返回非零退出码并显示支持的后端列表。

- [ ] **Step 1: Add CLI smoke tests**

使用 `subprocess.run` 调用 `transcribe.py --help`、非法 backend 和缺少模型路径的 `chinese` 命令，不下载模型、不访问网络。

- [ ] **Step 2: Run the complete test suite**

Run: `python -m pytest .agents/skills/video-content-digest/tests -q`

Expected: 全部 PASS。

- [ ] **Step 3: Run syntax and help checks**

Run: `python -m compileall .agents/skills/video-content-digest/scripts`

Expected: 所有 Python 文件编译成功。

Run: `python .agents/skills/video-content-digest/scripts/transcribe.py --help`

Expected: 帮助中出现 `light`、`chinese`、`--asr-model`、`--vad-model` 和 `--punc-model`。
