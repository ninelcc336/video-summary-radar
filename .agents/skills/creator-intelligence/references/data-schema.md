# Creator Intelligence 数据 Schema

所有采集路径都生成一个 UTF-8 JSON collection 文件：

```json
{
  "request": {"topic": "AI 工具", "range": "7d", "platforms": ["youtube"], "limit": 10},
  "requested_at": "2026-07-11T10:00:00+00:00",
  "videos": [],
  "statuses": []
}
```

`videos` 中每条记录必须包含：`platform`、`creator_id`、`creator_name`、`domain`、`video_id`、`title`、`url`、`published_at`、`duration_seconds`、`views`、`source_adapter`、`collected_at`、`metric_coverage`、`data_caveats`。

- 时间字段使用带时区的 ISO 8601 字符串。
- `metric_coverage` 包含 `views`、`likes`、`comments`、`shares`、`favorites` 五个布尔字段；缺失指标填 `false`，数值填 `0`。
- `source_adapter` 标识实际数据入口，例如 `agent-reach-bili`、`public-yt-dlp`。
- `data_caveats` 是限制说明列表；不要把无法取得的指标伪装成零值。

`statuses` 中每条记录包含：`platform`、`adapter`、`state`、`reason`、`collected_at`、`result_count`。`state` 只能是 `available`、`unavailable` 或 `failed`。
