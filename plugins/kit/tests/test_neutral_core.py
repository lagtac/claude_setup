"""Tests that the global core and the kit plugin name no method.

Run from plugins/kit: python3 -m unittest discover tests

global/CLAUDE.md holds only rules that hold under any method; the rules of
a method live in its plugin's forced output style. kit is on in every
project, so its files must not point at docs/plans, superpowers or a my
skill either.
"""

import json
import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CORE = REPO / "global" / "CLAUDE.md"
ENGINEERING = REPO / "global" / "rules" / "engineering.md"
KIT = REPO / "plugins" / "kit"

METHOD_HEADINGS = [
    "Learning workspaces", "Superpowers Integration", "Pick the route",
    "Spec → Plan two-artifact flow", "No silent reinterpretation of approved decisions",
    "Code Review Routing", "UI Design", "Git Workflow", "One feature, four commits on `main`",
    "Splitting scope before branching", "When to use worktrees", "When NOT to use worktrees",
    "Finishing a worktree branch", "Assessing branch redundancy",
    "When to open an MR (optional)", "Planning Standards", "Trade-Off Analysis",
    "Risk Awareness", "Test Standards", "Plan Output Format"]
# The skills, agents and command of the my plugin (spec, Plugins table).
MY_NAMES = ["handoff", "soundness-review", "status", "spec-review", "architect",
            "roadmap-management", "clean-plans", "changelog-management",
            "code-reviewer", "spec-reviewer", "summarizer", "summarize",
            "design-system"]
# my names distinct enough to find without the prefix.
MY_BARE = [n for n in MY_NAMES if "-" in n and n not in ("code-reviewer",)]
# A my name counts only as a whole name, so design:design-system is no hit.
MY_PATTERNS = {token: re.compile(r"(?<![A-Za-z0-9:-])" + re.escape(token)
                                 + r"(?![A-Za-z0-9-])")
               for token in [f"my:{n}" for n in MY_NAMES] + MY_BARE}

OLD_PATHS = (r"methods/(my|tutor)\.md|global/methods|docs-layout|plan-format"
             r"|global/output-styles|\.claude/output-styles|kit:tutor")


def names_in(text):
    return [token for token, pattern in MY_PATTERNS.items()
            if pattern.search(text)]


def methods():
    """The marketplace entries whose category is method, by name."""
    data = json.loads((REPO / ".claude-plugin" / "marketplace.json").read_text())
    return {e["name"]: e for e in data["plugins"] if e.get("category") == "method"}


def style(name):
    """A method style's frontmatter, as a dict of strings, and its body."""
    text = (REPO / "plugins" / name / "output-styles" / f"{name}.md").read_text()
    _, front, body = text.split("---\n", 2)
    meta = dict(line.split(": ", 1) for line in front.splitlines() if line.strip())
    return meta, body


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

    def test_core_holds_plain_rules(self):
        core = CORE.read_text()
        self.assertIn("**One idea per sentence.**", core)
        self.assertIn("Check before sending", headings(core))
        self.assertNotIn("output-styles/", core)

    def test_core_keeps_neutral_sections(self):
        self.assertTrue({"Communication", "Critical Thinking", "Design work", "HTTP Requests"}
                        <= headings(CORE.read_text()))

    def test_core_has_no_engineering_sections(self):
        core = CORE.read_text()
        for heading in ["Code", "Engineering standards", "Mandatory Exploration",
                        "Reference Sweep", "Simplicity Rules"]:
            with self.subTest(heading=heading):
                self.assertNotIn(heading, headings(core))
        self.assertNotIn("Verify against ground truth", core)

    def test_core_precedence_names_rules_and_style(self):
        core = " ".join(CORE.read_text().split())
        self.assertIn("the rule files in `~/.claude/rules/`, and the active method's rules "
                      "(the output style its plugin forces on)", core)

    def test_engineering_rules_are_path_scoped(self):
        text = ENGINEERING.read_text()
        self.assertTrue(text.startswith(
            '---\npaths:\n'
            '  - "**/*.{py,js,ts,jsx,tsx,mjs,cjs,vue,php,sh,go,rs,java,rb,lua,sql,css,scss,html}"\n'
            '  - "**/{package.json,composer.json,pyproject.toml,Dockerfile}"\n'
            '  - "**/docs/plans/*.md"\n---\n'))
        self.assertTrue({"Code", "Engineering standards", "Mandatory Exploration",
                         "Reference Sweep", "Simplicity Rules"} <= headings(text))
        self.assertIn("**Verify against ground truth, not the artifact.**", text)

    def test_tutor_moved_out_of_kit(self):
        self.assertFalse((KIT / "skills" / "tutor").exists())
        for name in ["SKILL.md", "method.md", "templates.md"]:
            with self.subTest(name=name):
                self.assertTrue((REPO / "plugins/tutor/skills/tutor" / name).is_file())

    def test_tutor_style_and_skill_use_new_names(self):
        body = style("tutor")[1]
        skill = (REPO / "plugins/tutor/skills/tutor/SKILL.md").read_text()
        method = (REPO / "plugins/tutor/skills/tutor/method.md").read_text()
        for text in (body, skill, method):
            self.assertNotIn("kit:tutor", text)
        self.assertIn("tutor:tutor", body)
        self.assertNotIn("plain.md", body)
        self.assertNotIn("output style is not active", body)
        self.assertIn("Exceptions to the core and to `~/.claude/rules/engineering.md`: Verify "
                      "against ground truth, Mandatory Exploration, Reference Sweep and Simplicity "
                      "Rules do not apply in a learning workspace.", " ".join(body.split()))
        self.assertNotIn("outputStyle", skill)
        self.assertNotIn("~/.claude/methods", skill)
        self.assertIn("/kit:setup tutor", skill)

    def test_global_method_folders_are_gone(self):
        for rel in ["global/methods", "global/output-styles"]:
            with self.subTest(path=rel):
                self.assertFalse((REPO / rel).exists())

    def test_the_three_methods(self):
        self.assertEqual(set(methods()), {"my", "tutor", "sp"})

    def test_no_file_names_a_moved_path(self):
        r = subprocess.run(["git", "-C", str(REPO), "grep", "-n", "-E", OLD_PATHS, "--", ".",
                            ":!docs/plans", ":!docs/reports", ":!CHANGELOG.md", ":!ROADMAP.md",
                            ":!plugins/kit/tests", ":!plugins/kit/hooks/method-guard.py"],
                           capture_output=True, text=True)
        self.assertEqual(r.stdout, "")

    def test_core_sends_design_work_to_router(self):
        core = CORE.read_text()
        self.assertIn("Design work", headings(core))
        self.assertIn("invoke `kit:design-router`", core)

    def test_method_styles_have_forced_frontmatter(self):
        self.assertIn("my", methods())   # the loop below asserts nothing while methods() is empty
        for name in methods():
            with self.subTest(method=name):
                meta, _ = style(name)
                self.assertEqual(set(meta), {"name", "description", "force-for-plugin",
                                             "keep-coding-instructions"})
                self.assertEqual(meta["name"], name)
                self.assertEqual(meta["force-for-plugin"], "true")
                self.assertEqual(meta["keep-coding-instructions"], "true")
                self.assertTrue(meta["description"])

    def test_method_manifests_match_marketplace(self):
        self.assertIn("my", methods())
        for name, entry in methods().items():
            with self.subTest(method=name):
                self.assertEqual(entry["source"], f"./plugins/{name}")
                manifest = json.loads((REPO / "plugins" / name / ".claude-plugin"
                                       / "plugin.json").read_text())
                self.assertEqual(manifest["name"], name)
        self.assertEqual(json.loads((REPO / "plugins/my/.claude-plugin/plugin.json")
                                    .read_text())["dependencies"], ["superpowers@synced"])

    def test_no_applies_line_left(self):
        self.assertIn("my", methods())
        for name in methods():
            with self.subTest(method=name):
                self.assertNotIn("Applies only in projects whose", style(name)[1])

    def test_my_style_points_at_no_moved_file(self):
        body = style("my")[1]
        for token in ["docs-layout.md", "plan-format.md", "~/.claude/methods",
                      "That rule loads when", "importing this file", "names the method,",
                      "Mandatory Exploration (in the core)",
                      "Engineering standards in `~/.claude/CLAUDE.md`", "the core's"]:
            with self.subTest(token=token):
                self.assertNotIn(token, body)

    def test_old_rule_files_are_gone(self):
        for rel in ["global/methods/my.md", "global/rules/docs-layout.md",
                    "global/rules/plan-format.md"]:
            with self.subTest(path=rel):
                self.assertFalse((REPO / rel).exists())

    def test_whole_name_match(self):
        self.assertEqual(names_in("run design:design-system now"), [])
        self.assertEqual(names_in("use design-skills:design-systems"), [])
        self.assertEqual(names_in("run the design-system audit"), ["design-system"])
        self.assertIn("my:handoff", names_in("type /my:handoff run"))

    def test_kit_cites_no_method(self):
        tokens = ["docs/plans", "superpowers:", "global/CLAUDE.md"]
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
            with self.subTest(file=str(rel)):
                self.assertEqual(names_in(text), [])


if __name__ == "__main__":
    unittest.main()
