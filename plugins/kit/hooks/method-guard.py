#!/usr/bin/env python3
"""Warn at session start when a project's method is half set.

A SessionStart hook in kit. A method is a plugin whose forced output style
holds its rules; a folder's settings turn it on with its dependencies. This
script reads, never writes, and warns about:

- more than one method on, because Claude Code applies only the first style
  it loads;
- a method on with a dependency off;
- an old import line @~/.claude/methods/<m>.md left in CLAUDE.md or
  CLAUDE.local.md;
- an input file that cannot be read.

Inputs: the method list and each method's dependencies, from
`claude-method --methods` ($CLAUDE_PLUGIN_ROOT/bin/claude-method, else the
bin folder beside this script's folder); the project root
(CLAUDE_PROJECT_DIR, else the git top level of the current directory, else
the current directory); the import lines in the root's CLAUDE.md and
CLAUDE.local.md; enabledPlugins from $HOME/.claude/settings.json,
<root>/.claude/settings.json and <root>/.claude/settings.local.json, a later
file winning per key. A key no file names counts as on when it ends in
@synced, as off otherwise. If claude-method fails, the script prints that
one warning and judges nothing else.

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


def method_list():
    """Return ({method key: [dependency keys]}, None), or (None, reason)."""
    root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    script = (Path(root) if root else Path(__file__).resolve().parent.parent) \
        / "bin" / "claude-method"
    try:
        run = subprocess.run([sys.executable, str(script), "--methods"],
                             capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError) as err:
        return None, str(err)
    if run.returncode != 0:
        lines = [l for l in run.stderr.splitlines() if l.strip()]
        return None, lines[-1] if lines else f"exit {run.returncode}"
    try:
        data = json.loads(run.stdout)
    except ValueError as err:
        return None, str(err)
    if not isinstance(data, dict):
        return None, "not a JSON object"
    return data, None


def method_imports(root):
    """Return (file name, method) for each import line."""
    found = []
    for name in ("CLAUDE.md", "CLAUDE.local.md"):
        try:
            text = (root / name).read_text(errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            match = IMPORT.match(line)
            if match:
                found.append((name, match.group(1)))
    return found


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
    plugins = {}
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


def is_on(key, plugins):
    if key in plugins:
        return plugins[key] is True
    return key.endswith("@synced")


def short(key):
    return key.rsplit("@", 1)[0]


def warnings(methods, imports, plugins, errors):
    out = list(errors)
    on = sorted(key for key in methods if is_on(key, plugins))
    if len(on) > 1:
        out.append(f"method guard: more than one method is on: {', '.join(on)}. "
                   "Claude Code applies only the first style it loads. Keep one "
                   "with /kit:setup <method>.")
    for key in on:
        for dep in methods[key]:
            if not is_on(dep, plugins):
                out.append(f"method guard: the {short(key)} method is on, but its "
                           f"dependency {dep} is off. Run /kit:setup {short(key)}.")
    for name, method in imports:
        out.append(f"method guard: {name} still has the line "
                   f"@~/.claude/methods/{method}.md. Run /kit:setup {method}.")
    return out


def main():
    methods, reason = method_list()
    if methods is None:
        found = [f"method guard: claude-method --methods failed: {reason}"]
    else:
        home = Path(os.environ.get("HOME") or Path.home())
        root = project_root()
        errors = []
        plugins = enabled_plugins(home, root, errors)
        found = warnings(methods, method_imports(root), plugins, errors)
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
