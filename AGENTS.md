# AGENTS.md

## 注意事项
- 提交信息统一采用中文

## 开发与实际使用

- Skill 源码在 `skills/<skill-name>/`，直接在这里修改；`.agents/skills/` 仅作为本机发现入口，不作为另一份源码。
- 个人使用工作区放在 `local-workspaces/`，整个目录由 Git 忽略。视频蒸馏工作区为 `local-workspaces/视频蒸馏/`，其 `.video-summary-radar/` 保存已有环境、模型、缓存、媒体与结果。
- 从仓库根目录处理实际视频时，将采集、下载和转写命令的工作目录设为对应的本地工作区，使默认运行路径仍为该工作区下的 `.video-summary-radar/`。不要把运行数据写入 `skills/`，不要把仓库根目录的既有运行数据自动合并或清理。
- 更新函数时添加清晰的函数级注释。按范围运行验证，通常包括 `python scripts/validate_skills.py` 和 `python -m pytest skills`；再从本地使用工作区执行原始或等价输入，验证当前源码的实际行为。
- 源码提交前更新 `CHANGELOG.md` 的 Unreleased 区域。不要提交个人工作区、账号配置、凭据、媒体、模型或真实任务输出；未经明确同意不安装依赖、不下载模型，也不安装或卸载 `ffmpeg`。

## 视频采集的浏览器边界

- 单视频、创作者采集、批量作业和第三方下载页默认只使用匿名公开入口；需要浏览器时，优先使用已确认隔离且未登录的 Codex 内置浏览器，否则使用全新独立上下文或空配置目录。
- 视频采集不适用“真实网站优先使用个人 Chrome”的通用规则。不连接日常 Chrome，不复用或复制个人 Cookie、profile、扩展登录态或认证状态，不调用会自动导入这些状态的 Agent-Reach/OpenCLI 后端。
- 无法确认隔离时跳过该路线；失败不自动切回个人浏览器或要求登录。普通登录提示可尝试其他匿名渠道；验证码、明确风控或限流则停止该平台请求，不跨后端连续重试。必要时请求本地视频或导出字幕。
- `yt-dlp` 使用 `--ignore-config`，不传账号或 Cookie 参数。结果记录实际获取渠道、匿名方式及失败原因。

## 已有视频产物检索

- 仓库内实际入口为 `local-workspaces/视频蒸馏/.video-summary-radar/outputs/产物索引.md`；该工作区被 Git 忽略，普通仓库搜索可能漏掉它，应显式指定路径。
- 先根据索引的分类、标签、标题、摘要或作者筛选，再读取命中的 `视频总结.md`。精确引用读同目录 `口播稿.txt`，证据核对才进入 `处理资料/`；不要默认扫描媒体、模型、缓存、原始日志和历史副本。
- 只读查询：从本地使用工作区运行 `python <仓库绝对路径>/skills/video-content-digest/scripts/index_outputs.py --query "关键词"`。多个词以空格分隔，全部匹配；无匹配时扩大到总结与口播正文，不据标签直接断言视频内容。
- 全文搜索使用 `rg --no-ignore --hidden`，限定实际 outputs 路径及 `视频总结.md` / `口播稿.txt`，排除 `处理资料/`、`处理记录/`。
- 总结顶部 YAML 的 `title/category/tags/summary` 是检索元数据来源；复用已有标签，不给口播 TXT 加元数据。完成新增、归整或元数据修改后，从使用工作区运行同脚本（不带 --query）重建 `产物索引.md`。规范见 `skills/video-content-digest/references/retrieval.md`。
