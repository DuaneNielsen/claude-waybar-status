# claude-waybar-status

Claude Code plugin that reports session state to a local
[waybar-topics](../waybar-topics) HTTP server, so each waybar workspace button
changes color while a session is working or awaiting input.

## How it works

Five hooks (`SessionStart`, `UserPromptSubmit`, `Stop`, `Notification`,
`SessionEnd`) call `scripts/notify.py`, which POSTs to
`http://127.0.0.1:8770/cc/event` with:

- `event` — the hook name
- `session_id` — Claude's session UUID
- `pid` — the Claude process PID (the script's parent)
- `cwd` — the session's working directory

The waybar-topics server walks UP from the Claude PID via `/proc/<pid>/stat`
ppid until it finds an ancestor PID matching a niri window — that resolves
the session to its workspace. Per-workspace state is exposed as a `cc-working`
or `cc-awaiting` CSS class on the corresponding waybar topic button.

## State mapping

| Hook                | State      | Color (default)     |
|---------------------|------------|---------------------|
| `SessionStart`      | `awaiting` | red `#e74c3c`       |
| `UserPromptSubmit`  | `working`  | blue `#3498db`      |
| `Stop`              | `awaiting` | red                 |
| `Notification`      | `awaiting` | red                 |
| `SessionEnd`        | (removed)  | (no class)          |

## Install

The plugin needs to be discoverable by Claude Code. The simplest route is to
add it as a local plugin path in your Claude Code settings, or symlink it into
`~/.claude/plugins/`.

## Config

`WAYBAR_TOPICS_URL` env var overrides the server URL (default
`http://127.0.0.1:8770`).
