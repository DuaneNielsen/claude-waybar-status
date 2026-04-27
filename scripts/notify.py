#!/usr/bin/env python3
"""Hook script: POST the current session's state to the waybar-topics server.

Reads the hook payload from stdin (Claude Code passes JSON with session_id,
hook_event_name, cwd, etc.), then sends:

    POST {SERVER}/cc/event
    {
      "event": "<hook_event_name>",
      "session_id": "...",
      "pid": <claude pid>,
      "cwd": "..."
    }

The script's `getppid()` is the short-lived shell that ran the hook, not the
claude process — so we walk up the process tree to find the real claude PID.
The server uses that PID to resolve the session to a niri window (and would
otherwise prune the session as soon as the shell exits).

Failures are swallowed — never block Claude on a missing/down server.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

SERVER = os.environ.get("WAYBAR_TOPICS_URL", "http://127.0.0.1:8770")
TIMEOUT = 1.0


def _proc_ppid(pid: int):
    try:
        with open(f"/proc/{pid}/stat") as f:
            content = f.read()
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return None
    rparen = content.rfind(")")
    if rparen < 0:
        return None
    rest = content[rparen + 2:].split()
    try:
        return int(rest[1])
    except (IndexError, ValueError):
        return None


def _proc_comm(pid: int):
    try:
        with open(f"/proc/{pid}/comm") as f:
            return f.read().strip()
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return None


def _find_claude_pid(start_pid: int):
    pid = start_pid
    for _ in range(20):
        if pid is None or pid <= 1:
            return None
        if _proc_comm(pid) == "claude":
            return pid
        pid = _proc_ppid(pid)
    return None


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    claude_pid = _find_claude_pid(os.getppid()) or os.getppid()
    payload = {
        "event": data.get("hook_event_name") or "",
        "session_id": data.get("session_id") or "",
        "pid": claude_pid,
        "cwd": data.get("cwd") or "",
    }

    if not payload["event"] or not payload["session_id"]:
        return 0

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{SERVER.rstrip('/')}/cc/event",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=TIMEOUT).read()
    except (urllib.error.URLError, OSError, TimeoutError):
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
