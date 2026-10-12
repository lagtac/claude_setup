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
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "handoff-state.py"
LOCK = Path(__file__).resolve().parent.parent / "bin" / "handoff-lock.py"
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

    def hold(self, name, cwd, seconds=30):
        """Start a holder of lock `name`, and return once it holds the lock."""
        ready = self.tmp / f"ready-{name}"
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


class FieldsTest(StateTestCase):
    def test_new_fields_and_next_value(self):
        self.state("slot=2", "checked_base=abc", "merge_retries=1", "next=merge-retry")
        self.assertEqual({k: self.get()[k] for k in ("slot", "checked_base", "merge_retries", "next")},
                         {"slot": "2", "checked_base": "abc", "merge_retries": "1",
                          "next": "merge-retry"})

    def test_check_merge_retry_needs_checked_base(self):
        self.full("merge-retry")
        self.assertCheck(self.check(), 1, ["missing field: checked_base"])

    def test_check_merge_retry_matches(self):
        self.full("merge-retry", checked_base=git(self.repo, "rev-parse", "main"))
        self.assertCheck(self.check(), 0, [])


class LiveTest(StateTestCase):
    def test_live_lists_runs_that_are_not_finished(self):
        run(self.repo, "set", "a", "slot=1", "next=code", "branch=feat/a")
        run(self.repo, "set", "b", "slot=2", "next=finished")
        run(self.repo, "set", "c", "slot=3", "next=review", "stopped=tests failed")
        result = run(self.repo, "live")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(),
                         ["a\t1\tcode\t\tfeat/a", "c\t3\treview\ttests failed\t"])

    def test_live_ignores_locks_and_temporary_files_and_counts_unreadable_ones(self):
        folder = self.repo / ".git" / "my-handoff"
        (folder / "locks").mkdir(parents=True)
        (folder / "locks" / "main.lock").write_text("")
        (folder / ".a.x1.tmp").write_text("{")
        (folder / "d.json").write_text("{")
        self.assertEqual(run(self.repo, "live").stdout.splitlines(), ["d\t\tunreadable\t\t"])


class StartTest(StateTestCase):
    def start(self, slug, n=2, *pairs):
        return run(self.repo, "start", slug, "--max", str(n), "next=code", *pairs)

    def test_start_takes_the_lowest_free_slot(self):
        self.assertEqual(self.start("a").stdout.strip(), "1")
        self.assertEqual(self.start("b").stdout.strip(), "2")
        run(self.repo, "set", "a", "next=finished")
        self.assertEqual(self.start("c").stdout.strip(), "1")
        state = json.loads(run(self.repo, "get", "c").stdout)
        self.assertEqual((state["slot"], state["merge_retries"], state["next"]), ("1", "0", "code"))

    def test_cap_refuses_and_writes_nothing(self):
        self.start("a")
        self.start("b")
        result = self.start("c")
        self.assertEqual(result.returncode, 1)
        self.assertIn("refused: 2 auto runs are live (a, b); the most is 2", result.stderr)
        self.assertEqual(run(self.repo, "get", "c").returncode, 1)

    def test_own_live_run_refuses_and_leaves_the_file(self):
        self.start("a", 2, "spec=one")
        result = self.start("a", 2, "spec=two")
        self.assertEqual(result.returncode, 1)
        self.assertIn("refused: a run for a exists; use resume", result.stderr)
        self.assertEqual(json.loads(run(self.repo, "get", "a").stdout)["spec"], "one")

    def test_finished_own_run_is_replaced(self):
        run(self.repo, "set", "a", "next=finished", "stopped=old")
        self.assertEqual(self.start("a").returncode, 0)
        self.assertNotIn("stopped", json.loads(run(self.repo, "get", "a").stdout))

    def test_usage_errors_write_nothing(self):
        for args in (["start", "a", "--max", "0", "next=code"], ["start", "a", "--max", "x"],
                     ["start", "a", "next=code"], ["start", "a", "--max", "2", "colour=red"],
                     ["start", "a", "--max", "2", "next=nowhere"]):
            with self.subTest(args=args):
                self.assertEqual(run(self.repo, *args).returncode, 2, args)
        self.assertEqual(run(self.repo, "get", "a").returncode, 1)

    def test_unreadable_state_counts_toward_the_cap(self):
        folder = self.repo / ".git" / "my-handoff"
        folder.mkdir()
        (folder / "d.json").write_text("{")
        self.assertEqual(self.start("a", 1).returncode, 1)

    def test_concurrent_locked_starts_never_pass_the_cap(self):
        procs = [subprocess.Popen([sys.executable, str(LOCK), "main", "--", sys.executable,
                                   str(SCRIPT), "start", f"s{i}", "--max", "2", "next=code"],
                                  cwd=self.repo, env=clean_env(), stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True)
                 for i in range(4)]
        outs = [(p.wait(timeout=60), p.stdout.read().strip()) for p in procs]
        for p in procs:
            p.stdout.close()
        self.assertEqual(sorted(code for code, _ in outs), [0, 0, 1, 1])
        self.assertEqual(sorted(slot for code, slot in outs if code == 0), ["1", "2"])

    def test_lock_timeout_writes_nothing(self):
        self.hold("main", self.repo)
        result = subprocess.run([sys.executable, str(LOCK), "main", "--timeout", "0.5", "--",
                                 sys.executable, str(SCRIPT), "start", "a", "--max", "2",
                                 "next=code"],
                                cwd=self.repo, env=clean_env(), capture_output=True, text=True)
        self.assertEqual(result.returncode, 75)
        self.assertEqual(run(self.repo, "get", "a").returncode, 1)


class MergeTest(StateTestCase):
    MESSAGE = SUBJECT + "\n\nThe body.\n\nCo-Authored-By: X <x@example.com>"

    def ready(self, **extra):
        self.full("merge-retry", checked_base=git(self.repo, "merge-base", "main", "feat/widget"),
                  squash_subject="", **extra)

    def merge(self, *extra):
        return run(self.repo, "merge", "widget", "-m", self.MESSAGE, *extra)

    def test_merge_lands_the_squash_and_moves_next(self):
        self.ready()
        result = self.merge()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), git(self.repo, "rev-parse", "--short", "HEAD"))
        self.assertEqual(git(self.repo, "log", "-1", "--format=%s"), SUBJECT)
        self.assertEqual(git(self.repo, "log", "-1", "--format=%B"), self.MESSAGE)
        self.assertTrue((self.repo / "widget.py").exists())
        state = self.get()
        self.assertEqual((state["next"], state["squash_subject"]), ("worktree-remove", SUBJECT))

    def test_refuses_staged_changes(self):
        self.ready()
        before = git(self.repo, "rev-parse", "HEAD")
        (self.repo / "staged.md").write_text("x\n")
        git(self.repo, "add", "staged.md")
        result = self.merge()
        self.assertEqual(result.returncode, 1)
        self.assertIn("staged changes", result.stderr)
        self.assertEqual((git(self.repo, "rev-parse", "HEAD"), self.get()["next"]),
                         (before, "merge-retry"))

    def test_refuses_when_code_moved_on_the_base(self):
        self.ready()
        commit(self.repo, "feat: other", {"other.py": "y = 2\n"})
        before = git(self.repo, "rev-parse", "HEAD")
        result = self.merge()
        self.assertEqual(result.returncode, 4)
        self.assertIn("other.py", result.stderr)
        self.assertEqual((git(self.repo, "rev-parse", "HEAD"), self.get()["next"]),
                         (before, "merge-retry"))

    def test_docs_only_move_still_merges(self):
        self.ready()
        commit(self.repo, "docs: roadmap", {"ROADMAP.md": "row\n"})
        result = self.merge()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_docs_paths_option_changes_the_list(self):
        self.ready()
        commit(self.repo, "docs: notes", {"NOTES.md": "n\n"})
        self.assertEqual(self.merge().returncode, 4)
        result = self.merge("--docs-paths", "NOTES.md")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_squash_conflict_resets_and_keeps_next_merge(self):
        commit(self.worktree, "docs: branch roadmap", {"ROADMAP.md": "branch\n"})
        self.ready()
        commit(self.repo, "docs: main roadmap", {"ROADMAP.md": "main\n"})
        before = git(self.repo, "rev-parse", "HEAD")
        result = self.merge()
        self.assertEqual(result.returncode, 5)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), before)
        self.assertEqual((self.get()["next"], self.get()["squash_subject"]), ("merge", SUBJECT))
        self.assertFalse((self.repo / ".git" / "SQUASH_MSG").exists())

    def test_failed_commit_resets(self):
        self.ready()
        hook = self.repo / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
        self.assertEqual(self.merge().returncode, 5)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")
        self.assertFalse((self.repo / ".git" / "SQUASH_MSG").exists())

    def test_missing_checked_base_refuses(self):
        self.full("merge-retry")
        result = self.merge()
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing field: checked_base", result.stderr)
        self.assertEqual(git(self.repo, "log", "-1", "--format=%s"),
                         "docs(plans): plan for the widget")

    def test_wrong_next_refuses(self):
        self.ready()
        self.state("next=review")
        self.assertEqual(self.merge().returncode, 1)


if __name__ == "__main__":
    unittest.main()
