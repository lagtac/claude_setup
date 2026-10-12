"""Integration test: two simulated auto runs in one repository.

Run from plugins/my: python3 -m unittest discover tests

The test plays the parts that the my:handoff stages play, but calls only the
real scripts (handoff-lock.py, handoff-state.py, git-fold-fixups.py) and git,
with bin/ first on PATH. Two runs, a and b, change different functions of one
file. Whichever order the merges and checks come in, b's first merge refuses
because main gained code that b's checks never saw, b's merge after a rebase
lands, and every hash cited in a `done` mark is on main.
"""

import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin"
APP = "def alpha():\n    return 1\n" + "\n" * 10 + "def beta():\n    return 2\n"
BODIES = {"alpha": ("return 1", "return 'alpha'"), "beta": ("return 2", "return 'beta'")}
# The commit form of D4, with the message passed as an argument (plan, Decision 10).
LOCKED_COMMIT = 'm=$1; shift; git add -- "$@" && git commit -q -m "$m" -- "$@"'


def clean_env():
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_EDITOR"] = "false"
    env["PATH"] = f"{BIN}{os.pathsep}{env.get('PATH', '')}"
    return env


def sh(cwd, *args):
    return subprocess.run(list(args), cwd=cwd, env=clean_env(), capture_output=True,
                          text=True, timeout=60)


def git(cwd, *args):
    result = sh(cwd, "git", *args)
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout.strip()


def spec_path(slug):
    return f"docs/plans/2026-10-12-{slug}-spec.md"


class ParallelRunsTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.tmp = Path(folder.name)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "user.email", "test@example.com")
        (self.repo / "app.py").write_text(APP)
        (self.repo / ".gitignore").write_text("__pycache__/\n")
        (self.repo / "docs" / "plans").mkdir(parents=True)
        for slug in ("a", "b"):
            (self.repo / spec_path(slug)).write_text(
                f"# Spec {slug}\n\n**Status:** approved, 2026-10-12. Ready.\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-q", "-m", "root")
        for slug in ("a", "b"):
            (self.repo / spec_path(slug)).write_text(
                f"# Spec {slug}\n\n**Status:** approved, 2026-10-12. Ready to build.\n")
            git(self.repo, "commit", "-q", "-am", f"docs(plans): spec for {slug}")

    # The helpers, one per stage action.

    def state(self, *args):
        return sh(self.repo, "handoff-state.py", *args)

    def set(self, slug, *pairs):
        result = self.state("set", slug, *pairs)
        self.assertEqual(result.returncode, 0, result.stderr)

    def start_result(self, slug):
        return sh(self.repo, "handoff-lock.py", "main", "--", "handoff-state.py", "start",
                  slug, "--max", "2", f"spec={spec_path(slug)}",
                  f"task_doc={spec_path(slug)}", "next=code")

    def start(self, slug):
        result = self.start_result(slug)
        self.assertEqual(result.returncode, 0, result.stderr)

    def worktree(self, slug):
        return self.tmp / f"wt-{slug}"

    def build(self, slug, func):
        wt = self.worktree(slug)
        git(self.repo, "worktree", "add", "-q", str(wt), "-b", f"feat/{slug}")
        old, new = BODIES[func]
        app = wt / "app.py"
        app.write_text(app.read_text().replace(old, new))
        git(wt, "commit", "-q", "-am", f"feat({slug}): change {func}")
        self.set(slug, f"branch=feat/{slug}", f"worktree={wt}")

    def checks_pass(self, slug):
        result = sh(self.worktree(slug), "python3", "-c", "import app")
        self.assertEqual(result.returncode, 0, result.stderr)
        base = git(self.repo, "merge-base", "main", f"feat/{slug}")
        self.set(slug, f"checked_base={base}", "next=merge-retry")

    def merge(self, slug):
        return sh(self.repo, "handoff-lock.py", "main", "--", "handoff-state.py", "merge",
                  slug, "-m", f"feat({slug}): {slug}")

    def retry(self, slug):
        git(self.worktree(slug), "rebase", "-q", "main")
        self.checks_pass(slug)
        self.set(slug, "merge_retries=1")

    def on_main(self, short):
        return sh(self.repo, "git", "merge-base", "--is-ancestor", short, "main").returncode == 0

    def done(self, slug, short):
        path = spec_path(slug)
        spec = self.repo / path
        spec.write_text(re.sub(r"\*\*Status:\*\*.*",
                               f"**Status:** done, 2026-10-12. Shipped in {short}.",
                               spec.read_text()))
        result = sh(self.repo, "handoff-lock.py", "main", "--", "sh", "-c", LOCKED_COMMIT,
                    "sh", f"docs(plans): mark {slug} done", path)
        self.assertEqual(result.returncode, 0, result.stderr)

    def fold(self, *args):
        return sh(self.repo, "git-fold-fixups.py", *args)

    def finish(self, slug):
        result = self.merge(slug)
        self.assertEqual(result.returncode, 0, result.stderr)
        git(self.repo, "worktree", "remove", str(self.worktree(slug)))
        self.done(slug, result.stdout.strip())
        self.set(slug, "next=finished")

    def assert_citations_on_main(self):
        cited = re.findall(r"Shipped in ([0-9a-f]{7,})",
                           git(self.repo, "grep", "-h", "Shipped in", "--", "docs/"))
        self.assertEqual(len(cited), 2)
        for short in cited:
            self.assertTrue(self.on_main(short), short)
        app = (self.repo / "app.py").read_text()
        self.assertIn("return 'alpha'", app)
        self.assertIn("return 'beta'", app)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")
        # A fixup of a's spec now spans b's cited squash commit: D6 refuses it.
        spec_a = git(self.repo, "log", "--diff-filter=M", "--format=%H", "-1",
                     "--grep", "^docs(plans): spec for a$", "--", spec_path("a"))
        result = self.fold("check", spec_a)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("is cited in", result.stderr)

    # The two orders.

    def test_a_merges_after_b_checks(self):
        self.start("a")
        self.start("b")
        self.assertIn("2 auto runs are live (a, b)", self.start_result("c").stderr)
        self.build("a", "alpha")
        self.build("b", "beta")
        self.checks_pass("a")
        self.checks_pass("b")
        self.finish("a")
        self.assertEqual(self.merge("b").returncode, 4)
        self.retry("b")
        self.finish("b")
        self.assert_citations_on_main()

    def test_a_merges_before_b_checks(self):
        self.start("a")
        self.start("b")
        self.build("a", "alpha")
        self.build("b", "beta")
        self.checks_pass("a")
        self.finish("a")
        self.checks_pass("b")
        self.assertEqual(self.merge("b").returncode, 4)
        self.retry("b")
        self.finish("b")
        self.assert_citations_on_main()


if __name__ == "__main__":
    unittest.main()
