"""Tests for bin/git-fold-fixups.py.

Run from plugins/my: python3 -m unittest discover tests

Each test builds a throwaway repository in a temporary directory and runs the
script there as a subprocess. Git runs without the user's or the system's
config, so a hook path or rebase setting of the machine cannot change a result.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "git-fold-fixups.py"


def clean_env():
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_EDITOR"] = "false"
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


def run(repo, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=repo,
        env=clean_env(),
        capture_output=True,
        text=True,
        timeout=60,
    )


def make_repo(tmp, root=True):
    repo = Path(tmp) / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "user.email", "test@example.com")
    if root:
        commit(repo, "root", {"root.md": "root\n"})
    return repo


def commit(repo, subject, files={}):
    for name, text in files.items():
        (repo / name).write_text(text)
        git(repo, "add", name)
    git(repo, "commit", "-q", "--allow-empty", "-m", subject)
    return git(repo, "rev-parse", "HEAD")


def subjects(repo):
    return git(repo, "log", "--format=%s").splitlines()


class FoldTestCase(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.tmp = Path(folder.name)
        self.repo = make_repo(self.tmp)

    def spec_with_fixup(self):
        """root, docs: spec, unrelated, fixup! docs: spec. Returns the spec hash."""
        target = commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        commit(self.repo, "unrelated", {"other.md": "other\n"})
        commit(self.repo, "fixup! docs: spec", {"spec.md": "two\n"})
        return target

    def head(self):
        return git(self.repo, "rev-parse", "HEAD")

    def add_upstream(self):
        """Push main to a bare origin and track it. Returns the origin path."""
        origin = self.tmp / "origin.git"
        git(self.repo, "clone", "-q", "--bare", str(self.repo), str(origin))
        git(self.repo, "remote", "add", "origin", str(origin))
        git(self.repo, "fetch", "-q", "origin")
        git(self.repo, "branch", "-u", "origin/main")
        return origin

    def assertRefused(self, result, word, before):
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(word, result.stderr)
        self.assertEqual(self.head(), before)


class CheckTest(FoldTestCase):
    def test_check_safe_without_worktree(self):
        target = commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        commit(self.repo, "later")
        result = run(self.repo, "check", target)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_check_refuses_when_worktree_holds_branch(self):
        target = commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        commit(self.repo, "later")
        git(self.repo, "worktree", "add", "-q", str(self.tmp / "wt"), "-b", "feat")
        result = run(self.repo, "check", target)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("feat", result.stderr)
        self.assertIn("wt", result.stderr)

    def test_check_ignores_merged_branch_without_worktree(self):
        target = commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        commit(self.repo, "later")
        git(self.repo, "branch", "merged")
        result = run(self.repo, "check", target)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_check_refuses_target_on_upstream(self):
        target = commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        self.add_upstream()
        result = run(self.repo, "check", target)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("pushed", result.stderr)

    def test_check_refuses_shared_subject(self):
        commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        target = commit(self.repo, "docs: spec", {"spec.md": "two\n"})
        result = run(self.repo, "check", target)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("ambiguous", result.stderr)

    def test_check_refuses_detached_worktree_on_top(self):
        target = commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        commit(self.repo, "later")
        git(self.repo, "worktree", "add", "-q", "--detach", str(self.tmp / "wt"))
        result = run(self.repo, "check", target)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("detached", result.stderr)
        self.assertIn("wt", result.stderr)

    def test_check_of_a_fixup_tests_its_target(self):
        commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        self.add_upstream()
        fixup = commit(self.repo, "fixup! docs: spec", {"spec.md": "two\n"})
        result = run(self.repo, "check", fixup)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("pushed", result.stderr)

    def test_check_refuses_merge_after_target(self):
        target = commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        git(self.repo, "checkout", "-q", "-b", "side")
        commit(self.repo, "side work", {"side.md": "side\n"})
        git(self.repo, "checkout", "-q", "main")
        commit(self.repo, "main work", {"main.md": "main\n"})
        git(self.repo, "merge", "-q", "--no-ff", "-m", "merge side", "side")
        result = run(self.repo, "check", target)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("merge", result.stderr)

    def test_check_refuses_squash_commit_after_target(self):
        target = commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        commit(self.repo, "squash! docs: spec", {"spec.md": "two\n"})
        result = run(self.repo, "check", target)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("squash!", result.stderr)

    def test_check_refuses_target_off_first_parent_history(self):
        git(self.repo, "checkout", "-q", "-b", "side")
        target = commit(self.repo, "side work", {"side.md": "side\n"})
        git(self.repo, "checkout", "-q", "main")
        commit(self.repo, "main work", {"main.md": "main\n"})
        git(self.repo, "merge", "-q", "--no-ff", "-m", "merge side", "side")
        result = run(self.repo, "check", target)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("no target", result.stderr)

    def side_commit_sharing_a_subject(self):
        """main has `docs: spec`; branch side has another `docs: spec`. Returns side's."""
        commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        git(self.repo, "checkout", "-q", "-b", "side", "HEAD~1")
        side = commit(self.repo, "docs: spec", {"side.md": "side\n"})
        git(self.repo, "checkout", "-q", "main")
        return side

    def test_check_refuses_off_history_target_sharing_a_subject(self):
        side = self.side_commit_sharing_a_subject()
        result = run(self.repo, "check", side)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("no target", result.stderr)

    def test_check_refuses_off_history_fixup_sharing_a_subject(self):
        commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        git(self.repo, "checkout", "-q", "-b", "side", "HEAD~1")
        commit(self.repo, "docs: spec", {"side.md": "side\n"})
        fixup = commit(self.repo, "fixup! docs: spec", {"side.md": "two\n"})
        git(self.repo, "checkout", "-q", "main")
        result = run(self.repo, "check", fixup)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("no target", result.stderr)

    def test_check_refuses_fixup_older_than_its_target(self):
        fixup = commit(self.repo, "fixup! docs: spec", {"spec.md": "one\n"})
        commit(self.repo, "docs: spec", {"spec.md": "two\n"})
        result = run(self.repo, "check", fixup)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("no target", result.stderr)

    def test_check_safe_for_a_waiting_fixup(self):
        self.spec_with_fixup()
        result = run(self.repo, "check", self.head())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_check_safe_when_target_has_a_waiting_fixup(self):
        target = self.spec_with_fixup()
        result = run(self.repo, "check", target)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_check_not_a_commit_is_usage_error(self):
        result = run(self.repo, "check", "no-such-ref")
        self.assertEqual(result.returncode, 2)
        self.assertIn("not a commit", result.stderr)

    def test_usage_error(self):
        result = run(self.repo, "check")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Usage", result.stderr)
        self.assertNotIn("No such file", result.stderr)


class FoldTest(FoldTestCase):
    def test_nothing_to_fold(self):
        commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        before = self.head()
        result = run(self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("nothing to fold", result.stdout)
        self.assertEqual(self.head(), before)

    def test_folds_one_fixup(self):
        self.spec_with_fixup()
        before = self.head()
        result = run(self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("folded 1 fixups into 1 commits", result.stdout)
        self.assertEqual(subjects(self.repo), ["unrelated", "docs: spec", "root"])
        self.assertEqual(git(self.repo, "diff", before, "HEAD"), "")

    def test_folds_nested_fixup_prefix(self):
        commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        commit(self.repo, "fixup! docs: spec", {"spec.md": "two\n"})
        commit(self.repo, "fixup! fixup! docs: spec", {"spec.md": "three\n"})
        before = self.head()
        result = run(self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(subjects(self.repo), ["docs: spec", "root"])
        self.assertEqual(git(self.repo, "diff", before, "HEAD"), "")

    def test_folds_into_root_commit(self):
        commit(self.repo, "fixup! root", {"root.md": "changed\n"})
        before = self.head()
        result = run(self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(subjects(self.repo), ["root"])
        self.assertEqual(git(self.repo, "diff", before, "HEAD"), "")

    def test_folds_two_targets_from_the_oldest(self):
        commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        commit(self.repo, "docs: plan", {"plan.md": "one\n"})
        commit(self.repo, "fixup! docs: plan", {"plan.md": "two\n"})
        commit(self.repo, "fixup! docs: spec", {"spec.md": "two\n"})
        before = self.head()
        result = run(self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("folded 2 fixups into 2 commits", result.stdout)
        self.assertEqual(subjects(self.repo), ["docs: plan", "docs: spec", "root"])
        self.assertEqual(git(self.repo, "diff", before, "HEAD"), "")

    def test_ignores_fixup_already_pushed(self):
        self.spec_with_fixup()
        self.add_upstream()
        commit(self.repo, "later", {"later.md": "later\n"})
        before = self.head()
        result = run(self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("nothing to fold", result.stdout)
        self.assertEqual(self.head(), before)

    def test_allows_untracked_file(self):
        self.spec_with_fixup()
        (self.repo / "loose.txt").write_text("untracked\n")
        result = run(self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(subjects(self.repo), ["unrelated", "docs: spec", "root"])
        self.assertTrue((self.repo / "loose.txt").exists())


class RefusalTest(FoldTestCase):
    def test_refuses_dirty_tracked_file(self):
        self.spec_with_fixup()
        before = self.head()
        (self.repo / "other.md").write_text("edited\n")
        self.assertRefused(run(self.repo), "uncommitted", before)

    def test_refuses_fixup_without_target(self):
        commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        commit(self.repo, "fixup! docs: missing", {"spec.md": "two\n"})
        before = self.head()
        self.assertRefused(run(self.repo), "no target", before)

    def test_refuses_target_held_by_worktree(self):
        target = self.spec_with_fixup()
        before = self.head()
        git(self.repo, "worktree", "add", "-q", str(self.tmp / "wt"), "-b", "feat", target)
        self.assertRefused(run(self.repo), "feat", before)

    def test_refuses_target_on_upstream(self):
        commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        self.add_upstream()
        commit(self.repo, "fixup! docs: spec", {"spec.md": "two\n"})
        before = self.head()
        self.assertRefused(run(self.repo), "pushed", before)

    def test_refuses_target_under_detached_worktree(self):
        self.spec_with_fixup()
        before = self.head()
        git(self.repo, "worktree", "add", "-q", "--detach", str(self.tmp / "wt"), "HEAD~1")
        self.assertRefused(run(self.repo), "detached", before)

    def test_refuses_missing_upstream_ref(self):
        self.spec_with_fixup()
        self.add_upstream()
        git(self.repo, "update-ref", "-d", "refs/remotes/origin/main")
        before = self.head()
        result = run(self.repo)
        self.assertRefused(result, "upstream origin/main is configured but missing", before)
        self.assertNotIn("ambiguous argument", result.stderr)

    def test_refuses_merge_in_range(self):
        commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        git(self.repo, "checkout", "-q", "-b", "side")
        commit(self.repo, "side work", {"side.md": "side\n"})
        git(self.repo, "checkout", "-q", "main")
        commit(self.repo, "main work", {"main.md": "main\n"})
        git(self.repo, "merge", "-q", "--no-ff", "-m", "merge side", "side")
        commit(self.repo, "fixup! docs: spec", {"spec.md": "two\n"})
        before = self.head()
        self.assertRefused(run(self.repo), "merge", before)

    def test_refuses_during_rebase(self):
        commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        commit(self.repo, "fixup! docs: spec", {"spec.md": "two\n"})
        git(self.repo, "checkout", "-q", "-b", "other", "HEAD~2")
        commit(self.repo, "other", {"spec.md": "clash\n"})
        git(self.repo, "checkout", "-q", "main")
        git(self.repo, "rebase", "-q", "other", check=False)
        before = self.head()
        result = run(self.repo)
        self.assertRefused(result, "in progress", before)
        rebase_dir = self.repo / git(self.repo, "rev-parse", "--git-path", "rebase-merge")
        self.assertTrue(rebase_dir.exists())

    def test_conflict_aborts_and_restores_head(self):
        commit(self.repo, "docs: spec", {"spec.md": "x\n"})
        commit(self.repo, "later edit", {"spec.md": "y\n"})
        commit(self.repo, "fixup! docs: spec", {"spec.md": "z\n"})
        before = self.head()
        result = run(self.repo)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("the rebase failed", result.stderr)
        self.assertIn("could not apply", result.stderr)
        self.assertEqual(self.head(), before)
        rebase_dir = self.repo / git(self.repo, "rev-parse", "--git-path", "rebase-merge")
        self.assertFalse(rebase_dir.exists())
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")

    def test_refuses_ambiguous_target(self):
        commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        commit(self.repo, "docs: spec", {"spec.md": "two\n"})
        commit(self.repo, "fixup! docs: spec", {"spec.md": "three\n"})
        before = self.head()
        self.assertRefused(run(self.repo), "ambiguous", before)

    def test_refuses_squash_commit_in_range(self):
        commit(self.repo, "docs: spec", {"spec.md": "one\n"})
        commit(self.repo, "squash! docs: spec", {"spec.md": "two\n"})
        commit(self.repo, "fixup! docs: spec", {"spec.md": "three\n"})
        before = self.head()
        self.assertRefused(run(self.repo), "squash!", before)

    def test_pre_rebase_hook_refusal_restores_nothing_to_abort(self):
        self.spec_with_fixup()
        before = self.head()
        hook = self.repo / ".git" / "hooks" / "pre-rebase"
        hook.write_text("#!/bin/sh\necho 'hook says no' >&2\nexit 1\n")
        hook.chmod(0o755)
        result = run(self.repo)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("hook says no", result.stderr)
        self.assertNotIn("No rebase in progress", result.stderr)
        self.assertEqual(self.head(), before)


if __name__ == "__main__":
    unittest.main()
