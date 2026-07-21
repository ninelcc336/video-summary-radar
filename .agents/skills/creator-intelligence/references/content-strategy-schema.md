# 内容策略任务数据 Schema

批量蒸馏任务目录将采集快照、账号画像、作业状态、内容包和策略报告放在同一目录中。所有 JSON 均使用 UTF-8，时间均使用带时区的 ISO 8601 字符串。

## account-profile.json

```json
{
  "platform": "bilibili",
  "domain": "AI 工具",
  "audience": "独立开发者",
  "source_text": "做 AI 工具评测，强调可验证的实测体验",
  "profile_url": "https://space.bilibili.com/123456",
  "content_format": "横向评测和实操教程",
  "business_goal": "积累关注并转化课程咨询",
  "exclusions": ["投资建议"]
}
```

`platform`、`domain`、`audience` 必填；`source_text` 与 `profile_url` 至少填写一个。主页链接只能是 `http` 或 `https`，并不代表 skill 可以绕过访问限制读取它。

## digest-manifest.json

```json
{
  "profile": {"platform": "bilibili", "domain": "AI 工具", "audience": "独立开发者", "source_text": "账号说明", "profile_url": "", "content_format": "", "business_goal": "", "exclusions": []},
  "created_at": "2026-07-21T12:00:00+00:00",
  "jobs": [
    {
      "stable_video_key": "youtube:abc123",
      "state": "pending",
      "package_path": "digests/youtube-abc123/content-package.md",
      "failure_stage": "",
      "failure_reason": "",
      "updated_at": "2026-07-21T12:00:00+00:00",
      "video": {"platform": "youtube", "video_id": "abc123", "title": "示例", "url": "https://www.youtube.com/watch?v=abc123"}
    }
  ]
}
```

`stable_video_key` 固定为 `platform:video_id`，是内容包和采集视频的唯一关联键。`video` 完整字段沿用 `data-schema.md`。

状态迁移只能是：`pending → succeeded`、`pending → failed`、`pending → skipped`。`failed` 必须填写 `failure_stage` 与 `failure_reason`。

## digest-jobs.json

这是给 `video-content-digest` 的最小作业清单：

```json
{
  "jobs": [
    {
      "stable_video_key": "youtube:abc123",
      "url": "https://www.youtube.com/watch?v=abc123",
      "title": "示例",
      "platform": "youtube",
      "state": "pending",
      "output_path": "digests/youtube-abc123/content-package.md"
    }
  ]
}
```

上游必须按 `output_path` 保存内容包。处理失败时不要创建无来源内容包。

## analysis.json

```json
{
  "profile": {"platform": "bilibili", "domain": "AI 工具", "audience": "独立开发者"},
  "sufficient_sample": false,
  "observations": [],
  "warnings": ["有效内容包仅 2 条，至少 5 条才输出高频规律。"],
  "recommendations": [
    {
      "topic": "低成本验证 AI 工具",
      "recent_heat_score": 80.0,
      "replicability_score": 100.0,
      "profile_match_score": 50.0,
      "evidence_completeness_score": 83.33,
      "total_score": 78.0,
      "confidence": 40.0,
      "evidence_urls": ["https://www.youtube.com/watch?v=abc123"]
    }
  ]
}
```

推荐分数由近期热度、可复刻性、账号匹配度、证据完整度组成。低样本或章节缺失会降低置信度，不能将评分表述为确定的流量预测。
