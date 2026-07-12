---
name: creator-intelligence
description: 当用户要分析关注的创作者、寻找某个主题近期热门视频、生成爆款视频报告，或比较 B站、YouTube、抖音、小红书等平台的创作者内容表现时使用。此 skill 优先通过已安装的 agent-reach 收集可验证的实时视频数据；缺失时先征询用户是否安装，若用户拒绝则只通过内置公共适配器处理可公开获取的平台，并在报告中透明标明无法抓取的平台与原因。
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
