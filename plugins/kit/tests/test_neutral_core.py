"""Tests that the global core and the kit plugin name no method.

Run from plugins/kit: python3 -m unittest discover tests

global/CLAUDE.md holds only rules that hold under any method; the rules of
the my method live in global/methods/my.md. kit is on in every project, so
its files must not point at docs/plans, superpowers or a my skill either.
"""

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CORE = REPO / "global" / "CLAUDE.md"
KIT = REPO / "plugins" / "kit"

METHOD_HEADINGS = [
    "Learning workspaces", "Superpowers Integration", "Size the process to the change",
    "Spec → Plan two-artifact flow", "No silent reinterpretation of approved decisions",
    "Code Review Routing", "UI Design", "Git Workflow", "One feature, four commits on `main`",
    "Splitting scope before branching", "When to use worktrees", "When NOT to use worktrees",
    "Finishing a worktree branch", "Assessing branch redundancy",
    "When to open an MR (optional)", "Planning Standards", "Trade-Off Analysis",
    "Risk Awareness", "Test Standards", "Plan Output Format"]
APPLIES = ("Applies only in projects whose `CLAUDE.md` imports "
           "`~/.claude/methods/my.md`. Ignore it otherwise.")
# The skills, agents and command of the my plugin (spec, Plugins table).
MY_NAMES = ["handoff", "soundness-review", "status", "spec-review", "architect",
            "roadmap-management", "clean-plans", "changelog-management",
            "code-reviewer", "spec-reviewer", "summarizer", "summarize"]
# my names distinct enough to find without the prefix.
MY_BARE = [n for n in MY_NAMES if "-" in n and n not in ("code-reviewer",)]


def headings(text):
    return {line.lstrip("#").strip() for line in text.splitlines()
            if line.startswith("#")}


class NeutralCoreTest(unittest.TestCase):
    def test_core_names_no_method(self):
        core = CORE.read_text()
        for token in ["my:", "superpowers:", "docs/plans", "docs/reports"]:
            with self.subTest(token=token):
                self.assertNotIn(token, core)

    def test_core_has_no_method_heading(self):
        found = headings(CORE.read_text())
        for heading in METHOD_HEADINGS:
            with self.subTest(heading=heading):
                self.assertNotIn(heading, found)

    def test_core_has_engineering_standards(self):
        self.assertIn("Engineering standards", headings(CORE.read_text()))

    def test_method_files_exist(self):
        for name in ["my.md", "tutor.md"]:
            with self.subTest(name=name):
                self.assertTrue((REPO / "global" / "methods" / name).is_file())

    def test_lazy_rules_start_with_applies_line(self):
        for name in ["docs-layout.md", "plan-format.md"]:
            with self.subTest(name=name):
                lines = [l for l in (REPO / "global" / "rules" / name)
                         .read_text().splitlines() if l.strip()]
                if lines[0] == "---":  # skip the paths frontmatter
                    lines = lines[lines.index("---", 1) + 1:]
                self.assertTrue(lines[0].startswith("# "))
                self.assertEqual(lines[1], APPLIES)

    def test_kit_cites_no_method(self):
        tokens = (["docs/plans", "superpowers:", "global/CLAUDE.md"]
                  + [f"my:{n}" for n in MY_NAMES] + MY_BARE)
        for path in sorted(KIT.rglob("*")):
            rel = path.relative_to(KIT)
            if (path.is_symlink() or not path.is_file()
                    or rel.parts[0] == "tests"
                    or rel.parts[:2] == ("skills", "setup")
                    or "__pycache__" in rel.parts):
                continue
            text = path.read_text(errors="replace")
            for token in tokens:
                with self.subTest(file=str(rel), token=token):
                    self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
