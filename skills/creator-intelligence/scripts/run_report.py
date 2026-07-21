from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from creator_intelligence.pipeline import generate_report, write_report  # noqa: E402


def main() -> None:
    """解析报告参数并将默认结果写入调用工作区的私有输出目录。"""
    parser = argparse.ArgumentParser(prog="creator-intelligence-report")
    parser.add_argument("--range", choices=["1d", "7d", "30d"], default="7d")
    parser.add_argument("--input", required=True, help="真实采集得到的 collection JSON")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    output_path = (
        Path(args.output)
        if args.output
        else Path.cwd() / ".video-summary-radar" / "outputs" / "reports" / f"creator-intelligence-{now.date().isoformat()}.md"
    )
    result = generate_report(args.range, input_path=args.input, now=now)
    written = write_report(result.markdown, output_path)
    print(f"报告已生成：{written}")


if __name__ == "__main__":
    main()
