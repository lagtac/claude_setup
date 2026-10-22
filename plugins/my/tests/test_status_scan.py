"""Tests for bin/status-scan.py.

Run from plugins/my: python3 -m unittest discover tests

Each test builds a throwaway repository in a temporary directory, with `main`
checked out. The script runs there as a subprocess. Git runs without the
user's or the system's config, so a hook path or other setting of the machine
cannot change a result.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "status-scan.py"
LONG_A = "first long line of the change"
LONG_B = "second long line of the change"


def clean_env(extra={}):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_EDITOR"] = "false"
    env.update(extra)
    return env


def git(repo, *args, check=True):
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        env=clean_env(),
        capture_output=True,
        text=True,
        timeout=30,
    )
    if check and result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout.strip()


def run(cwd, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd,
        env=clean_env(),
        capture_output=True,
        text=True,
        timeout=120,
    )


def make_repo(tmp):
    repo = Path(tmp) / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "user.email", "test@example.com")
    commit(repo, "root", {"root.md": "root\n"})
    return repo


def commit(repo, subject, files={}):
    for name, text in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        git(repo, "add", name)
    git(repo, "commit", "-q", "--allow-empty", "-m", subject)
    return git(repo, "rev-parse", "HEAD")


def block(stdout, name):
    """The lines of one block, split on tabs; [] for `none`."""
    lines = stdout.splitlines()
    start = lines.index(f"== {name}") + 1
    rows = []
    for line in lines[start:]:
        if line.startswith("== "):
            break
        rows.append(line)
    if rows == ["none"]:
        return []
    return [row.split("\t") for row in rows]


class ScanTestCase(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.tmp = Path(folder.name)
        self.repo = make_repo(self.tmp)

    def scan(self, cwd=None):
        result = run(cwd or self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def roadmap(self, text):
        commit(self.repo, "docs: roadmap", {"ROADMAP.md": text})

    def branch(self, name, subject, files):
        git(self.repo, "switch", "-q", "-c", name)
        commit(self.repo, subject, files)
        git(self.repo, "switch", "-q", "main")


class RoadmapTest(ScanTestCase):
    def test_bullet_rows_skip_shipped(self):
        self.roadmap("# Roadmap\n\n"
                     "- 💭 **A** — x\n"
                     "- ✅ **B** — y\n"
                     "- 📋 **C** — [spec](docs/plans/c-spec.md)\n")
        rows = block(self.scan(), "roadmap")
        self.assertEqual([r[:4] for r in rows],
                         [["💭", "-", "A", "-"],
                          ["📋", "-", "C", "docs/plans/c-spec.md"]])
        self.assertEqual(rows[0][4], "- 💭 **A** — x")

    def test_bullet_rows_keep_number(self):
        self.roadmap("# Roadmap\n\n"
                     "- 💭 12 **A** — x\n"
                     "- 🚧 12b **B** — y\n"
                     "- ✅ 13 **C** — z\n")
        rows = block(self.scan(), "roadmap")
        self.assertEqual([r[:4] for r in rows],
                         [["💭", "12", "A", "-"], ["🚧", "12b", "B", "-"]])
        self.assertEqual(rows[0][4], "- 💭 12 **A** — x")

    def test_table_rows_keep_number(self):
        self.roadmap("# Roadmap\n\n"
                     "| # | Row | Status | Links |\n"
                     "| --- | --- | --- | --- |\n"
                     "| 3 | **Choose** — y. Waits for row 1. | 🚧 | — |\n"
                     "| 4 | **Shipped** — z. | ✅ | — |\n")
        rows = block(self.scan(), "roadmap")
        self.assertEqual([r[:4] for r in rows], [["🚧", "3", "Choose", "-"]])
        self.assertIn("Waits for row 1.", rows[0][4])

    def test_bullet_row_continuation_joined(self):
        self.roadmap("# Roadmap\n\n- 💭 **A** — first line\n  Waits for B.\n\nText.\n")
        self.assertEqual(block(self.scan(), "roadmap")[0][4],
                         "- 💭 **A** — first line Waits for B.")

    def test_order_copied_or_none(self):
        out_without = None
        self.roadmap("# Roadmap\n\n- 💭 **A** — x\n")
        out_without = self.scan()
        self.roadmap("# Roadmap\n\n## Order of work\n\n"
                     "- **1 and 2, then 3.** reason\n\n## Rows\n\n- 💭 **A** — x\n")
        out_with = self.scan()
        self.assertEqual(block(out_with, "order"), [["- **1 and 2, then 3.** reason"]])
        self.assertIn("== order\nnone", out_without)

    def test_missing_roadmap_is_none(self):
        out = self.scan()
        self.assertIn("== roadmap\nnone", out)
        self.assertIn("== order\nnone", out)


class DocsTest(ScanTestCase):
    def test_docs_status_filter(self):
        commit(self.repo, "docs: plans", {
            "docs/plans/a-spec.md": "# A\n\n**Status:** draft, 2026-10-12. Waiting.\n",
            "docs/plans/b-spec.md": "# B\n\n**Status:** done, 2026-10-11. Shipped in abc.\n",
            "docs/plans/b-spec-review.md":
                "# Review\n\n**Status:** review of b-spec.md, 2026-10-11. Answered.\n",
            "docs/plans/c.md": "# C\n\nNo status here.\n",
        })
        self.assertEqual(block(self.scan(), "docs"),
                         [["draft", "2026-10-12", "docs/plans/a-spec.md"],
                          ["no-status", "-", "docs/plans/c.md"]])

    def test_answered_spike_is_not_open(self):
        commit(self.repo, "docs: spike", {
            "docs/plans/2026-10-18-fonts-spike.md":
                "# Fonts\n\n**Status:** answered, 2026-10-18. Yes, with a bundled font.\n",
        })
        self.assertNotIn("fonts-spike.md", self.scan())


class CheckoutTest(ScanTestCase):
    def test_fixup_lists_target(self):
        spec = commit(self.repo, "docs: spec", {"spec.md": "spec\n"})
        fixup = commit(self.repo, "fixup! docs: spec", {"spec.md": "spec 2\n"})
        self.assertEqual(block(self.scan(), "checkout"),
                         [["fixup", fixup, spec, "docs: spec"]])

    def test_dirty_path_listed(self):
        (self.repo / "notes.md").write_text("notes\n")
        self.assertIn(["dirty", "notes.md"], block(self.scan(), "checkout"))

    def test_worktree_side_rename_lists_one_path(self):
        commit(self.repo, "docs: tracked", {"tracked.txt": "tracked\n"})
        (self.repo / "tracked.txt").rename(self.repo / "renamed.txt")
        git(self.repo, "add", "-N", "renamed.txt")
        dirty = [row for row in block(self.scan(), "checkout") if row[0] == "dirty"]
        self.assertIn(["dirty", "renamed.txt"], dirty)
        self.assertNotIn(["dirty", "cked.txt"], dirty)


class WorktreeTest(ScanTestCase):
    def test_worktree_ahead_and_dirty(self):
        wt = self.tmp / "wt"
        git(self.repo, "worktree", "add", "-q", str(wt), "-b", "feat/x")
        commit(wt, "feat: one", {"x.py": "x = 1\n"})
        commit(wt, "feat: two", {"x.py": "x = 2\n"})
        (wt / "x.py").write_text("x = 3\n")
        self.assertEqual(block(self.scan(), "worktrees"),
                         [[str(wt), "feat/x", "2", "dirty"]])


class BranchTest(ScanTestCase):
    def test_squash_merged_branch_hidden(self):
        self.branch("feat/y", "feat: y", {"y.py": f"{LONG_A}\n{LONG_B}\n"})
        commit(self.repo, "feat: y (squash)", {"y.py": f"{LONG_A}\n{LONG_B}\n"})
        self.assertEqual(block(self.scan(), "branches"), [])

    def test_squash_merged_then_edited_hidden(self):
        self.branch("feat/y", "feat: y", {"y.py": f"{LONG_A}\n{LONG_B}\n"})
        commit(self.repo, "feat: y (squash)", {"y.py": f"{LONG_A}\n{LONG_B}\n"})
        commit(self.repo, "refactor: y", {"y.py": "a completely rewritten body\n"})
        self.assertEqual(block(self.scan(), "branches"), [])

    def test_delete_only_branch_listed(self):
        commit(self.repo, "feat: base", {"d.py": f"{LONG_A}\n{LONG_B}\nkeep\n"})
        self.branch("feat/d", "feat: d", {"d.py": "keep\n"})
        self.assertEqual(block(self.scan(), "branches"),
                         [["maybe-unfinished", "feat/d", "2", "feat: d"]])

    def test_unmerged_branch_listed(self):
        self.branch("feat/z", "feat: z", {"z.py": f"{LONG_A}\n{LONG_B}\n"})
        self.assertEqual(block(self.scan(), "branches"),
                         [["maybe-unfinished", "feat/z", "2", "feat: z"]])

    def test_orphan_branch_compared_with_all_of_main(self):
        commit(self.repo, "feat: y", {"y.py": f"{LONG_A}\n{LONG_B}\n"})
        git(self.repo, "switch", "-q", "--orphan", "backup/old")
        commit(self.repo, "feat: y (old history)", {"y.py": f"{LONG_A}\n{LONG_B}\n"})
        git(self.repo, "switch", "-q", "-f", "main")
        self.branch("feat/z", "feat: z", {"z.py": f"{LONG_A} z\n{LONG_B} z\n"})
        self.assertEqual(block(self.scan(), "branches"),
                         [["maybe-unfinished", "feat/z", "2", "feat: z"]])

    def test_tag_with_branch_name(self):
        self.branch("feat/z", "feat: z", {"z.py": f"{LONG_A}\n{LONG_B}\n"})
        git(self.repo, "tag", "feat/z", "main")
        self.assertEqual(block(self.scan(), "branches"),
                         [["maybe-unfinished", "feat/z", "2", "feat: z"]])

    def test_short_lines_ignored(self):
        self.branch("feat/s", "feat: s", {"s.py": "}\nreturn\n"})
        self.assertEqual(block(self.scan(), "branches"), [])

    def test_branch_cap(self):
        for n in range(31):
            self.branch(f"feat/b{n}", f"feat: b{n}", {f"b{n}.py": f"{LONG_A} {n}\n"})
        rows = block(self.scan(), "branches")
        self.assertEqual(len(rows), 31)
        self.assertEqual(rows[-1], ["skipped", "1"])


class RunsTest(ScanTestCase):
    def state(self, slug, text):
        folder = self.repo / ".git" / "my-handoff"
        folder.mkdir(exist_ok=True)
        (folder / f"{slug}.json").write_text(text)

    def test_runs_fallback_hides_finished(self):
        self.state("a", '{"next": "code", "branch": "feat/a", "stopped": ""}')
        self.state("b", '{"next": "finished", "branch": "feat/b"}')
        self.assertEqual(block(self.scan(), "runs"), [["a", "-", "code", "-", "feat/a", "auto"]])

    def test_runs_block_shows_mode(self):
        self.state("a", '{"next": "code", "slot": "1", "mode": "supervised"}')
        self.state("b", '{"next": "review", "slot": "2"}')
        self.assertEqual(block(self.scan(), "runs"), [
            ["a", "1", "code", "-", "-", "supervised"],
            ["b", "2", "review", "-", "-", "auto"]])

    def test_runs_fallback_reads_mode_with_auto_by_default(self):
        # The fallback runs only when `handoff-state.py live` exits 2. The scan
        # finds that script next to itself, so a copy runs beside a stub.
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        shutil.copy(SCRIPT, bin_dir / "status-scan.py")
        (bin_dir / "handoff-state.py").write_text(
            "import sys\n"
            "if sys.argv[1:] == ['queue', 'show']:\n"
            "    print('none')\n"
            "    sys.exit(0)\n"
            "sys.exit(2)\n")
        self.state("a", '{"next": "code", "mode": "supervised"}')
        self.state("b", '{"next": "code", "branch": "feat/b"}')
        result = subprocess.run([sys.executable, str(bin_dir / "status-scan.py")],
                                cwd=self.repo, env=clean_env(), capture_output=True,
                                text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(block(result.stdout, "runs"), [
            ["a", "-", "code", "-", "-", "supervised"],
            ["b", "-", "code", "-", "feat/b", "auto"]])

    def test_bad_state_file_is_error_line(self):
        self.state("c", "{not json")
        result = run(self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(block(result.stdout, "runs")[0][0], "error")


class QueueTest(ScanTestCase):
    def setUp(self):
        super().setUp()
        self.specs = {slug: f"docs/plans/2026-10-13-{slug}-spec.md" for slug in "abc"}
        commit(self.repo, "docs(plans): specs",
               {path: f"spec {slug}\n" for slug, path in self.specs.items()})

    def entry(self, slug, row, state, after=(), reason=""):
        return {"row": row, "slug": slug, "spec": self.specs[slug], "stage": "code",
                "after": list(after), "exclusive": False,
                "spec_hash": git(self.repo, "hash-object", self.specs[slug]),
                "state": state, "reason": reason}

    def write_queue(self, text):
        folder = self.repo / ".git" / "my-handoff" / "queue"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "rows.json").write_text(text)

    def test_no_queue_is_none(self):
        self.assertEqual(block(self.scan(), "queue"), [])

    def test_queue_block_comes_after_runs_and_before_branches(self):
        names = [l[3:] for l in self.scan().splitlines() if l.startswith("== ")]
        self.assertEqual(names[names.index("runs"):], ["runs", "queue", "branches"])

    def test_show_line_then_waiting_and_skipped_entries(self):
        folder = self.repo / ".git" / "my-handoff"
        folder.mkdir()
        (folder / "a.json").write_text('{"next": "code", "slot": "1"}')
        self.write_queue(json.dumps([
            self.entry("a", "9", "started"),
            self.entry("b", "12b", "waiting", after=["a"]),
            self.entry("c", "3", "skipped", reason="spec changed since the call")]))
        self.assertEqual(block(self.scan(), "queue"), [
            ["waits", "b", "a"],
            ["waiting", "12b", "b", "a", "-"],
            ["skipped", "3", "c", "-", "spec changed since the call"]])

    def test_unreadable_queue_is_an_error_line(self):
        self.write_queue("{")
        result = run(self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(block(result.stdout, "queue")[0][0], "error")

    def test_queue_folder_is_not_a_run(self):
        self.write_queue(json.dumps([self.entry("a", "9", "waiting")]))
        self.assertEqual(block(self.scan(), "runs"), [])


class ExitTest(ScanTestCase):
    def test_outside_repo_exits_2(self):
        outside = self.tmp / "outside"
        outside.mkdir()
        result = run(outside)
        self.assertEqual(result.returncode, 2)
        self.assertIn("not inside a git repository", result.stderr)


if __name__ == "__main__":
    unittest.main()
