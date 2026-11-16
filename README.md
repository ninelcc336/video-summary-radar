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

## 默认视频产物

每条视频默认保存到 `.video-summary-radar/outputs/视频标题__平台-视频ID/`：`口播稿.txt` 保留原始表达，`视频总结.md` 包含整体概括、最有价值的部分、必要展开与来源缺口；字幕、媒体、截图和日志统一放在 `处理资料/`。

相同视频重复解析沿用首次目录名，已有稿件默认保留。只取得页面章节时标为部分解析，不补造口播稿。单视频和批量任务使用同一规范，批次另提供可点击索引。

视频总结顶部保存分类、3–8 个标签和一句话摘要。交付后运行 `skills/video-content-digest/scripts/index_outputs.py` 生成带分类、标签、摘要和链接的 `产物索引.md`，Agent 先筛索引再读取总结；`--query "关键词"` 可只读查询。脚本从调用工作区读取默认 outputs，自定义位置使用 `--output-root`。规则见 [产物标签与检索](skills/video-content-digest/references/retrieval.md)。

## 运行时与隐私 / Runtime and privacy

- 技能源码目录只读；虚拟环境、模型、缓存与结果默认位于调用项目的 `.video-summary-radar/`。
- 首次使用只做依赖检查。安装 Python 包或下载模型必须由用户明确确认。
- 视频采集默认匿名：先用公开元数据/字幕，需要页面交互时使用已确认隔离且未登录的浏览器。不连接个人 Chrome，不复用或自动导入个人登录态；失败时说明限制或使用本地视频/字幕，不自动切换到个人账号。
- 不提交 `.video-summary-radar/`、密钥、Cookie、真实账号配置或真实任务输出。

详见 [安装说明](docs/INSTALLATION.md)、[架构](docs/ARCHITECTURE.md) 与[贡献指南](docs/CONTRIBUTING.md)。

## 本地开发与使用

可以在同一仓库中修改 Skill 并运行个人任务：源码保留在 `skills/`，使用工作区放在 `local-workspaces/<工作区名称>/`，其环境和结果保存在工作区内的 `.video-summary-radar/`。整个 `local-workspaces/` 由 Git 忽略。

在仓库根目录开发时，实际采集、下载和转写命令仍以对应使用工作区为当前目录；源码测试在仓库根目录运行。需要 Agent 自动发现源码技能时，可在本机 `.agents/skills/` 中建立到 `skills/<skill-name>/` 的目录联接或符号链接；这些本机入口不提交，不复制源码。

## 生命周期与发布 / Lifecycle and releases

- `skills/`：稳定技能，满足 CI 与发布门槛，可被默认安装。
- `experimental/`：预览技能，不保证兼容性或输出稳定性。
- `deprecated/`：废弃技能的迁移说明；不保留可执行旧副本。

仓库整体采用语义化版本，首个公开版本为 `v0.1.0`。变更记录见 [CHANGELOG.md](CHANGELOG.md)。

## 许可证 / License

[MIT](LICENSE)
