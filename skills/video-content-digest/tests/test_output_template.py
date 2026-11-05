from pathlib import Path


TEMPLATE = Path(__file__).resolve().parents[1] / "references" / "output-templates.md"


def test_output_template_is_utf8_and_contains_required_sections():
    template = TEMPLATE.read_text(encoding="utf-8")
    for heading in (
        "结论速览",
        "完整内容还原",
        "关键画面与操作",
        "关键结论与可执行启发",
        "待确认信息",
        "证据与处理说明",
    ):
        assert f"## {heading}" in template or f"### {heading}" in template
    assert "时间戳仅用于溯源" in template
    content_package = template.split("```markdown\n", 1)[1].split("```", 1)[0]
    assert "创作复用" not in content_package
    assert "公众号初稿" not in content_package
    assert "小红书初稿" not in content_package
