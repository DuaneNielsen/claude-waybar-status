#!/usr/bin/env python3
"""Hook script: POST the current session's state to the waybar-topics server.

Reads the hook payload from stdin (Claude Code passes JSON with session_id,
hook_event_name, cwd, etc.), then sends:

    POST {SERVER}/cc/event
    {
      "event": "<hook_event_name>",
      "session_id": "...",
      "pid": <claude pid (our parent)>,
      "cwd": "..."
    }

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


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    payload = {
        "event": data.get("hook_event_name") or "",
        "session_id": data.get("session_id") or "",
        "pid": os.getppid(),
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
