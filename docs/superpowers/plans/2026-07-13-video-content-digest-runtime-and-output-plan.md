# Video Content Digest Runtime and Output Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `video-content-digest` 的依赖和模型固定到当前 skill 的 `lib/`，移除所有非中文转录模式，并升级内容包结构。

**Architecture:** 运行时路径由 `scripts/runtime_paths.py` 直接解析为 `skill_root()/lib`，不再使用项目 scope 或外部 home 覆盖。转录链路只保留 FunASR 中文后端，并默认从 `lib/models/` 读取模型。内容包模板、质量清单和平台说明统一使用 UTF-8 中文，并新增五维内容拆解章节。

**Tech Stack:** Python 3.10+、FunASR、PyTorch、yt-dlp、pytest、Markdown。

## Global Constraints

- 运行时唯一根目录是 `.agents/skills/video-content-digest/lib/`（全局安装时为对应 skill 根目录下的 `lib/`）。
- 不得保留或引用旧 `.video-content-digest/` 路径。
- 只支持 `chinese`，依赖固定为 `yt-dlp`、`funasr`、`torch`、`torchaudio`。
- Python 依赖只有在用户明确传入 `--install` 后才安装；`ffmpeg` 和 FunASR 模型不自动安装或下载。
- 输出默认使用中文，并将公众号、小红书章节分别命名为“公众号初稿”“小红书初稿”。
- 内容拆解必须包含“选题角度、开头钩子、内容结构、视频爆点、互动引导”。

---

### Task 1: 先固定新的运行时、依赖和 CLI 行为

**Files:**
- Modify: `.agents/skills/video-content-digest/tests/test_check_env.py`
- Modify: `.agents/skills/video-content-digest/tests/test_cli_smoke.py`
- Modify: `.agents/skills/video-content-digest/tests/test_transcription_backends.py`
- Test: the three files above

**Interfaces:**
- Tests will require `runtime_paths().home == skill_root() / "lib"`.
- Tests will require `check_env.selected_packages("chinese")` to return only the four Chinese-mode packages.
- Tests will require the help output to contain `chinese` and not contain `light`, `all`, `api`, or `local`.
- Tests will require `transcribe_audio` to reject any backend other than `chinese`.

- [ ] **Step 1: Replace obsolete dependency tests with failing assertions**

Update `test_check_env.py` so the old `light`, aliases, scope, and external-home tests are removed and the core assertions become:

```python
from runtime_paths import runtime_paths, skill_root


def test_only_chinese_dependencies_are_supported():
    assert check_env.selected_packages("chinese") == {
        "yt-dlp": "yt_dlp",
        "funasr": "funasr",
        "torch": "torch",
        "torchaudio": "torchaudio",
    }


def test_runtime_is_inside_the_skill_lib_directory():
    paths = runtime_paths()
    assert paths.home == skill_root() / "lib"
    assert paths.models == paths.home / "models"
    assert paths.cache == paths.home / "cache"


def test_default_dependency_mode_is_chinese():
    assert check_env.DEFAULT_MODE == "chinese"


def test_unsupported_modes_are_rejected():
    with pytest.raises(ValueError):
        check_env.selected_packages("light")
```

Add `import pytest` if it is not already present. Replace the old environment override, scope, and global/macOS home tests because those interfaces are intentionally removed.

- [ ] **Step 2: Replace CLI smoke assertions**

Change `test_help_lists_backends` to:

```python
def test_help_lists_only_chinese_backend():
    result = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "chinese" in result.stdout
    for obsolete in ("light", "all", "api", "local", "faster-whisper"):
        assert obsolete not in result.stdout
    assert "--asr-model" in result.stdout
```

- [ ] **Step 3: Replace backend tests**

Remove the faster-whisper-specific test coverage and change the unsupported-backend test to call the simplified Chinese-only interface expected from Task 2:

```python
def test_non_chinese_backend_is_rejected(tmp_path):
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"fake")
    with pytest.raises(ValueError, match="chinese"):
        transcribe_audio(audio, "light", "small", None, None, None)
```

- [ ] **Step 4: Run the focused tests and confirm they fail for the old implementation**

Run:

```powershell
python -m pytest .agents/skills/video-content-digest/tests/test_check_env.py .agents/skills/video-content-digest/tests/test_cli_smoke.py .agents/skills/video-content-digest/tests/test_transcription_backends.py -q
```

Expected: failures for the old `.video-content-digest` path, obsolete modes, and faster-whisper CLI output.

### Task 2: Implement skill-local `lib/` runtime and Chinese-only dependency checks

**Files:**
- Modify: `.agents/skills/video-content-digest/scripts/runtime_paths.py`
- Modify: `.agents/skills/video-content-digest/scripts/check_env.py`
- Test: `.agents/skills/video-content-digest/tests/test_check_env.py`

**Interfaces:**
- `skill_root() -> Path` remains the source of the skill directory.
- `runtime_paths() -> RuntimePaths` returns `home == skill_root() / "lib"`.
- `selected_packages("chinese")` returns the four fixed packages.
- `check_env.py --mode` accepts only `chinese`.

- [ ] **Step 1: Make `runtime_paths.py` resolve only `skill_root()/lib`**

Remove `PROJECT_RUNTIME_DIR_NAME`, `HOME_ENV_VAR`, `SCOPE_ENV_VAR`, `default_home`, `find_project_root`, and `detect_scope`. Keep `platform_key` and the `RuntimePaths` fields needed by the checker. Implement the root as:

```python
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
```

Update all callers and tests to use the no-argument function.

- [ ] **Step 2: Reduce `check_env.py` to the Chinese dependency set**

Set the constants to:

```python
PYTHON_PACKAGES = {
    "chinese": {
        "yt-dlp": "yt_dlp",
        "funasr": "funasr",
        "torch": "torch",
        "torchaudio": "torchaudio",
    },
}
DEFAULT_MODE = "chinese"
```

Make `selected_packages` validate the key directly, remove `MODE_ALIASES` and `normalize_mode`, and change the parser to `choices=["chinese"]`. `build_report` should call `runtime_paths()` without arguments. Keep the existing explicit-install behavior, CPU PyTorch handling, model reporting, and manual cleanup reporting, but make all rendered paths derive from `paths.home`.

- [ ] **Step 3: Set default model directories under `lib/models`**

Add a helper in `runtime_paths.py`:

```python
def model_paths(paths: RuntimePaths | None = None) -> dict[str, Path]:
    active = paths or runtime_paths()
    return {
        "asr": active.models / "SenseVoiceSmall",
        "vad": active.models / "FSMN-VAD",
        "punc": active.models / "PUNC",
    }
```

Use this helper in `check_env.model_report` so the report and the transcription CLI share the same model locations.

- [ ] **Step 4: Run the focused tests and confirm they pass**

Run:

```powershell
python -m pytest .agents/skills/video-content-digest/tests/test_check_env.py -q
```

Expected: all runtime and dependency-check tests pass.

### Task 3: Remove faster-whisper and expose only FunASR transcription

**Files:**
- Modify: `.agents/skills/video-content-digest/scripts/transcription_backends.py`
- Modify: `.agents/skills/video-content-digest/scripts/transcribe.py`
- Modify: `.agents/skills/video-content-digest/tests/test_transcription_backends.py`
- Modify: `.agents/skills/video-content-digest/tests/test_cli_smoke.py`

**Interfaces:**
- `transcribe_audio(audio_path, backend, asr_model, vad_model, punc_model, language)` remains callable by the CLI but accepts only `backend == "chinese"`.
- `transcribe.py --backend` accepts only `chinese` and defaults to it.
- `--model` is removed because no faster-whisper model name is used.
- Omitted model arguments default to the directories returned by `runtime_paths()`.

- [ ] **Step 1: Delete faster-whisper backend code**

In `transcription_backends.py`, change:

```python
SUPPORTED_BACKENDS = {"chinese"}
```

Delete `_transcribe_faster_whisper`, remove the `if backend == "light"` branch, and validate the backend before calling `_transcribe_funasr`. Keep timestamp normalization and FunASR sentence handling unchanged.

- [ ] **Step 2: Make model arguments default to skill-local models**

Import `model_paths` and use:

```python
defaults = model_paths()
asr_model = asr_model or str(defaults["asr"])
vad_model = vad_model or (str(defaults["vad"]) if defaults["vad"].exists() else None)
punc_model = punc_model or (str(defaults["punc"]) if defaults["punc"].exists() else None)
return _transcribe_funasr(audio_path, asr_model, vad_model, punc_model, language)
```

The ASR model remains mandatory through `_require_model_path`; VAD and punctuation remain optional.

- [ ] **Step 3: Simplify `transcribe.py` CLI**

Use:

```python
parser.add_argument("--backend", choices=["chinese"], default="chinese")
parser.add_argument("--language", default="zh")
parser.add_argument("--asr-model", default=None)
parser.add_argument("--vad-model", default=None)
parser.add_argument("--punc-model", default=None)
```

Remove the backward-compatible `transcribe()` faster-whisper function and the `--model` argument. Update the module description to state that it transcribes with FunASR Chinese mode only.

- [ ] **Step 4: Run transcription tests**

Run:

```powershell
python -m pytest .agents/skills/video-content-digest/tests/test_transcription_backends.py .agents/skills/video-content-digest/tests/test_cli_smoke.py -q
```

Expected: all tests pass without importing `faster_whisper`.

### Task 4: Update the content package template and supporting instructions

**Files:**
- Modify: `.agents/skills/video-content-digest/SKILL.md`
- Modify: `.agents/skills/video-content-digest/references/output-templates.md`
- Modify: `.agents/skills/video-content-digest/references/dependency-management.md`
- Modify: `.agents/skills/video-content-digest/references/platform-notes.md`
- Modify: `.agents/skills/video-content-digest/references/quality-checklist.md`
- Modify: `.agents/skills/video-content-digest/agents/openai.yaml`

**Interfaces:**
- The skill description continues to trigger for video URLs and local video paths.
- The final package uses a stable Chinese Markdown section order.
- All reference files are valid UTF-8 and contain no `light`, `faster-whisper`, old runtime path, or obsolete compatibility mode references.

- [ ] **Step 1: Rewrite `SKILL.md` runtime and backend instructions**

State that runtime files are always under `Path(skill_root()) / "lib"`, regardless of installation scope. Remove `VIDEO_DIGEST_SCOPE`, `VIDEO_DIGEST_HOME`, `light`, `all`, `api`, `local`, and faster-whisper examples. Keep `python scripts/check_env.py --mode chinese` and `--install` examples only. Update model examples to `lib/models/SenseVoiceSmall`, `lib/models/FSMN-VAD`, and optional `lib/models/PUNC`.

- [ ] **Step 2: Rewrite `output-templates.md` as valid UTF-8 Chinese**

Use this section order:

```markdown
# 视频内容包
## 基本信息
## 视频摘要
## 核心观点
## 内容拆解
### 选题角度
### 开头钩子
### 内容结构
### 视频爆点
### 互动引导
## 时间线
## 金句
## 公众号初稿
## 小红书初稿
## 标题备选
## 适合二次剪辑的片段
## 注意事项
```

For each content-decomposition subsection, instruct the writer to provide evidence or timestamps where available and distinguish source facts from editorial analysis.

- [ ] **Step 3: Update quality and platform references**

Change the checklist to verify the five new analysis dimensions, the two “初稿” labels, FunASR-only provenance, and UTF-8 output. Remove all light-backend quality notes. Update platform notes so local transcription always means FunASR Chinese mode.

- [ ] **Step 4: Update dependency management and agent metadata**

Document the skill-local `lib/` directory and the fixed four-package dependency set. Ensure `agents/openai.yaml` contains no stale mode or path wording.

- [ ] **Step 5: Search for stale references**

Run:

```powershell
rg -n --hidden --glob '!lib/**' "\.video-content-digest|VIDEO_DIGEST_HOME|VIDEO_DIGEST_SCOPE|faster-whisper|light|\ball\b|\bapi\b|\blocal\b" .agents/skills/video-content-digest .gitignore
```

Expected: no matches except intentional prose that explicitly says an obsolete feature was removed; remove even those references if the source must contain no obsolete terms.

### Task 5: Add ignore rules, remove obsolete files, and complete regression tests

**Files:**
- Modify: `.gitignore`
- Modify: `.agents/skills/video-content-digest/tests/test_cli_smoke.py`
- Modify: `.agents/skills/video-content-digest/tests/test_check_env.py`
- Modify: `.agents/skills/video-content-digest/tests/test_transcription_backends.py`
- Modify: `.agents/skills/video-content-digest/tests/test_normalize_transcript.py`
- Delete: `.video-content-digest/` if it exists

**Interfaces:**
- `lib/` is runtime data and must not be committed.
- Tests must use readable UTF-8 Chinese strings rather than mojibake fixtures.

- [ ] **Step 1: Ignore the skill-local runtime**

Add this exact rule to `.gitignore`:

```gitignore
.agents/skills/video-content-digest/lib/
```

Keep existing output and cache rules.

- [ ] **Step 2: Repair Chinese test fixtures**

Replace mojibake strings in `test_transcription_backends.py` and `test_normalize_transcript.py` with readable values such as `你好`、`世界`、`第一句` and `第二句`, preserving the same assertions.

- [ ] **Step 3: Add template and encoding checks**

Add a test that reads `references/output-templates.md` with UTF-8 and asserts:

```python
template = template_path.read_text(encoding="utf-8")
for heading in ("选题角度", "开头钩子", "内容结构", "视频爆点", "互动引导", "公众号初稿", "小红书初稿"):
    assert f"## {heading}" in template or f"### {heading}" in template
```

Also assert that the old title strings are absent.

- [ ] **Step 4: Remove the old runtime if present**

If `.video-content-digest/` exists in the worktree, remove it with a workspace-scoped PowerShell command; do not add migration code or documentation:

```powershell
$legacy = (Resolve-Path '.video-content-digest' -ErrorAction SilentlyContinue)
if ($legacy) { Remove-Item -LiteralPath $legacy.Path -Recurse -Force }
```

- [ ] **Step 5: Run the complete test suite**

Run:

```powershell
python -m pytest .agents/skills/video-content-digest/tests -q
```

Expected: all tests pass.

- [ ] **Step 6: Verify repository-wide stale references and working tree**

Run:

```powershell
rg -n --hidden --glob '!**/.git/**' --glob '!**/lib/**' "\.video-content-digest|faster-whisper|VIDEO_DIGEST_HOME|VIDEO_DIGEST_SCOPE" .
git status --short
```

Expected: no obsolete references and only the intended skill, documentation, test, and ignore-rule changes are present.

## Self-Review Checklist

- Runtime path requirement is covered by Task 2 and Task 5.
- Chinese-only dependency and backend requirements are covered by Tasks 1–3.
- Output naming and five-dimensional content decomposition are covered by Tasks 4–5.
- Legacy path deletion is covered by Task 5 without migration logic.
- UTF-8 repair and regression tests are covered by Tasks 4–5.
- No task requires automatic installation of Python, `ffmpeg`, or FunASR models.
