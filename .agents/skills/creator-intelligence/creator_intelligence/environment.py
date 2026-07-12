from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any


PUBLIC_TOOLS = ("yt-dlp", "bili")


def run_json_command(command: list[str], timeout_seconds: int) -> tuple[dict[str, Any] | None, str]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return None, "探测超时"
    except OSError as exc:
        return None, str(exc)

    if completed.returncode != 0:
        message = completed.stderr.strip() or f"退出码 {completed.returncode}"
        return None, message
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None, "探测命令未返回有效 JSON"
    return payload if isinstance(payload, dict) else {"result": payload}, ""


def inspect_environment(timeout_seconds: int = 10) -> dict[str, Any]:
    agent_reach_path = shutil.which("agent-reach")
    if agent_reach_path is None:
        agent_reach = {"state": "unavailable", "reason": "未安装 agent-reach", "details": {}}
    else:
        payload, reason = run_json_command([agent_reach_path, "doctor", "--json"], timeout_seconds)
        agent_reach = {
            "state": "available" if payload is not None else "unavailable",
            "reason": reason,
            "details": payload or {},
        }

    tools = {name: {"available": shutil.which(name) is not None} for name in PUBLIC_TOOLS}
    return {"agent_reach": agent_reach, "public_tools": tools}
