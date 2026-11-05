# Video Summary Radar

面向 Codex、Claude Code、Cursor 及其他遵循 Agent Skills 约定的 Agent 的视频内容情报技能集。

Video intelligence skills for Codex, Claude Code, Cursor, and other agents that support the Agent Skills convention.

## 安装 / Install

推荐按需安装，不要一次装入全部技能，以免增加 Agent 的常驻上下文：

```bash
npx skills add <github-owner>/video-summary-radar
```

若安装器尚未支持你的 Agent，请仅复制所需的 `skills/<skill-name>/` 完整目录到该 Agent 的 skills 目录。不要复制运行缓存、模型或生成结果。

## 稳定技能 / Stable skills

| Skill | 用途 |
| --- | --- |
| `video-content-digest` | 获取视频字幕、口播与必要画面，交付中文摘要、内容还原和转录证据；B站、抖音读取失败时可经 PeanutDL 下载。微信、小红书文案作为后续可选任务。 |
| `creator-intelligence` | 基于可验证的公开数据生成创作者情报、热点分析与选题策略。 |

所有 skill 都以 `SKILL.md` 为跨平台入口。当前不维护各 Agent 的专用适配层或市场插件。

## 运行时与隐私 / Runtime and privacy

- 技能源码目录只读；虚拟环境、模型、缓存与结果默认位于调用项目的 `.video-summary-radar/`。
- 首次使用只做依赖检查。安装 Python 包或下载模型必须由用户明确确认。
- 不提交 `.video-summary-radar/`、密钥、Cookie、真实账号配置或真实任务输出。

详见 [安装说明](docs/INSTALLATION.md)、[架构](docs/ARCHITECTURE.md) 与[贡献指南](docs/CONTRIBUTING.md)。

## 生命周期与发布 / Lifecycle and releases

- `skills/`：稳定技能，满足 CI 与发布门槛，可被默认安装。
- `experimental/`：预览技能，不保证兼容性或输出稳定性。
- `deprecated/`：废弃技能的迁移说明；不保留可执行旧副本。

仓库整体采用语义化版本，首个公开版本为 `v0.1.0`。变更记录见 [CHANGELOG.md](CHANGELOG.md)。

## 许可证 / License

[MIT](LICENSE)
