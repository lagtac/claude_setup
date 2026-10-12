"""Tests for bin/handoff-state.py.

Run from plugins/my: python3 -m unittest discover tests

Each test builds a throwaway repository in a temporary directory: `main` holds
a spec and a plan, and the branch `feat/widget` is checked out in a worktree
next to the repository. The script runs there as a subprocess. Git runs
without the user's or the system's config, so a hook path or rebase setting of
the machine cannot change a result.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "handoff-state.py"
SPEC = "docs/plans/2026-10-12-widget-spec.md"
PLAN = "docs/plans/2026-10-12-widget.md"
SUBJECT = "feat(widget): the widget"


def clean_env(extra={}):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_EDITOR"] = "false"
    env.update(extra)
    return env


def git(repo, *args, check=True, env={}):
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        env=clean_env(env),
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
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        git(repo, "add", name)
    git(repo, "commit", "-q", "--allow-empty", "-m", subject)
    return git(repo, "rev-parse", "HEAD")


class StateTestCase(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.tmp = Path(folder.name)
        self.repo = make_repo(self.tmp)
        commit(self.repo, "docs(plans): spec for the widget", {SPEC: "spec\n"})
        commit(self.repo, "docs(plans): plan for the widget", {PLAN: "plan\n"})
        self.worktree = self.tmp / "wt"
        git(self.repo, "worktree", "add", "-q", str(self.worktree), "-b", "feat/widget")
        commit(self.worktree, "feat(widget): first task", {"widget.py": "x = 1\n"})

    def state(self, *pairs, cwd=None):
        result = run(cwd or self.repo, "set", "widget", *pairs)
        self.assertEqual(result.returncode, 0, result.stderr)

    def get(self):
        result = run(self.repo, "get", "widget")
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def full(self, next_value, **extra):
        values = {"spec": SPEC, "task_doc": PLAN, "branch": "feat/widget",
                  "worktree": str(self.worktree), "next": next_value,
                  "squash_subject": SUBJECT, **extra}
        self.state(*(f"{k}={v}" for k, v in values.items()))

    def squash_merge(self):
        git(self.repo, "merge", "--squash", "feat/widget")
        git(self.repo, "commit", "-q", "-m", SUBJECT)

    def check(self):
        return run(self.repo, "check", "widget")

    def assertCheck(self, result, code, lines):
        self.assertEqual((result.returncode, result.stdout.splitlines()),
                         (code, lines), result.stderr)


class SetGetTest(StateTestCase):
    def test_set_then_get_round_trips_every_field(self):
        pairs = {"spec": SPEC, "task_doc": PLAN, "branch": "feat/widget",
                 "worktree": ".claude/worktrees/widget", "next": "merge",
                 "squash_subject": SUBJECT, "head_before_fold": "abc1234",
                 "stopped": "fold refused: a dirty tree"}
        self.state(*(f"{k}={v}" for k, v in pairs.items()))
        self.assertEqual(self.get(), pairs)

    def test_set_keeps_the_fields_it_does_not_name(self):
        self.state(f"spec={SPEC}", "next=plan")
        self.state("next=code", "stopped=")
        self.assertEqual(self.get(), {"spec": SPEC, "next": "code", "stopped": ""})

    def test_set_rejects_an_unknown_field(self):
        result = run(self.repo, "set", "widget", "next=plan", "colour=red")
        self.assertEqual((result.returncode, result.stderr.strip()),
                         (2, "unknown field: colour"))
        self.assertFalse((self.repo / ".git" / "my-handoff" / "widget.json").exists())

    def test_set_rejects_an_unknown_next(self):
        result = run(self.repo, "set", "widget", "next=shipping")
        self.assertEqual((result.returncode, result.stderr.strip()),
                         (2, "unknown next: shipping"))

    def test_get_without_a_file_exits_1(self):
        result = run(self.repo, "get", "widget")
        self.assertEqual((result.returncode, result.stderr.strip()),
                         (1, "no state for widget"))

    def test_file_is_in_the_git_common_dir_and_untracked(self):
        self.state("next=plan", cwd=self.worktree)
        path = self.repo / ".git" / "my-handoff" / "widget.json"
        self.assertEqual(json.loads(path.read_text()), {"next": "plan"})
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")

    def test_no_temporary_file_is_left(self):
        for value in ("plan", "code", "review"):
            self.state(f"next={value}")
        folder = self.repo / ".git" / "my-handoff"
        self.assertEqual(sorted(p.name for p in folder.iterdir()), ["widget.json"])

    def test_usage_error(self):
        for args in ([], ["set", "widget"], ["get"], ["check", "a", "b"],
                     ["stop", "widget"], ["set", "widget", "next"]):
            with self.subTest(args=args):
                self.assertEqual(run(self.repo, *args).returncode, 2)


class CheckTest(StateTestCase):
    def test_check_without_a_file(self):
        self.assertCheck(self.check(), 1, ["no state for widget"])

    def test_check_matches_for_each_next(self):
        steps = ["plan", "code", "review", "merge"]
        for value in steps:
            with self.subTest(next=value):
                self.full(value)
                self.assertCheck(self.check(), 0, [])
        self.squash_merge()
        self.full("worktree-remove")
        self.assertCheck(self.check(), 0, [])
        git(self.repo, "worktree", "remove", str(self.worktree))
        for value in ("fold", "done", "finished"):
            with self.subTest(next=value):
                self.full(value)
                self.assertCheck(self.check(), 0, [])

    def test_check_mismatch_for_each_next(self):
        cases = {
            "plan": ({"spec": "docs/plans/gone-spec.md"},
                     ["spec missing: docs/plans/gone-spec.md"]),
            "code": ({"task_doc": "docs/plans/2026-10-12-new.md"},
                     ["task doc not committed on main: docs/plans/2026-10-12-new.md"]),
            "review": ({"branch": "feat/gone"}, ["branch missing: feat/gone"]),
            "merge": ({"branch": "feat/gone"},
                      ["branch missing: feat/gone", f"no squash commit: {SUBJECT}"]),
            "worktree-remove": ({}, [f"no squash commit: {SUBJECT}"]),
        }
        for value, (extra, lines) in cases.items():
            with self.subTest(next=value):
                self.full(value, **extra)
                self.assertCheck(self.check(), 1, lines)
        self.squash_merge()
        with self.subTest(next="fold"):
            self.full("fold")
            self.assertCheck(self.check(), 1, [f"worktree still listed: {self.worktree}"])
        with self.subTest(next="done"):
            git(self.repo, "worktree", "remove", str(self.worktree))
            commit(self.repo, "fixup! docs(plans): spec for the widget", {SPEC: "spec 2\n"})
            fixup = git(self.repo, "rev-parse", "--short=7", "HEAD")
            self.full("done")
            self.assertCheck(self.check(), 1, [
                f"fixup waits: {fixup} fixup! docs(plans): spec for the widget"])
        with self.subTest(next="finished"):
            self.start_rebase()
            self.full("finished")
            self.assertCheck(self.check(), 1, ["in progress: rebase-merge"])

    def test_check_finds_a_merge_that_happened_before_a_crash(self):
        self.full("merge")
        self.squash_merge()
        self.assertCheck(self.check(), 0, ["merge done"])
        self.assertEqual(self.get()["next"], "worktree-remove")

    def test_check_ignores_an_older_commit_with_the_squash_subject(self):
        commit(self.repo, SUBJECT)
        git(self.worktree, "reset", "-q", "--hard", "main")
        commit(self.worktree, "feat(widget): first task", {"widget.py": "x = 1\n"})
        self.full("merge")
        self.assertCheck(self.check(), 0, [])
        self.assertEqual(self.get()["next"], "merge")

    def test_check_counts_two_squash_commits(self):
        self.squash_merge()
        commit(self.repo, SUBJECT)
        self.full("worktree-remove")
        self.assertCheck(self.check(), 1, ["squash subject matches 2 commits"])

    def start_rebase(self):
        git(self.repo, "rebase", "-i", "HEAD~1",
            env={"GIT_SEQUENCE_EDITOR": "sed -i 1s/pick/edit/"})
        self.assertTrue((self.repo / ".git" / "rebase-merge").exists())

    def test_check_refuses_during_a_rebase(self):
        self.full("done")
        self.start_rebase()
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("in progress: rebase-merge", result.stdout.splitlines())

    def test_check_names_a_missing_field(self):
        self.state(f"spec={SPEC}", "next=review", f"worktree={self.worktree}")
        self.assertCheck(self.check(), 1, ["missing field: branch"])

    def test_check_names_a_missing_field_after_the_merge(self):
        self.squash_merge()
        self.state(f"spec={SPEC}", f"task_doc={PLAN}", "branch=feat/widget",
                   "next=worktree-remove", f"squash_subject={SUBJECT}", "worktree=")
        self.assertCheck(self.check(), 1, ["missing field: worktree"])
        git(self.repo, "worktree", "remove", str(self.worktree))
        self.state("next=done", f"worktree={self.worktree}", "squash_subject=")
        self.assertCheck(self.check(), 1, ["missing field: squash_subject"])

    def test_check_at_done_needs_exactly_one_squash_commit(self):
        git(self.repo, "worktree", "remove", str(self.worktree))
        self.full("done")
        self.assertCheck(self.check(), 1, [f"no squash commit: {SUBJECT}"])
        self.squash_merge()
        commit(self.repo, SUBJECT)
        self.assertCheck(self.check(), 1, ["squash subject matches 2 commits"])

    def test_check_refuses_a_squash_left_staged(self):
        self.full("merge")
        git(self.repo, "merge", "--squash", "feat/widget")
        self.assertCheck(self.check(), 1, [
            "in progress: SQUASH_MSG", "staged changes in the main checkout"])
        self.assertEqual(self.get()["next"], "merge")

    def test_check_refuses_a_fold_that_rewrote_history(self):
        self.squash_merge()
        git(self.repo, "worktree", "remove", str(self.worktree))
        before = git(self.repo, "rev-parse", "HEAD")
        self.full("fold", head_before_fold=before)
        commit(self.repo, "docs: later work")
        self.assertCheck(self.check(), 0, [])
        git(self.repo, "reset", "-q", "--hard", "HEAD~2")
        commit(self.repo, SUBJECT)
        self.assertCheck(self.check(), 1, [
            f"history rewritten: head_before_fold {before} is not on main"])

    def test_check_writes_nothing_when_the_merge_step_fails(self):
        self.full("merge")
        self.squash_merge()
        commit(self.repo, SUBJECT)
        self.assertCheck(self.check(), 1, ["squash subject matches 2 commits"])
        self.assertEqual(self.get()["next"], "merge")

    def test_check_from_the_worktree(self):
        self.full("review")
        self.assertCheck(run(self.worktree, "check", "widget"), 0, [])


if __name__ == "__main__":
    unittest.main()
