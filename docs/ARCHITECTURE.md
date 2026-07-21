# 架构

## 设计目标

本仓库只收录由维护者维护、面向视频内容情报工作流的 Agent Skills。`SKILL.md` 是每项能力的跨平台入口；脚本、测试与参考资料随 skill 一起发布。

```text
skills/<skill-name>/
├── SKILL.md
├── scripts/
├── references/
└── tests/
```

`creator-intelligence` 负责多视频采集、排序与策略分析；`video-content-digest` 负责单条视频的字幕、转写与内容包生成。前者通过稳定的 `platform:video_id` 作业清单调用后者，不复制其下载和转写逻辑。

## 写入边界

安装目录只能读取。调用项目的 `.video-summary-radar/` 是唯一默认运行目录：

```text
.video-summary-radar/
├── runtime/    # 虚拟环境、模型、缓存与运行清单
└── outputs/    # 转录、报告与内容包
```

用户可显式指定其他输出或运行目录。未经确认，skill 不安装依赖、不下载模型、不修改系统级工具，也不删除任何运行数据。

## 跨平台与分发

正式支持 Windows、macOS 和 Linux。仓库优先遵循通用 Agent Skills 目录约定，通过 `npx skills add` 分发，并提供手动复制目录的兜底方式。专用插件市场仅在有明确维护需求时添加。
