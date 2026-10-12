"""Tests for hooks/block-autorun-push.py.

Run from plugins/my: python3 -m unittest discover tests

Each test runs the script as a subprocess and feeds it the hook's JSON on
stdin, the way Claude Code calls a PreToolUse hook. MY_AUTORUN is set or
removed for each call, so the user's own environment cannot change a result.
"""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "hooks" / "block-autorun-push.py"


def guard(command, autorun="widget", tool="Bash", raw=None):
    env = {k: v for k, v in os.environ.items() if k != "MY_AUTORUN"}
    if autorun is not None:
        env["MY_AUTORUN"] = autorun
    stdin = raw if raw is not None else json.dumps(
        {"tool_name": tool, "tool_input": {"command": command}})
    return subprocess.run([sys.executable, str(SCRIPT)], input=stdin,
                          env=env, capture_output=True, text=True, timeout=10)


BLOCKED = [
    "git push", "git push origin main", "git -C /x push", "git -c a=b push",
    "cd /x && git push", "git --no-pager push", "git status; git push",
    "git status || git push", "true | git push", "git status\ngit push",
    "(cd /x && git push)", "FOO=1 git push", "/usr/bin/git push",
    'git push "unbalanced',
    "git add -A  # stage all\ngit push origin main", "curl http://x/#frag; git push",
    "for b in a b; do git push origin $b; done", "if true; then git push; fi",
    "if git push; then :; fi", "while git push; do :; done", "{ git push; }",
    "time git push", "! git push", "nohup git push", "command git push",
    "exec git push", "if false; then :; else git push; fi",
    "git --git-dir .git push", "git --work-tree . push", "git --namespace n push",
]
ALLOWED = [
    "git stash push", "echo push", "git status", 'git commit -m "never git push"',
    'git commit -m "a; git push"', "cat <<'EOF'\ngit push\nEOF",
    "cat <<-EOF\n\tgit push\n\tEOF\ngit status", 'echo "unbalanced',
    "ls # git push", "# git push later\ngit status", "git --git-dir .git status",
]


class GuardTest(unittest.TestCase):
    def test_blocks_a_push(self):
        for command in BLOCKED:
            with self.subTest(command=command):
                result = guard(command)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stderr.strip(),
                                 "Blocked: autonomous runs never push.")

    def test_monitor_push_is_blocked(self):
        self.assertEqual(guard("git push", tool="Monitor").returncode, 2)

    def test_allows_text_that_only_mentions_push(self):
        for command in ALLOWED:
            with self.subTest(command=command):
                self.assertEqual(guard(command).returncode, 0)

    def test_every_command_passes_without_the_variable(self):
        for command in BLOCKED + ALLOWED:
            with self.subTest(command=command):
                self.assertEqual(guard(command, autorun=None).returncode, 0)
                self.assertEqual(guard(command, autorun="").returncode, 0)

    def test_bad_json_passes_without_the_variable(self):
        self.assertEqual(guard("", autorun=None, raw="not json").returncode, 0)

    def test_hooks_json_runs_the_guard_for_bash_and_monitor(self):
        hooks = json.loads((SCRIPT.parent / "hooks.json").read_text())["hooks"]
        commands = [h["command"] for entry in hooks["PreToolUse"]
                    if entry["matcher"] == "Bash|Monitor" for h in entry["hooks"]]
        self.assertEqual(commands,
                         ['python3 "$CLAUDE_PLUGIN_ROOT/hooks/block-autorun-push.py"'])


if __name__ == "__main__":
    unittest.main()
