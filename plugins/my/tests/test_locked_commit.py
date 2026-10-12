"""Tests for bin/locked-commit.py.

Run from plugins/my: python3 -m unittest discover tests

Each test builds a throwaway repository in a temporary directory and runs the
real script in it. The message file sits in the temporary directory, outside
the repository. Git runs without the user's or the system's config.
"""

import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin"
SCRIPT = BIN / "locked-commit.py"
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


def message(tmp, text, name="msg.txt"):
    path = Path(tmp) / name
    path.write_text(text)
    return path


def run(repo, *args, timeout=30):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], cwd=repo,
                          env=clean_env(), capture_output=True, text=True,
                          timeout=timeout)


class LockedCommitTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.tmp = Path(folder.name)
        self.repo = make_repo(self.tmp)
        (self.repo / "a.md").write_text("a\n")
        self.msg = message(self.tmp, "docs: add a\n")

    def assert_refused(self, result):
        head, index = git(self.repo, "rev-parse", "HEAD"), git(self.repo, "ls-files", "-s")
        self.assertEqual(result.returncode, 64, result.stderr)
        self.assertTrue(result.stderr.startswith("locked-commit:"), result.stderr)
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), head)
        self.assertEqual(git(self.repo, "ls-files", "-s"), index)
        self.assertEqual(git(self.repo, "ls-files", "-s", "a.md"), "")

    def test_message_with_shell_characters_is_verbatim(self):
        text = "docs: it's `x` and $(id)\n\nbody line\n"
        msg = message(self.tmp, text, "shell.txt")
        result = run(self.repo, "-F", msg, "a.md")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(git(self.repo, "log", "-1", "--format=%B"), text.strip())

    def test_prints_stat_of_its_commit(self):
        result = run(self.repo, "-F", self.msg, "a.md")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(" a.md | ", result.stdout)
        self.assertIn(git(self.repo, "show", "--stat", "--format=", "HEAD"), result.stdout)

    def test_other_staged_file_stays_staged(self):
        (self.repo / "b.md").write_text("b\n")
        git(self.repo, "add", "b.md")
        result = run(self.repo, "-F", self.msg, "a.md")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(git(self.repo, "show", "--name-only", "--format=", "HEAD"), "a.md")
        self.assertEqual(git(self.repo, "diff", "--cached", "--name-only"), "b.md")

    def test_deleted_path_committed_as_deletion(self):
        (self.repo / "c.md").write_text("c\n")
        git(self.repo, "add", "c.md")
        git(self.repo, "commit", "-q", "-m", "add c")
        (self.repo / "c.md").unlink()
        result = run(self.repo, "-F", self.msg, "c.md")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(git(self.repo, "show", "--name-status", "--format=", "HEAD"), "D\tc.md")

    def test_message_file_deleted_after_success(self):
        result = run(self.repo, "-F", self.msg, "a.md")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.msg.exists())

    def test_message_file_kept_when_commit_fails(self):
        result = run(self.repo, "-F", self.msg, "root.md")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.msg.exists())

    def test_paths_unstaged_when_hook_rejects_commit(self):
        hook = self.repo / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
        head = git(self.repo, "rev-parse", "HEAD")
        result = run(self.repo, "-F", self.msg, "a.md")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), head)
        self.assertEqual(git(self.repo, "diff", "--cached", "--name-only"), "")
        self.assertTrue(self.msg.exists())

    def test_refuses_without_paths(self):
        self.assert_refused(run(self.repo, "-F", self.msg))

    def test_refuses_without_message_file_option(self):
        self.assert_refused(run(self.repo, "a.md"))

    def test_refuses_unknown_option(self):
        self.assert_refused(run(self.repo, "--amend", "-F", self.msg, "a.md"))

    def test_refuses_missing_message_file(self):
        self.assert_refused(run(self.repo, "-F", self.tmp / "nope", "a.md"))

    def test_refuses_blank_message_file(self):
        blank = message(self.tmp, " \n\n", "blank.txt")
        self.assert_refused(run(self.repo, "-F", blank, "a.md"))

    def test_refuses_message_file_inside_work_tree(self):
        inside = message(self.repo, "docs: add a\n")
        self.assert_refused(run(self.repo, "-F", inside, "a.md"))
        self.assertTrue(inside.exists())

    def test_refuses_message_file_inside_work_tree_by_relative_path(self):
        (self.repo / "sub").mkdir()
        message(self.repo / "sub", "docs: add a\n")
        self.assert_refused(run(self.repo / "sub", "-F", "msg.txt", "../a.md"))

    def test_refuses_outside_repository(self):
        plain = self.tmp / "plain"
        plain.mkdir()
        (plain / "a.md").write_text("a\n")
        result = run(plain, "-F", self.msg, "a.md")
        self.assertEqual(result.returncode, 64, result.stderr)
        self.assertTrue(result.stderr.startswith("locked-commit:"), result.stderr)
        self.assertTrue(self.msg.exists())

    def test_help_prints_usage_and_exits_0(self):
        for flag in ("-h", "--help"):
            with self.subTest(flag=flag):
                result = run(self.repo, flag)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("Usage:", result.stdout)

    def test_lock_timeout_exits_75_and_commits_nothing(self):
        ready = self.tmp / "ready"
        holder = subprocess.Popen(
            [sys.executable, str(LOCK), "main", "--", "sh", "-c",
             'touch "$0"; exec sleep 5', str(ready)],
            cwd=self.repo, env=clean_env(), stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        self.addCleanup(holder.wait)
        self.addCleanup(holder.kill)
        deadline = time.monotonic() + 10
        while not ready.exists():
            if time.monotonic() > deadline or holder.poll() is not None:
                self.fail("holder of main never started")
            time.sleep(0.05)
        head_before = git(self.repo, "rev-parse", "HEAD")
        result = run(self.repo, "--timeout", "0", "-F", self.msg, "a.md")
        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertTrue(result.stderr.startswith("handoff-lock:"), result.stderr)
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), head_before)
        self.assertEqual(git(self.repo, "ls-files", "-s", "a.md"), "")
        self.assertTrue(self.msg.exists())


if __name__ == "__main__":
    unittest.main()
