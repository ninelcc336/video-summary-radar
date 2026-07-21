#!/usr/bin/env python3
"""检查 Creator Intelligence 的可选联网能力，不安装任何依赖。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from creator_intelligence.environment import inspect_environment  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=10, help="单个探测命令的超时秒数")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()
    report = inspect_environment(max(1, args.timeout))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
