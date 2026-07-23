# Changelog

## [Unreleased]

### Changed

- 将技能源码从 `.agents/skills/` 迁移到跨 Agent 的 `skills/` 目录。
- 将运行环境、模型、缓存和生成结果迁移为工作区私有数据。

## [0.1.0] - 2026-07-21

### Added

- 首次以视频内容情报 Agent Skills 源码仓库形式发布。
- `video-content-digest` 与 `creator-intelligence` 两项稳定技能。

## [0.1.1] - 2026-07-23

- 优化 `video-content-digest`：优先使用浏览器能力取证，默认输出语义化内容还原、待确认信息与证据说明；创作复用改为按需生成。
