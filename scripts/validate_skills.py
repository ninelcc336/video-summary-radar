#!/usr/bin/env python3
"""校验稳定 skill 的最小目录与 front matter 约定。"""

from __future__ import annotations

import re
import sys
from pathlib import Path


REQUIRED_FIELDS = ("name", "description")


def repository_root() -> Path:
    """返回仓库根目录，避免校验依赖执行时的当前工作目录。"""
    return Path(__file__).resolve().parents[1]


def read_front_matter(skill_file: Path) -> dict[str, str]:
    """读取简单 YAML front matter，拒绝缺失或格式不完整的技能入口。"""
    content = skill_file.read_text(encoding="utf-8")
    match = re.match(r"^---[ \t]*\n(.*?)\n---[ \t]*(?:\n|$)", content, flags=re.DOTALL)
    if not match:
        raise ValueError("缺少 YAML front matter")
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip():
            fields[key.strip()] = value.strip()
    return fields


def validate_skill(skill_dir: Path) -> list[str]:
    """返回单个稳定 skill 的全部校验错误，便于一次性修复。"""
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return [f"{skill_dir.name}: 缺少 SKILL.md"]
    try:
        fields = read_front_matter(skill_file)
    except ValueError as error:
        return [f"{skill_dir.name}: {error}"]
    for field in REQUIRED_FIELDS:
        if not fields.get(field):
            errors.append(f"{skill_dir.name}: front matter 缺少 {field}")
    if fields.get("name") and fields["name"] != skill_dir.name:
        errors.append(f"{skill_dir.name}: name 必须与目录名一致")
    return errors


def main() -> int:
    """校验 skills 目录并以非零退出码阻止不完整的稳定发布。"""
    skills_dir = repository_root() / "skills"
    directories = sorted(path for path in skills_dir.iterdir() if path.is_dir()) if skills_dir.is_dir() else []
    errors = [error for skill_dir in directories for error in validate_skill(skill_dir)]
    if errors:
        print("技能结构校验失败：", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"技能结构校验通过：{len(directories)} 项稳定技能。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
