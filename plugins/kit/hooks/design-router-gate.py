#!/usr/bin/env python3
"""Refuse Claude's calls to design skills that kit:design-router did not start.

A PreToolUse hook in kit, with the matcher Skill. Claude Code sends it
{"session_id": ..., "tool_input": {"skill": "<plugin>:<name>"}, ...} on
stdin. A command the user types never reaches it.

A fresh ticket <tickets>/<session_id>/<skill>, written by
design-router-ticket.py at most 5 minutes before, lets one call through and
is deleted. A stale ticket is deleted too. <tickets> is
DESIGN_ROUTER_TICKETS, else ~/.cache/design-router/tickets. Without a ticket,
the gate judges the skill by its plugin prefix, the text before the first
":", looked up in skills/design-router/plugins.json:

- no prefix, or the prefix kit: let through;
- routed: refuse, and point to kit:design-router;
- excluded: refuse, and say so;
- not-design: let through;
- absent from the list but an installed plugin: refuse as not reviewed;
- absent and not installed (a project folder, a claude.ai skill set): let
  through.

Inputs: the list (DESIGN_ROUTER_PLUGINS, else
$CLAUDE_PLUGIN_ROOT/skills/design-router/plugins.json, else the same path
next to this script); the installed plugins, which are the names before "@"
of the keys of .plugins in <home>/installed_plugins.json and the name in
each <home>/synced/*/*/.claude-plugin/plugin.json, where <home> is
DESIGN_ROUTER_PLUGIN_HOME, else ~/.claude/plugins.

Prints nothing to let a call through, a deny decision to refuse it, and a
systemMessage alone when the list cannot be read. It never prints allow,
which would skip the user's permission prompts. It fails open: a broken
list or a crash refuses nothing. Always exits 0.
"""

import json
import os
import sys
import time
from pathlib import Path

LIST = Path("skills") / "design-router" / "plugins.json"
FRESH = 300


def list_path():
    env = os.environ.get("DESIGN_ROUTER_PLUGINS")
    if env:
        return Path(env)
    root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    return (Path(root) if root else Path(__file__).resolve().parent.parent) / LIST


def plugin_home():
    env = os.environ.get("DESIGN_ROUTER_PLUGIN_HOME")
    return Path(env) if env else Path.home() / ".claude" / "plugins"


def tickets_dir():
    env = os.environ.get("DESIGN_ROUTER_TICKETS")
    return Path(env) if env else Path.home() / ".cache" / "design-router" / "tickets"


def safe(part):
    return isinstance(part, str) and part not in ("", ".", "..") and "/" not in part


def take_ticket(tickets, session_id, skill, now):
    if not (safe(session_id) and safe(skill)):
        return False
    ticket = tickets / session_id / skill
    try:
        age = now - ticket.stat().st_mtime
        ticket.unlink()
    except OSError:
        return False
    return age <= FRESH


def load_states(path):
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def installed_plugins(home):
    names = set()
    try:
        plugins = json.loads((home / "installed_plugins.json").read_text())["plugins"]
        names.update(key.split("@")[0] for key in plugins)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        pass
    for manifest in home.glob("synced/*/*/.claude-plugin/plugin.json"):
        try:
            name = json.loads(manifest.read_text())["name"]
        except (OSError, ValueError, KeyError, TypeError):
            continue
        if isinstance(name, str):
            names.add(name)
    return names


def refuse(text):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                   "permissionDecision": "deny",
                                   "permissionDecisionReason": text}}


def decide(skill, session_id):
    if not isinstance(skill, str):
        return None
    skill = skill[1:] if skill.startswith("/") else skill
    if ":" not in skill:
        return None
    plugin = skill.split(":")[0]
    if plugin == "kit":
        return None
    if take_ticket(tickets_dir(), session_id, skill, time.time()):
        return None
    path = list_path()
    states = load_states(path)
    if states is None:
        return {"systemMessage": f"Design router gate: cannot read {path}; "
                                 "it lets every skill through."}
    state = states.get(plugin)
    if state == "routed":
        return refuse(f"{skill} is a design skill: invoke kit:design-router, "
                      "which starts it.")
    if state == "excluded":
        return refuse(f"{plugin} is excluded from the design router: tell the "
                      "user, who can type the command or turn the plugin off.")
    if state is not None:
        return None
    if plugin in installed_plugins(plugin_home()):
        return refuse(f"{plugin} is not reviewed for design skills: tell the user "
                      "to add it to plugins.json in kit's design-router skill, "
                      "commit, then run claude plugin update kit@claude-setup and "
                      "/reload-plugins; or to type the command.")
    return None


def main():
    try:
        data = json.loads(sys.stdin.read())
    except ValueError:
        return 0
    tool_input = data.get("tool_input") if isinstance(data, dict) else None
    if not isinstance(tool_input, dict):
        return 0
    out = decide(tool_input.get("skill"), data.get("session_id"))
    if out is not None:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
