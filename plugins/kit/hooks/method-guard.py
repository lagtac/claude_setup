#!/usr/bin/env python3
"""Warn at session start when a project's method switch is half set.

A SessionStart hook in kit. A project picks the my method with an import
line `@~/.claude/methods/my.md` in its CLAUDE.md and two enabledPlugins keys
in its .claude/settings.json; the tutor method with the import line only.
This script reads, never writes, and checks that the parts agree:

- the import of my with the my or superpowers plugin off;
- an import of my or tutor that the user has not approved, or declined;
- the my or superpowers plugin on in a project that does not import my;
- more than one method import;
- an input file that cannot be read.

Inputs: the project root (CLAUDE_PROJECT_DIR, else the git top level of the
current directory, else the current directory); the import lines in the
root's CLAUDE.md and CLAUDE.local.md; enabledPlugins from
$HOME/.claude/settings.json, <root>/.claude/settings.json and
<root>/.claude/settings.local.json, a later file winning per key; the
approval flags of the root in $HOME/.claude.json. A key no file names counts
as on for superpowers@synced and as off for my@claude-setup and
kit@claude-setup.

Prints nothing when all is well, else one JSON object with the warnings in
both systemMessage and additionalContext, cut to 2,000 characters. Always
exits 0, so it never blocks a session.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

IMPORT = re.compile(r"^@~/\.claude/methods/([a-z0-9-]+)\.md\s*$")
MY = "my@claude-setup"
SUPERPOWERS = "superpowers@synced"
DEFAULTS = {SUPERPOWERS: True, MY: False, "kit@claude-setup": False}
LIMIT = 2000


def project_root():
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env)
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=5)
        if top.returncode == 0 and top.stdout.strip():
            return Path(top.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return Path.cwd()


def method_imports(root):
    names = []
    for name in ("CLAUDE.md", "CLAUDE.local.md"):
        try:
            text = (root / name).read_text(errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            match = IMPORT.match(line)
            if match:
                names.append(match.group(1))
    return names


def unreadable(path, errors):
    errors.append(f"method guard could not read {path}")


def read_json(path, errors):
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        data = None
    if not isinstance(data, dict):
        unreadable(path, errors)
        return None
    return data


def enabled_plugins(home, root, errors):
    plugins = dict(DEFAULTS)
    for path in (home / ".claude" / "settings.json",
                 root / ".claude" / "settings.json",
                 root / ".claude" / "settings.local.json"):
        data = read_json(path, errors)
        if data is None:
            continue
        enabled = data.get("enabledPlugins", {})
        if not isinstance(enabled, dict):
            unreadable(path, errors)
            continue
        plugins.update(enabled)
    return plugins


def approval(home, root, errors):
    """Return (approved, shown) for the root, or None when unreadable."""
    data = read_json(home / ".claude.json", errors)
    if data is None:
        return None
    projects = data.get("projects")
    entry = projects.get(str(root)) if isinstance(projects, dict) else None
    if not isinstance(entry, dict):
        return (False, False)
    return (entry.get("hasClaudeMdExternalIncludesApproved") is True,
            entry.get("hasClaudeMdExternalIncludesWarningShown") is True)


def warnings(root, imports, plugins, approved, errors):
    out = list(errors)
    if len(imports) > 1:
        out.append("method guard: this project imports more than one method "
                   f"file: {', '.join(imports)}. Keep one.")
    if "my" in imports:
        lines = [f'"{key}": true' for key in (MY, SUPERPOWERS)
                 if plugins.get(key) is not True]
        if lines:
            out.append("method guard: this project imports the my method, but "
                       "its plugins are off. Add to .claude/settings.json under "
                       f"enabledPlugins: {', '.join(lines)}. Or run /kit:setup my.")
    if approved is not None and not approved[0]:
        for name in dict.fromkeys(n for n in imports if n in ("my", "tutor")):
            if approved[1]:
                out.append(
                    f"method guard: the {name} method import was declined "
                    "earlier, so its rules are not loaded and Claude Code will "
                    f"not ask again. Read ~/.claude/methods/{name}.md before "
                    "your first reply. To be asked again, set "
                    f'projects["{root}"].hasClaudeMdExternalIncludesWarningShown '
                    "to false in ~/.claude.json while no session runs in this "
                    "directory, then start a new interactive session here.")
            else:
                out.append(
                    f"method guard: the {name} method import is not approved, "
                    "so its rules are not loaded. Read "
                    f"~/.claude/methods/{name}.md before your first reply, and "
                    "ask the user to approve the import (start a new "
                    "interactive session in this directory).")
    if "my" not in imports:
        on = [key for key in (MY, SUPERPOWERS) if plugins.get(key) is True]
        if on:
            lines = ", ".join(f'"{key}": false' for key in on)
            out.append("method guard: this project does not import the my "
                       f"method, but these plugins are on: {', '.join(on)}. To "
                       "turn them off, add to .claude/settings.json under "
                       f"enabledPlugins: {lines}.")
    return out


def main():
    home = Path(os.environ.get("HOME") or Path.home())
    root = project_root()
    errors = []
    imports = method_imports(root)
    plugins = enabled_plugins(home, root, errors)
    approved = approval(home, root, errors)
    found = warnings(root, imports, plugins, approved, errors)
    if not found:
        return 0
    text = "\n".join(found)[:LIMIT]
    print(json.dumps({"systemMessage": text, "hookSpecificOutput": {
        "hookEventName": "SessionStart", "additionalContext": text}}))
    return 0


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
