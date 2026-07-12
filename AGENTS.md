# AGENTS.md

## 项目级技能限制

- 本项目禁用 `agent-reach` 技能。
- 不得调用 `agent-reach` CLI、`agent-reach` 虚拟环境、其后端适配器或相关 MCP 能力。
- 处理视频链接时，优先使用项目内的 `video-content-digest` 技能；不得因为 URL 或平台触发而回退到 `agent-reach`。
- 若项目内所需依赖缺失，应说明缺失项并征得用户同意后再安装，不得借用 `agent-reach` 环境中的同名工具代替。

