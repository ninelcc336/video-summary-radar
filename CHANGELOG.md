# Changelog

## [Unreleased]

### Changed

- 将 `video-content-digest` 收束为视频内容获取与忠实整理；微信公众号、小红书等文案仅提供后续创作选项，不再纳入技能交付。
- 为 B站、抖音增加页面和字幕读取不足时的 PeanutDL 下载回退，下载后复用本地音频提取、转写与证据记录流程。

## [0.1.2] - 2026-09-17

### Changed

- 将技能源码从 `.agents/skills/` 迁移到跨 Agent 的 `skills/` 目录。
- 将运行环境、模型、缓存和生成结果迁移为工作区私有数据。
- `video-content-digest` 现在可直接规范化本地 ASR 生成的 JSON 转录结果。
- Windows 上校验 FunASR 模型路径时不再解析映射驱动器路径。

## [0.1.0] - 2026-07-21

### Added

- 首次以视频内容情报 Agent Skills 源码仓库形式发布。
- `video-content-digest` 与 `creator-intelligence` 两项稳定技能。

## [0.1.1] - 2026-07-23

- 优化 `video-content-digest`：优先使用浏览器能力取证，默认输出语义化内容还原、待确认信息与证据说明；创作复用改为按需生成。
