"""Integration test: the queue of `/my:handoff auto rows`, end to end.

Run from plugins/my: python3 -m unittest discover tests

The test plays the parts that my:handoff plays, but calls only the real
scripts (handoff-lock.py, handoff-state.py) and git, with bin/ first on PATH.
Every queue write and every `pull` runs under `handoff-lock.py main`. A run
"finishes" with `handoff-state.py set <slug> next=finished stopped=`, as the
review stage's last sub-step does, and the refill is the next locked `pull`.
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin"


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


def spec(slug):
    return f"docs/plans/2026-10-13-{slug}-spec.md"


def entry(slug, after=(), exclusive=False):
    return {"row": slug, "spec": spec(slug), "stage": "code", "after": list(after),
            "exclusive": exclusive}


class RoadmapQueueTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.tmp = Path(folder.name)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "user.email", "test@example.com")
        (self.repo / "docs" / "plans").mkdir(parents=True)
        for slug in "abcef":
            (self.repo / spec(slug)).write_text(
                f"# Spec {slug}\n\n**Status:** approved, 2026-10-13. Ready.\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-q", "-m", "docs(plans): five specs")
        self.files = 0

    # The helpers, one per part that my:handoff plays.

    def locked(self, *args):
        return sh(self.repo, "handoff-lock.py", "main", "--", "handoff-state.py", *args)

    def add(self, *entries):
        self.files += 1
        path = self.tmp / f"entries-{self.files}.json"
        path.write_text(json.dumps(list(entries)))
        result = self.locked("queue", "add", "--file", str(path))
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def pull(self, n):
        result = self.locked("pull", "--max", str(n))
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def pulled(self, n):
        return [line.split("\t")[0] for line in self.pull(n).stdout.splitlines()]

    def finish(self, slug, stopped=""):
        result = sh(self.repo, "handoff-state.py", "set", slug, "next=finished",
                    f"stopped={stopped}")
        self.assertEqual(result.returncode, 0, result.stderr)

    def live(self, slug):
        result = sh(self.repo, "handoff-state.py", "set", slug, "next=code", "slot=9")
        self.assertEqual(result.returncode, 0, result.stderr)

    # The cases of the spec's Testing section.

    def test_three_rows_typed_dependent_first_run_one_at_a_time(self):
        self.add(entry("c", after=["b"]), entry("b", after=["a"]), entry("a"))
        self.assertEqual(self.pulled(1), ["a"])
        self.assertEqual(self.pulled(1), [])
        self.finish("a")
        self.assertEqual(self.pulled(1), ["b"])
        self.finish("b")
        self.assertEqual(self.pulled(1), ["c"])

    def test_after_gate_holds_a_row_until_its_blocker_finishes(self):
        self.add(entry("a"), entry("b", after=["a"]))
        self.assertEqual(self.pulled(2), ["a"])
        self.assertEqual(self.pulled(2), [])
        self.finish("a")
        self.assertEqual(self.pulled(2), ["b"])

    def test_ended_or_dropped_blocker_skips_the_rows_behind_it(self):
        self.add(entry("a"), entry("b", after=["a"]), entry("c", after=["b"]))
        self.pulled(1)
        self.finish("a", stopped="ended by the user")
        result = self.pull(1)
        self.assertEqual(result.stdout, "")
        self.assertIn("skipped: b: blocker a did not finish", result.stderr)
        self.assertIn("skipped: c: blocker b did not finish", result.stderr)
        self.add(entry("e"), entry("f", after=["e"]))
        self.assertEqual(self.locked("queue", "drop", "e").returncode, 0)
        result = self.pull(1)
        self.assertEqual(result.stdout, "")
        self.assertIn("skipped: f: blocker e did not finish", result.stderr)

    def test_changed_spec_is_skipped(self):
        self.add(entry("a"))
        (self.repo / spec("a")).write_text("edited after the call\n")
        result = self.pull(1)
        self.assertEqual(result.stdout, "")
        self.assertIn("skipped: a: spec changed since the call", result.stderr)

    def test_exclusive_row_waits_runs_alone_and_blocks_later_adds(self):
        self.live("x")
        self.add(entry("e", exclusive=True), entry("f"))
        self.assertEqual(self.pulled(2), [])
        self.finish("x")
        self.assertEqual(self.pulled(2), ["e"])
        self.add(entry("a"))
        self.assertEqual(self.pulled(2), [])
        self.finish("e")
        self.assertEqual(self.pulled(2), ["f", "a"])

    def test_concurrent_pulls_never_pass_the_cap(self):
        self.add(*(entry(s) for s in "abcef"))
        procs = [subprocess.Popen(["handoff-lock.py", "main", "--", "handoff-state.py",
                                   "pull", "--max", "2"],
                                  cwd=self.repo, env=clean_env(), stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True)
                 for _ in range(4)]
        outs = [proc.communicate(timeout=60)[0] for proc in procs]
        self.assertEqual([proc.returncode for proc in procs], [0, 0, 0, 0])
        started = [line.split("\t") for out in outs for line in out.splitlines()]
        self.assertEqual(len(started), 2)
        self.assertEqual(sorted(row[3] for row in started), ["1", "2"])

    def test_pull_inside_lock_main_does_not_wait_on_its_own_lock(self):
        self.add(entry("a"))
        result = sh(self.repo, "handoff-lock.py", "main", "--timeout", "5", "--",
                    "handoff-state.py", "pull", "--max", "1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split("\t")[0], "a")


if __name__ == "__main__":
    unittest.main()
