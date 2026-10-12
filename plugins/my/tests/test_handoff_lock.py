"""Tests for bin/handoff-lock.py.

Run from plugins/my: python3 -m unittest discover tests

Each test builds a throwaway repository in a temporary directory, with the
branch `feat/widget` checked out in a worktree next to it. A holder takes a
lock by running `sleep` under the script; the test then runs a second command
under the same lock, or another one. Git runs without the user's or the
system's config.
"""

import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin"
LOCK = BIN / "handoff-lock.py"


def clean_env(extra={}):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_EDITOR"] = "false"
    env["PATH"] = f"{BIN}{os.pathsep}{env.get('PATH', '')}"
    env.update(extra)
    return env


def git(repo, *args, check=True):
    result = subprocess.run(["git", *args], cwd=repo, env=clean_env(),
                            capture_output=True, text=True, timeout=30)
    if check and result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout.strip()


def make_repo(tmp):
    repo = Path(tmp) / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "user.email", "test@example.com")
    (repo / "root.md").write_text("root\n")
    git(repo, "add", "root.md")
    git(repo, "commit", "-q", "-m", "root")
    return repo


class LockTestCase(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.tmp = Path(folder.name)
        self.repo = make_repo(self.tmp)
        self.worktree = self.tmp / "wt"
        git(self.repo, "worktree", "add", "-q", str(self.worktree), "-b", "feat/widget")
        self.marker = self.tmp / "ran"
        self.holders = 0

    def hold(self, name, cwd, seconds=30):
        """Start a holder of lock `name`, and return once it holds the lock."""
        self.holders += 1
        ready = self.tmp / f"ready-{self.holders}"
        holder = subprocess.Popen(
            [sys.executable, str(LOCK), name, "--", "sh", "-c",
             f'touch "$0"; exec sleep {seconds}', str(ready)],
            cwd=cwd, env=clean_env(), stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        self.addCleanup(holder.wait)
        self.addCleanup(holder.kill)
        deadline = time.monotonic() + 10
        while not ready.exists():
            if time.monotonic() > deadline or holder.poll() is not None:
                self.fail(f"holder of {name} never started")
            time.sleep(0.05)
        return holder

    def lock(self, cwd, *args, env={}):
        return subprocess.run([sys.executable, str(LOCK), *args], cwd=cwd,
                              env=clean_env(env), capture_output=True, text=True,
                              timeout=60)


class LockTest(LockTestCase):
    def test_second_holder_times_out_and_runs_nothing(self):
        self.hold("main", self.repo)
        result = self.lock(self.repo, "main", "--timeout", "0.5", "--", "touch", str(self.marker))
        self.assertEqual(result.returncode, 75)
        self.assertTrue(result.stderr.startswith("handoff-lock:"))
        self.assertFalse(self.marker.exists())

    def test_waiter_runs_after_the_holder_ends(self):
        holder = self.hold("main", self.repo, seconds=1)
        result = self.lock(self.repo, "main", "--timeout", "10", "--", "touch", str(self.marker))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.marker.exists())
        self.assertIsNotNone(holder.poll())

    def test_different_name_does_not_wait(self):
        self.hold("main", self.repo)
        self.assertEqual(self.lock(self.repo, "e2e", "--timeout", "0.5", "--", "true").returncode, 0)

    def test_killed_holder_frees_the_lock(self):
        holder = self.hold("main", self.repo)
        holder.kill()
        holder.wait()
        self.assertEqual(self.lock(self.repo, "main", "--timeout", "0.5", "--", "true").returncode, 0)

    def test_worktree_and_main_checkout_share_the_lock(self):
        self.hold("main", self.repo)
        result = self.lock(self.worktree, "main", "--timeout", "0.5", "--", "true")
        self.assertEqual(result.returncode, 75)
        self.assertTrue((self.repo / ".git/my-handoff/locks/main.lock").exists())

    def test_exit_code_passes_through(self):
        self.assertEqual(self.lock(self.repo, "main", "--", "sh", "-c", "exit 7").returncode, 7)

    def test_gc_does_not_detach_and_existing_pairs_stay(self):
        env = {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "user.name",
               "GIT_CONFIG_VALUE_0": "Kept"}
        out = self.lock(self.repo, "main", "--", "sh", "-c",
                        "git config gc.autoDetach; git config maintenance.autoDetach;"
                        " git config user.name",
                        env=env).stdout.split()
        self.assertEqual(out, ["false", "false", "Kept"])

    def test_bad_names_are_usage_errors(self):
        for name in ("../x", "a/b", ""):
            with self.subTest(name=name):
                result = self.lock(self.repo, name, "--", "touch", str(self.marker))
                self.assertEqual(result.returncode, 64, name)
        self.assertFalse(self.marker.exists())

    def test_a_timeout_that_is_not_a_finite_number_is_a_usage_error(self):
        for value in ("nan", "inf", "-1"):
            with self.subTest(value=value):
                result = self.lock(self.repo, "main", "--timeout", value, "--", "true")
                self.assertEqual(result.returncode, 64, value)

    def test_missing_separator_is_a_usage_error(self):
        self.assertEqual(self.lock(self.repo, "main", "true").returncode, 64)

    def test_missing_command_exits_127_and_frees_the_lock(self):
        self.assertEqual(self.lock(self.repo, "main", "--", "no-such-command-xyz").returncode, 127)
        self.assertEqual(self.lock(self.repo, "main", "--timeout", "0.5", "--", "true").returncode, 0)


if __name__ == "__main__":
    unittest.main()
