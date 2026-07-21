---
name: creator-intelligence
description: 当用户要分析关注的创作者、寻找某个主题近期热门视频、生成爆款视频报告，或比较 B站、YouTube、抖音、小红书等平台的创作者内容表现时使用。用户要求批量蒸馏关注博主的视频、从多个视频提炼规律、结合自己的自媒体账号定位推荐可复刻爆款选题时，也必须使用此 skill 编排 video-content-digest。此 skill 优先通过已安装的 agent-reach 收集可验证的实时视频数据；缺失时先征询用户是否安装，若用户拒绝则只通过内置公共适配器处理可公开获取的平台，并在报告中透明标明无法抓取的平台与原因。
---

# Creator Intelligence

将真实视频数据整理成中文创作者情报报告。它支持：

- 关注列表（watchlist）：分析用户配置的创作者近期内容；
- 主题发现（discovery）：按主题、平台和时间范围寻找近期热门视频。

不要把 `tests/fixtures/` 中的数据用于用户请求。它们只用于自动化测试。

## 运行前检查

先运行，不安装任何依赖：

```bash
python <skill_path>/scripts/check_environment.py --json
```

按结果选择入口：

1. `agent_reach.state` 为 `available`：优先使用 Agent-Reach。
2. `agent-reach` 不可用：先向用户明确询问：

   > 未检测到可用的 Agent-Reach。是否需要安装它以获取更完整的多平台真实数据？

   用户同意后，遵循 `references/installation.md` 的官方安装流程；安装完成后重新执行检查。未经同意不得安装。
3. 用户拒绝安装：使用内置公共适配器。它仅支持当前环境中能合法公开访问的平台；其余平台必须记录为无法抓取，不能用样例、估算值或无来源链接补位。

## 数据采集

先判定模式：

- 用户提到“我关注的”“watchlist”“配置里的账号”时使用 watchlist 模式，读取 `config/creators.yaml`。
- 其余按领域、关键词、平台趋势查找的请求使用 discovery 模式。
- 时间范围：最近一天=`1d`、最近一周=`7d`、最近一个月/30天=`30d`；缺省为 `7d`。

### Agent-Reach 路径

阅读 `references/platform-capabilities.md` 中对应平台的说明，再调用当前 Agent-Reach 环境实际可用的只读命令。保留原始链接、发布时间、播放/互动指标与抓取时间。

将结果归一化为 `references/data-schema.md` 定义的 collection JSON，写入 `outputs/collection.json`，再运行：

```bash
python <skill_path>/scripts/run_report.py --range 7d --input outputs/collection.json
```

平台需要登录、没有当前环境后端、返回字段不足或命令超时时，保留对应失败状态并继续其他平台。不要绕过访问控制。

### 内置公共适配器路径

用户拒绝安装 Agent-Reach 后，对 discovery 请求运行：

```bash
python <skill_path>/scripts/collect_public.py \
  --topic "AI 工具" \
  --range 7d \
  --platform youtube,bilibili \
  --output outputs/collection.json
python <skill_path>/scripts/run_report.py --range 7d --input outputs/collection.json
```

- YouTube 使用本机已安装的 `yt-dlp` 搜索公开结果。
- B站使用公开搜索接口；接口受限、失败或字段不完整时会写入限制。
- 抖音、小红书没有稳定、无登录的内置公共发现入口，必须在报告中标为无法抓取。
- watchlist 模式下，如果公共入口无法依据配置中的账号标识可靠验证创作者身份，标记该创作者无法抓取，不用关键词猜测替代。

## 批量蒸馏与选题策略

当用户要求“批量蒸馏关注博主”“结合我的账号推荐可做选题”“找可复刻爆款”或等价请求时，在正常采集后进入此模式。

### 输入与准备

1. 收集用户账号画像。账号画像可来自对话描述，也可来自账号主页链接；至少要有平台、内容领域、目标受众，以及对话描述或链接之一。链接只能使用当前权限可访问的公开信息，无法验证时保留限制说明。
2. 将账号画像写为 `account-profile.json`。字段格式见 `references/content-strategy-schema.md`。
3. 先执行正常采集，生成真实 `collection.json`。遵循本 skill 的 Agent-Reach 检查、访问边界和降级规则。
4. 创建任务目录：

```powershell
python <skill_path>/scripts/prepare_digest_batch.py --collection outputs/collection.json --profile account-profile.json --range 7d --mode top --limit 10 --output-dir outputs/content-strategy
```

- 默认使用 `top`，仅在用户明确要求全量蒸馏时使用 `--mode all`。
- 该命令生成 `collection.json`、`account-profile.json`、`digest-manifest.json` 和 `digest-jobs.json`，并不会下载或转写视频。

### 逐条内容蒸馏

读取 `digest-jobs.json`，对每个 `pending` 作业调用 `video-content-digest`：

1. 仅处理作业指定的 `url`。
2. 将固定格式内容包写到该作业的 `output_path`，例如 `digests/youtube-abc/content-package.md`。
3. 保留来源链接、字幕来源、时间戳和质量限制。无法取得内容包时，不得补造内容；记录失败原因，继续其他作业。

每条作业由 `platform:video_id` 稳定关联，不得用标题匹配。不要复制 `video-content-digest` 的下载、音频提取或转写逻辑。

### 聚合与报告

完成可用作业后运行：

```powershell
python <skill_path>/scripts/run_content_strategy.py --run-dir outputs/content-strategy --range 7d
```

它会更新 `digest-manifest.json`，并写出：

- `analysis.json`：评分分量、置信度、证据 URL 与来源 stable key；
- `report.md`：批量蒸馏索引、创作者与样本规律、可复刻爆款选题池、优先级行动清单、数据覆盖与限制。

推荐仅复刻选题角度、标题策略、叙事结构、表达节奏和互动设计；不要建议照抄原文、画面、素材或未经验证的事实。推荐评分由近期热度、可复刻性、账号匹配度和证据完整度构成。有效内容包少于 5 条时，只报告样本观察与不足，不下“高频规律”结论。

## 报告规则

报告必须包含：

1. 各平台热度榜单：按平台内热度分排序。热度综合播放速度与可用互动指标。
2. 跨平台参考榜单：只能作为参考，明确提示不同平台绝对播放量不可直接等价。
3. 爆款规律分析：少于 5 条数据时只说明样本不足，不下规律结论。
4. 数据覆盖与限制：逐平台列出数据入口、状态、数量、采集时间和失败原因。

每条视频必须保留来源适配器、采集时间、指标可用性和数据限制。不要虚构播放量、互动数据、发布时间或来源链接。

## 配置格式

关注列表保存在 `config/creators.yaml`。字段与 collection JSON 见 `references/data-schema.md`。账号需要是平台可识别的真实账号标识；示例或占位账号不会产生正式报告。

## 验证

```bash
python <skill_path>/scripts/check_environment.py --json
```
