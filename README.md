# Video Summary Radar

## 项目简介

这个仓库用于整理和演示视频内容摘要、转录与生成相关的数据与工具。它包含了一些视频来源链接、输出结果以及 AI 代理技能配置，适合用于视频内容分析、短视频素材处理和内容包生成的参考。

## 目录结构

- `.agents/` - 代理技能和相关配置
- `docs/` - 文档目录
- `outputs/` - 生成的转录、内容包和输出文件
- `video-url.txt` - 视频链接示例列表
- `.gitignore` - Git 忽略规则

## 使用说明

1. `video-url.txt` 中是测试用的视频链接。
2. `outputs/` 目录下存放了不同视频的转录文本、内容包和结果文件，可作为样例数据阅读和分析。
3. `.agents/skills` 目录里包含了 `video-content-digest` 相关技能的定义和参考资料，说明该项目可能用于 AI 视频摘要/内容消化场景。

## 注意事项

- `docs/superpowers` 已列入 `.gitignore`，不会被 Git 追踪。
- `outputs/` 目录也在 `.gitignore` 中，因此本地生成内容不会提交到版本库。
