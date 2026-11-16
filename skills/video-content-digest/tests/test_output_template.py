from pathlib import Path


TEMPLATE = Path(__file__).resolve().parents[1] / "references" / "output-templates.md"


def test_output_template_is_utf8_and_contains_required_sections():
    """报告固定五个阅读章节，二次创作文案不进入默认交付。"""
    template = TEMPLATE.read_text(encoding="utf-8")
    for heading in ("视频信息", "整体概括", "最有价值的部分", "核心内容与必要展开", "内容缺口与来源"):
        assert f"## {heading}" in template
    assert "时间戳仅用于溯源" in template
    content_package = template.split("```markdown\n", 1)[1].split("```", 1)[0]
    assert "创作复用" not in content_package
    assert "公众号初稿" not in content_package
    assert "小红书初稿" not in content_package
