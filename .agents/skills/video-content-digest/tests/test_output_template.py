from pathlib import Path


TEMPLATE = Path(__file__).resolve().parents[1] / "references" / "output-templates.md"


def test_output_template_is_utf8_and_contains_required_sections():
    template = TEMPLATE.read_text(encoding="utf-8")
    for heading in ("选题角度", "开头钩子", "内容结构", "视频爆点", "互动引导", "公众号初稿", "小红书初稿"):
        assert f"## {heading}" in template or f"### {heading}" in template
    assert "## 公众号文章" not in template
    assert "## 小红书文案" not in template
