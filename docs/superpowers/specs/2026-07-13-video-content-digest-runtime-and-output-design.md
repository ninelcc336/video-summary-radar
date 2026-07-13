# Video Content Digest 运行时与内容包优化设计

## 背景

当前 `video-content-digest` 将项目级运行时放在 `.video-content-digest/`，同时保留了全局运行时、`light` 转录后端及多个兼容模式。内容模板还存在中文编码乱码，且缺少面向内容创作复用的结构化拆解。

## 目标

1. 全局安装和项目级安装的 skill 都将依赖、模型、缓存和配置放在当前 skill 目录的 `lib/` 中。
2. 删除 `light`、`all`、`api`、`local` 等转录模式，只保留中文 FunASR 后端。
3. 将公众号和小红书输出明确标记为“初稿”。
4. 在内容包中新增“内容拆解”，覆盖选题角度、开头钩子、内容结构、视频爆点、互动引导五个维度。
5. 修复相关中文文件的 UTF-8 编码问题，并用测试固定新行为。

## 设计

### 运行时路径

运行时根目录由 `runtime_paths.py` 通过 skill 根目录计算：

```text
<skill-root>/lib/
├── venv/
├── models/
├── cache/
├── config/
└── manifest.json
```

项目级安装和全局安装只影响 `<skill-root>`，不再根据项目 `.git`、`VIDEO_DIGEST_SCOPE` 或 `VIDEO_DIGEST_HOME` 选择其他位置。安装脚本仍只在显式传入 `--install` 后创建虚拟环境并安装 Python 依赖。

旧 `.video-content-digest/` 不做迁移、检测、保留或自动删除逻辑；代码、文档和测试中不再引用该路径。

### 转录后端

只保留 FunASR 中文后端，依赖集合固定为：

```text
yt-dlp
funasr
torch
torchaudio
```

模型默认从 `lib/models/` 查找：

```text
SenseVoiceSmall/
FSMN-VAD/
PUNC/
```

其中 ASR 模型是必需项，VAD 和标点模型可选。模型不会由 skill 自动下载；缺失时报告准确目录和下一步操作。

### 内容包结构

输出模板使用正常 UTF-8 中文，并保留现有摘要、核心观点、时间线、金句、标题备选、二次剪辑片段和注意事项。公众号与小红书章节改为：

```markdown
## 公众号初稿
## 小红书初稿
```

新增章节：

```markdown
## 内容拆解

### 选题角度
### 开头钩子
### 内容结构
### 视频爆点
### 互动引导
```

五个维度必须基于视频转录、字幕、标题、描述或用户提供的上下文。开头钩子、视频爆点和内容结构尽量附时间戳；对于无法从来源确认的判断，标记为分析而不是事实。

### 文档与测试

同步更新 `SKILL.md`、依赖管理说明、平台说明、质量清单和输出模板，删除 `light` 及旧运行时路径的描述。测试覆盖固定 skill-local `lib/` 路径、唯一中文依赖集合、CLI 帮助信息、默认模型路径、内容模板章节和 UTF-8 文本。

## 错误处理

- 缺少 Python：说明需要 Python 3.10 或更高版本。
- 缺少 Python 包：报告目标虚拟环境和仅在确认后执行的安装命令。
- 缺少 `ffmpeg`：报告用途和平台包管理器命令，不自动安装。
- 缺少 FunASR 模型：报告 `lib/models/` 下的准确路径。
- 无可用字幕或转录质量不足：在内容包中披露限制，避免过度确定的结论。
- 受限或需要登录的视频：不绕过访问限制，请用户提供本地文件、字幕或转录稿。

## 验证标准

- `runtime_paths()` 的 `home` 始终等于当前 skill 根目录下的 `lib`。
- `check_env.py --help` 和 `transcribe.py --help` 不再展示 `light`、`all`、`api` 或 `local`。
- 所有 Python 依赖检查和安装目标都位于 `lib/venv/`。
- 输出模板包含五个内容拆解维度，并使用“公众号初稿”“小红书初稿”。
- 相关测试全部通过，源码和文档不再引用旧 `.video-content-digest/` 路径。
