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
import shutil
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
                     ["stop", "widget"], ["set", "widget", "next"],
                     ["queue"], ["queue", "add"], ["queue", "nope"],
                     ["pull"], ["pull", "--max", "0"], ["queue", "show", "x"]):
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

    def test_live_ignores_the_queue_folder(self):
        folder = self.repo / ".git" / "my-handoff" / "queue"
        folder.mkdir(parents=True)
        (folder / "rows.json").write_text(json.dumps([{"slug": "a", "state": "waiting"}]))
        result = run(self.repo, "live")
        self.assertEqual((result.returncode, result.stdout), (0, ""))


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


def spec(slug):
    return f"docs/plans/2026-10-13-{slug}-spec.md"


class QueueTestCase(StateTestCase):
    """The specs of rows a, b and c are committed on main."""

    def setUp(self):
        super().setUp()
        commit(self.repo, "docs(plans): specs a, b and c",
               {spec(slug): f"spec {slug}\n" for slug in "abc"})

    def entries_file(self, *entries):
        path = self.tmp / f"entries-{len(list(self.tmp.glob('entries-*')))}.json"
        path.write_text(json.dumps(list(entries)))
        return path

    def entry(self, slug, after=(), stage="code", exclusive=False, row=None):
        return {"row": row or slug, "spec": spec(slug), "stage": stage,
                "after": list(after), "exclusive": exclusive}

    def add(self, *entries):
        return run(self.repo, "queue", "add", "--file", str(self.entries_file(*entries)))

    def queue_file(self):
        return self.repo / ".git" / "my-handoff" / "queue" / "rows.json"

    def queue(self):
        path = self.queue_file()
        return json.loads(path.read_text()) if path.exists() else []

    def get_state(self, slug):
        result = run(self.repo, "get", slug)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)


class QueueAddTest(QueueTestCase):
    def test_add_writes_a_waiting_entry_with_the_spec_hash(self):
        result = self.add(self.entry("a", row="1b"))
        self.assertEqual((result.returncode, result.stdout), (0, "added\ta\n"), result.stderr)
        self.assertEqual(self.queue(), [{
            "row": "1b", "slug": "a", "spec": "docs/plans/2026-10-13-a-spec.md",
            "stage": "code", "after": [], "exclusive": False,
            "spec_hash": git(self.repo, "hash-object", "docs/plans/2026-10-13-a-spec.md"),
            "state": "waiting", "reason": ""}])

    def test_add_refuses_an_invalid_entry_and_writes_nothing(self):
        bad = {"unknown key": {"colour": "red"}, "missing key": {"stage": None},
               "stage": {"stage": "review"}, "after slug": {"after": ["../x"]},
               "after type": {"after": "a"}, "exclusive type": {"exclusive": "yes"},
               "row type": {"row": 5}, "spec pattern": {"spec": "docs/plans/a.md"},
               "spec missing": {"spec": "docs/plans/2026-10-13-zz-spec.md"}}
        for name, change in bad.items():
            with self.subTest(name):
                entry = {k: v for k, v in {**self.entry("b"), **change}.items()
                         if v is not None}
                result = self.add(self.entry("a"), entry)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertTrue(result.stderr.startswith("invalid entry 2: "), result.stderr)
                self.assertFalse(self.queue_file().exists())

    def test_add_refuses_a_file_that_is_not_a_list_of_objects(self):
        for text in ("{", "{}", "[1]"):
            with self.subTest(text):
                path = self.tmp / "bad.json"
                path.write_text(text)
                result = run(self.repo, "queue", "add", "--file", str(path))
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertFalse(self.queue_file().exists())

    def test_add_reports_a_waiting_duplicate(self):
        self.add(self.entry("a"))
        result = self.add(self.entry("a"), self.entry("b"))
        self.assertEqual((result.returncode, result.stdout), (0, "added\tb\n"))
        self.assertIn("skipped: a: already waiting", result.stderr)
        self.assertEqual([e["slug"] for e in self.queue()], ["a", "b"])

    def test_add_reports_a_duplicate_in_the_same_file(self):
        result = self.add(self.entry("a"), self.entry("a", row="2"))
        self.assertIn("skipped: a: already waiting", result.stderr)
        self.assertEqual([e["row"] for e in self.queue()], ["a"])

    def test_add_sorts_blockers_first_and_keeps_typed_order(self):
        self.add(self.entry("c", after=["b"]), self.entry("a"), self.entry("b", after=["a"]))
        self.assertEqual([e["slug"] for e in self.queue()], ["a", "b", "c"])

    def test_add_keeps_typed_order_without_links(self):
        self.add(self.entry("b"), self.entry("a"))
        self.assertEqual([e["slug"] for e in self.queue()], ["b", "a"])

    def test_add_appends_after_existing_entries(self):
        self.add(self.entry("b"))
        self.add(self.entry("a"))
        self.assertEqual([e["slug"] for e in self.queue()], ["b", "a"])

    def test_add_skips_a_gate_cycle_and_a_self_gate(self):
        result = self.add(self.entry("a", after=["b"]), self.entry("b", after=["a"]),
                          self.entry("c", after=["c"]))
        self.assertEqual((result.returncode, result.stdout), (0, ""))
        for slug in "abc":
            self.assertIn(f"skipped: {slug}: gate cycle", result.stderr)
        self.assertEqual(self.queue(), [])

    def test_add_labels_a_row_behind_a_gate_cycle(self):
        self.add(self.entry("a", after=["b"]))
        result = self.add(self.entry("b", after=["a"]), self.entry("c", after=["b"]))
        self.assertEqual((result.returncode, result.stdout), (0, ""))
        self.assertIn("skipped: b: gate cycle", result.stderr)
        self.assertIn("skipped: c: behind a gate cycle", result.stderr)
        self.assertNotIn("skipped: c: gate cycle", result.stderr)
        self.assertEqual([e["slug"] for e in self.queue()], ["a"])

    def test_add_prunes_only_what_d4_allows(self):
        def hand(slug, state, after=(), reason=""):
            return {"row": slug, "slug": slug, "spec": spec(slug), "stage": "code",
                    "after": list(after), "exclusive": False, "spec_hash": "x",
                    "state": state, "reason": reason}
        run(self.repo, "set", "s1", "next=finished")
        run(self.repo, "set", "s2", "next=code")
        self.queue_file().parent.mkdir(parents=True, exist_ok=True)
        self.queue_file().write_text(json.dumps([
            hand("s1", "started"), hand("s2", "started"), hand("s3", "started"),
            hand("k1", "skipped", reason="dropped by the user"),
            hand("k2", "skipped", reason="dropped by the user"),
            hand("w", "waiting", after=["k1"])]))
        self.add(self.entry("a"))
        self.assertEqual([e["slug"] for e in self.queue()], ["s2", "s3", "k1", "w", "a"])

    def test_readded_slug_replaces_its_skipped_entry_and_goes_first(self):
        self.add(self.entry("a"), self.entry("b", after=["a"]))
        run(self.repo, "queue", "drop", "a")
        result = self.add(self.entry("a"))
        self.assertEqual(result.stdout, "added\ta\n")
        self.assertEqual([(e["slug"], e["state"]) for e in self.queue()],
                         [("a", "waiting"), ("b", "waiting")])

    def test_old_skipped_entry_stays_when_the_readd_is_a_cycle(self):
        self.add(self.entry("a"), self.entry("b", after=["a"]))
        run(self.repo, "queue", "drop", "a")
        result = self.add(self.entry("a", after=["c"]), self.entry("c", after=["a"]))
        self.assertIn("skipped: a: gate cycle", result.stderr)
        self.assertEqual([(e["slug"], e["state"]) for e in self.queue()],
                         [("a", "skipped"), ("b", "waiting")])

    def test_add_refuses_an_unreadable_queue(self):
        self.queue_file().parent.mkdir(parents=True)
        self.queue_file().write_text("{")
        result = self.add(self.entry("a"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("refused: the queue file is not valid JSON", result.stderr)
        self.assertEqual(self.queue_file().read_text(), "{")

    def test_add_from_a_worktree_writes_the_common_queue(self):
        result = run(self.worktree, "queue", "add", "--file",
                     str(self.entries_file(self.entry("a"))))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([e["slug"] for e in self.queue()], ["a"])


class QueueDropTest(QueueTestCase):
    def test_drop_marks_waiting_entries_skipped(self):
        self.add(self.entry("a"), self.entry("b"))
        self.assertEqual(run(self.repo, "queue", "drop", "a", "b").returncode, 0)
        self.assertEqual([(e["state"], e["reason"]) for e in self.queue()],
                         [("skipped", "dropped by the user")] * 2)

    def test_drop_refuses_a_slug_that_is_not_waiting(self):
        self.add(self.entry("a"))
        before = self.queue_file().read_text()
        result = run(self.repo, "queue", "drop", "a", "zz")
        self.assertEqual(result.returncode, 1)
        self.assertIn("refused: zz is not waiting", result.stderr)
        self.assertEqual(self.queue_file().read_text(), before)

    def test_drop_refuses_an_unreadable_queue(self):
        self.queue_file().parent.mkdir(parents=True)
        self.queue_file().write_text("{")
        result = run(self.repo, "queue", "drop", "a")
        self.assertEqual(result.returncode, 1)
        self.assertIn("refused: the queue file is not valid JSON", result.stderr)
        self.assertEqual(self.queue_file().read_text(), "{")


class WalkTestCase(QueueTestCase):
    def pull(self, n, cwd=None):
        result = run(cwd or self.repo, "pull", "--max", str(n))
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def show(self):
        result = run(self.repo, "queue", "show")
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def finish(self, slug, stopped=""):
        run(self.repo, "set", slug, "next=finished", f"stopped={stopped}")

    def live_run(self, slug):
        slot = len(list((self.repo / ".git" / "my-handoff").glob("*.json"))) + 1
        run(self.repo, "set", slug, "next=code", f"slot={slot}")

    def reset(self):
        shutil.rmtree(self.repo / ".git" / "my-handoff", ignore_errors=True)


class PullTest(WalkTestCase):
    def test_no_queue_file_prints_nothing(self):
        self.assertEqual((self.pull(1).returncode, self.pull(1).stdout), (0, ""))
        self.assertFalse(self.queue_file().exists())

    def test_start_writes_the_state_and_marks_the_entry(self):
        self.add(self.entry("a"))
        result = self.pull(1)
        self.assertEqual(result.stdout, f"a\tcode\t{spec('a')}\t1\n")
        self.assertEqual(self.get_state("a"), {
            "spec": spec("a"), "task_doc": spec("a"), "next": "code", "branch": "",
            "worktree": "", "squash_subject": "", "head_before_fold": "",
            "stopped": "", "checked_base": "", "slot": "1", "merge_retries": "0"})
        self.assertEqual(self.queue()[0]["state"], "started")

    def test_plan_stage_task_doc_is_the_plan_path(self):
        self.add(self.entry("a", stage="plan"))
        self.pull(1)
        self.assertEqual(self.get_state("a")["task_doc"], "docs/plans/2026-10-13-a.md")

    def test_rule1_changed_or_missing_spec_is_skipped(self):
        self.add(self.entry("a"), self.entry("b"))
        (self.repo / spec("a")).write_text("changed\n")
        (self.repo / spec("b")).unlink()
        result = self.pull(2)
        self.assertEqual(result.stdout, "")
        self.assertIn("skipped: a: spec changed since the call", result.stderr)
        self.assertIn("skipped: b: spec changed since the call", result.stderr)
        self.assertEqual([(e["state"], e["reason"]) for e in self.queue()],
                         [("skipped", "spec changed since the call")] * 2)

    def test_rule2_blocker_skipped_ended_or_unknown(self):
        cases = {"skipped entry": lambda: run(self.repo, "queue", "drop", "a"),
                 "ended by the user": lambda: (self.pull(1),
                                               self.finish("a", "ended by the user"))}
        for name, make in cases.items():
            with self.subTest(name):
                self.reset()
                self.add(self.entry("a"), self.entry("b", after=["a"]))
                make()
                result = self.pull(1)
                self.assertIn("skipped: b: blocker a did not finish", result.stderr)
                self.assertEqual(result.stdout, "")
        self.reset()
        self.add(self.entry("b", after=["zz"]))
        result = self.pull(1)
        self.assertIn("skipped: b: blocker zz did not finish", result.stderr)

    def test_rule3_waiting_entry_stops_the_walk(self):
        self.live_run("a")
        self.add(self.entry("b", after=["a"]), self.entry("c"))
        self.assertEqual(self.pull(3).stdout, "")
        self.assertEqual([e["state"] for e in self.queue()], ["waiting", "waiting"])

    def test_rule3_ready_once_the_blocker_finished(self):
        self.live_run("a")
        self.add(self.entry("b", after=["a"]))
        self.finish("a")
        self.assertTrue(self.pull(2).stdout.startswith("b\t"))

    def test_rule4_exclusive_entry_waits_for_no_live_run(self):
        self.live_run("x")
        self.add(self.entry("a", exclusive=True))
        self.assertEqual(self.pull(2).stdout, "")

    def test_rule4_nothing_starts_beside_a_live_exclusive_run(self):
        self.add(self.entry("a", exclusive=True))
        self.assertTrue(self.pull(2).stdout.startswith("a\t"))
        self.add(self.entry("b"))
        self.assertEqual(self.pull(2).stdout, "")

    def test_rule4_walk_stops_after_starting_an_exclusive_entry(self):
        self.add(self.entry("a", exclusive=True), self.entry("b"))
        self.assertEqual([l.split("\t")[0] for l in self.pull(2).stdout.splitlines()], ["a"])

    def test_rule5_cap_stops_the_walk(self):
        self.add(self.entry("a"), self.entry("b"), self.entry("c"))
        lines = self.pull(2).stdout.splitlines()
        self.assertEqual([(l.split("\t")[0], l.split("\t")[3]) for l in lines],
                         [("a", "1"), ("b", "2")])
        self.assertEqual(self.queue()[2]["state"], "waiting")

    def test_rule6_existing_run_is_skipped_and_the_walk_goes_on(self):
        self.add(self.entry("a"), self.entry("b"))
        self.live_run("a")
        result = self.pull(3)
        self.assertIn("skipped: a: a run for a exists", result.stderr)
        self.assertTrue(result.stdout.startswith("b\t"))
        self.assertEqual(self.get_state("a")["next"], "code")

    def test_rule6_a_row_that_cannot_start_fresh_is_skipped_and_the_walk_goes_on(self):
        cases = {
            "plan": lambda: (self.repo / "docs/plans/2026-10-20-a.md").write_text("plan\n"),
            "branch": lambda: git(self.repo, "branch", "feat/a"),
            "worktree": lambda: (self.repo / ".claude" / "worktrees" / "a").mkdir(parents=True),
        }
        for what, make in cases.items():
            with self.subTest(what):
                self.reset()
                make()
                self.add(self.entry("a"), self.entry("b"))
                result = self.pull(3)
                self.assertIn(f"skipped: a: {what} for a exists", result.stderr)
                self.assertTrue(result.stdout.startswith("b\t"), result.stdout)
                self.assertEqual(run(self.repo, "get", "a").returncode, 1)
                self.assertEqual(self.queue()[0]["state"], "skipped")
                if what == "plan":
                    (self.repo / "docs/plans/2026-10-20-a.md").unlink()
                elif what == "branch":
                    git(self.repo, "branch", "-D", "feat/a")
                else:
                    shutil.rmtree(self.repo / ".claude")

    def test_rule6_a_longer_slug_with_a_plan_does_not_block(self):
        (self.repo / "docs/plans/2026-10-20-x-a.md").write_text("plan\n")
        self.add(self.entry("a"))
        self.assertTrue(self.pull(1).stdout.startswith("a\t"))

    def test_pull_drops_a_finished_started_entry_before_its_walk(self):
        self.add(self.entry("a", exclusive=True))
        self.pull(2)
        self.finish("a")
        self.pull(2)
        self.assertEqual(self.queue(), [])
        self.live_run("a")
        self.add(self.entry("b"))
        self.assertTrue(self.pull(2).stdout.startswith("b\t"))

    def test_pull_from_a_worktree_reads_the_main_checkout(self):
        self.add(self.entry("a"))
        self.assertFalse((self.worktree / spec("a")).exists())
        self.assertTrue(self.pull(1, cwd=self.worktree).stdout.startswith("a\t"))

    def test_unreadable_queue_refuses(self):
        self.queue_file().parent.mkdir(parents=True)
        self.queue_file().write_text("{")
        result = run(self.repo, "pull", "--max", "1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("refused: the queue file is not valid JSON", result.stderr)
        self.assertEqual(self.queue_file().read_text(), "{")
        self.assertEqual(list((self.repo / ".git" / "my-handoff").glob("*.json")), [])


class ShowTest(WalkTestCase):
    def test_none_without_a_queue(self):
        self.assertEqual(self.show().stdout, "none\n")

    def test_none_when_nothing_waits(self):
        self.add(self.entry("a"))
        self.pull(1)
        self.assertEqual(self.show().stdout, "none\n")

    def test_ready_writes_nothing(self):
        self.add(self.entry("a"))
        before = self.queue_file().read_bytes()
        self.assertEqual(self.show().stdout, "ready\ta\n")
        self.assertEqual(self.queue_file().read_bytes(), before)
        self.assertEqual(run(self.repo, "get", "a").returncode, 1)

    def test_waits_for_a_blocker(self):
        self.live_run("a")
        self.add(self.entry("b", after=["a"]))
        self.assertEqual(self.show().stdout, "waits\tb\ta\n")

    def test_waits_for_a_live_exclusive_run(self):
        self.add(self.entry("a", exclusive=True))
        self.pull(2)
        self.add(self.entry("b"))
        self.assertEqual(self.show().stdout, "waits\tb\texclusive a\n")

    def test_exclusive_entry_waits_for_live_runs(self):
        self.live_run("x")
        self.add(self.entry("a", exclusive=True))
        self.assertEqual(self.show().stdout, "waits\ta\tlive runs\n")

    def test_passes_over_an_entry_pull_would_skip(self):
        self.add(self.entry("a"), self.entry("b"))
        (self.repo / spec("a")).write_text("changed\n")
        before = self.queue_file().read_bytes()
        result = self.show()
        self.assertEqual((result.stdout, result.stderr), ("ready\tb\n", ""))
        self.assertEqual(self.queue_file().read_bytes(), before)

    def test_ignores_the_cap(self):
        for slug in ("x", "y", "z"):
            self.live_run(slug)
        self.add(self.entry("a"))
        self.assertEqual(self.show().stdout, "ready\ta\n")

    def test_unreadable_queue_refuses(self):
        self.queue_file().parent.mkdir(parents=True)
        self.queue_file().write_text("{")
        result = run(self.repo, "queue", "show")
        self.assertEqual(result.returncode, 1)
        self.assertIn("refused: the queue file is not valid JSON", result.stderr)


if __name__ == "__main__":
    unittest.main()
