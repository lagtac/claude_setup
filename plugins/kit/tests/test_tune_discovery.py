"""Tests for the file search in step 1 of tune-claude-instructions.

Run from plugins/kit: python3 -m unittest discover tests

The tests run the `find "$(pwd -P)"` commands that step 1 of the skill gives,
as the skill text gives them, on fixture folders. With a path, the skill puts
the absolute path in place of `$(pwd -P)`, and the tests do the same. Each
fixture folder has a space in its name, to catch an unquoted path.
"""

import re
import subprocess
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
SKILL = KIT / "skills" / "tune-claude-instructions" / "SKILL.md"
BLOCK = re.compile(r"```bash\n(.*?)```", re.S)
ROOT = 'find "$(pwd -P)" '


def search_commands():
    text = SKILL.read_text()
    step = text.split("### 1. Discover instruction files", 1)[1].split("### 2.", 1)[0]
    return [b for b in BLOCK.findall(step) if ROOT in b]


def run_search(cwd, path=None):
    found = set()
    for command in search_commands():
        if path:
            command = command.replace(ROOT, f'find "{path}" ')
        out = subprocess.run(["bash", "-c", command], cwd=cwd, capture_output=True,
                             text=True, check=True).stdout
        found.update(line for line in out.splitlines() if line)
    return found


def make(root, names):
    for name in names:
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text("# x\n")


DOT_CLAUDE = ["CLAUDE.md", "rules/own.md", "skills/own/SKILL.md",
              "plugins/cache/other/skills/theirs/SKILL.md",
              "projects/x/skills/session/SKILL.md"]


class DiscoveryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="tune discovery ")
        self.root = Path(self.tmp.name).resolve()

    def tearDown(self):
        self.tmp.cleanup()

    def test_step_one_has_a_search(self):
        self.assertTrue(search_commands())

    def test_project_search_finds_instruction_files(self):
        names = ["CLAUDE.md", "AGENTS.md", "global/CLAUDE.md", "global/rules/own.md",
                 "plugins/k/agents/a.md", "plugins/k/commands/c.md",
                 "plugins/k/skills/s/SKILL.md", "plugins/k/skills/s/references/r.md"]
        make(self.root, names)
        found = run_search(self.root)
        for name in names:
            self.assertIn(f"{self.root}/{name}", found)

    def test_dot_claude_path_skips_plugins_and_projects(self):
        home = self.root / ".claude"
        make(home, DOT_CLAUDE)
        found = run_search(self.root, str(home))
        self.assertIn(f"{home}/CLAUDE.md", found)
        self.assertIn(f"{home}/rules/own.md", found)
        self.assertIn(f"{home}/skills/own/SKILL.md", found)
        self.assertNotIn(f"{home}/plugins/cache/other/skills/theirs/SKILL.md", found)
        self.assertNotIn(f"{home}/projects/x/skills/session/SKILL.md", found)

    def test_search_from_inside_dot_claude_skips_plugins_and_projects(self):
        home = self.root / ".claude"
        make(home, DOT_CLAUDE)
        found = run_search(home)
        self.assertIn(f"{home}/skills/own/SKILL.md", found)
        self.assertNotIn(f"{home}/plugins/cache/other/skills/theirs/SKILL.md", found)
        self.assertNotIn(f"{home}/projects/x/skills/session/SKILL.md", found)


if __name__ == "__main__":
    unittest.main()
