"""Tests that skill and command text holds no bare $0, $1, ... placeholder.

Run from plugins/kit: python3 -m unittest discover tests

It reads every plugin in this repo, not only kit, so a skill keeps the check
when it moves between plugins. Supporting files and agents are left out:
they are read as files, and nothing fills their placeholders.

When Claude Code loads a skill or a command, it replaces $N with argument
number N, counting from zero, whenever that argument exists. A shell snippet
that uses "$1" for its own first argument then gets the user's second
argument instead: "/kit:git-squasher main --dry-run" turns the rebase script
into sed -i ... "--dry-run". ${1} is left alone, and the shell reads it the
same way.
"""

import re
import unittest
from pathlib import Path

PLUGINS = Path(__file__).resolve().parents[2]
BARE = re.compile(r"\$\d")


class PlaceholderTest(unittest.TestCase):
    def test_no_bare_positional_placeholder(self):
        files = (sorted(PLUGINS.glob("*/skills/*/SKILL.md"))
                 + sorted(PLUGINS.glob("*/commands/*.md")))
        self.assertTrue({p.relative_to(PLUGINS).parts[0] for p in files} - {"kit"})
        for path in files:
            for number, line in enumerate(path.read_text().splitlines(), 1):
                with self.subTest(file=str(path.relative_to(PLUGINS)), line=number):
                    self.assertIsNone(BARE.search(line), line.strip())


if __name__ == "__main__":
    unittest.main()
