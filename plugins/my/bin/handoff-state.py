#!/usr/bin/env python3
"""Keep the state of an autonomous my:handoff run, and check it against git.

The state of the run for <slug> is one JSON file,
`<git common dir>/my-handoff/<slug>.json`. It lives outside the work tree, so
`git status` never shows it. Run the script from anywhere inside the repository
or one of its worktrees.

Usage:
    handoff-state.py set <slug> <field>=<value> ...   write fields
    handoff-state.py get <slug>                       print the state
    handoff-state.py check <slug>                     compare the state with git

Fields: spec, task_doc, branch, worktree, next, squash_subject,
head_before_fold, stopped. `next` is one of plan, code, review, merge,
worktree-remove, fold, done, finished. An empty value is allowed, as in
`stopped=`. `set` writes a temporary file in the same folder, then renames it
over the state file, so a crash never leaves half a file.

`check` prints one mismatch per line: no rebase, merge, cherry-pick or
uncommitted squash in progress in the main checkout, every field that `next`
needs is set, then the facts `next` needs. When `next` is merge and the
squash commit is already on the base branch, the merge happened before a
crash: when worktree-remove's fields and facts also match, it prints
`merge done` and sets `next` to worktree-remove. Otherwise it writes nothing.
When `head_before_fold` is set and is no longer on the base branch, a fold
rewrote history, and `check` refuses. The base branch is the branch checked
out in the main checkout.

Exit codes:
    0  done; for check, everything matches
    1  get or check found no state file; check found a mismatch
    2  usage error, unknown field or unknown next (nothing written)
"""

import json
import os
import re
import subprocess
import sys
import tempfile

FIELDS = ("spec", "task_doc", "branch", "worktree", "next", "squash_subject",
          "head_before_fold", "stopped")
STEPS = ("plan", "code", "review", "merge", "worktree-remove", "fold", "done",
         "finished")
NEEDS = {
    "plan": ("spec",),
    "code": ("task_doc",),
    "review": ("branch", "worktree"),
    "merge": ("branch", "squash_subject"),
    "worktree-remove": ("branch", "worktree", "squash_subject"),
    "fold": ("branch", "worktree", "squash_subject"),
    "done": ("spec", "task_doc", "squash_subject"),
    "finished": (),
}
IN_PROGRESS = ("rebase-merge", "rebase-apply", "MERGE_HEAD", "CHERRY_PICK_HEAD",
               "REVERT_HEAD", "SQUASH_MSG")
SLUG = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
FIXUP = "fixup! "


class GitError(Exception):
    pass


def git(*args, cwd=None, check=True):
    """Run git and return its stdout without the last newline."""
    command = ["git", "-c", "log.showSignature=false", *args]
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.rstrip("\n")


def common_dir():
    return git("rev-parse", "--path-format=absolute", "--git-common-dir")


def state_path(slug):
    return os.path.join(common_dir(), "my-handoff", f"{slug}.json")


def read_state(slug):
    path = state_path(slug)
    if not os.path.exists(path):
        return None
    with open(path) as handle:
        return json.load(handle)


def write_state(slug, state):
    path = state_path(slug)
    folder = os.path.dirname(path)
    os.makedirs(folder, exist_ok=True)
    handle = tempfile.NamedTemporaryFile("w", dir=folder, prefix=f".{slug}.",
                                         suffix=".tmp", delete=False)
    try:
        with handle:
            json.dump(state, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(handle.name, path)
    except BaseException:
        os.unlink(handle.name)
        raise


def set_fields(slug, pairs):
    updates = {}
    for pair in pairs:
        field, _, value = pair.partition("=")
        if field not in FIELDS:
            print(f"unknown field: {field}", file=sys.stderr)
            return 2
        if field == "next" and value not in STEPS:
            print(f"unknown next: {value}", file=sys.stderr)
            return 2
        updates[field] = value
    state = read_state(slug) or {}
    state.update(updates)
    write_state(slug, state)
    return 0


class Repo:
    """The main checkout and its base branch, as seen from the current directory."""

    def __init__(self):
        self.git_dir = common_dir()
        self.root = os.path.dirname(self.git_dir)
        self.base = git("branch", "--show-current", cwd=self.root)

    def run(self, *args, check=True):
        return git(*args, cwd=self.root, check=check)

    def path(self, value):
        return os.path.realpath(os.path.join(self.root, value))

    def has_branch(self, branch):
        return bool(self.run("rev-parse", "--verify", "-q", f"refs/heads/{branch}",
                             check=False))

    def worktrees(self):
        """Listed worktrees, as {real path: branch name or ""}."""
        listed = {}
        for block in self.run("worktree", "list", "--porcelain").split("\n\n"):
            lines = block.splitlines()
            path = next((l[9:] for l in lines if l.startswith("worktree ")), None)
            branch = next((l[7:] for l in lines if l.startswith("branch ")), "")
            if path:
                listed[os.path.realpath(path)] = branch.removeprefix("refs/heads/")
        return listed

    def squash_commits(self, state):
        """Commits on the base branch, not on the work branch, with the squash subject."""
        args = [self.base, "--not", state["branch"]] if self.has_branch(state["branch"]) \
            else [self.base]
        rows = self.run("log", "--format=%H%x00%s", *args, "--").splitlines()
        return [sha for sha, _, subject in (r.partition("\0") for r in rows)
                if subject == state["squash_subject"]]

    def waiting_fixups(self, path):
        added = self.run("log", "--diff-filter=A", "--format=%H", "-1", self.base,
                         "--", path)
        if not added:
            return []
        subject = self.run("log", "-1", "--format=%s", added)
        rows = self.run("log", "--format=%h%x00%s", f"{added}..{self.base}").splitlines()
        return [f"{sha} {s}" for sha, _, s in (r.partition("\0") for r in rows)
                if s == FIXUP + subject]


def facts(repo, state, step):
    """Mismatches between the state for `step` and git."""
    if step in ("code", "merge", "worktree-remove", "fold", "done") and not repo.base:
        return ["no base branch"]
    lines = []
    if step == "plan":
        if not os.path.isfile(repo.path(state["spec"])):
            lines.append(f"spec missing: {state['spec']}")
    elif step == "code":
        if not repo.run("log", "-1", "--format=%h", repo.base, "--", state["task_doc"]):
            lines.append(f"task doc not committed on {repo.base}: {state['task_doc']}")
    elif step == "review":
        if not repo.has_branch(state["branch"]):
            lines.append(f"branch missing: {state['branch']}")
        elif repo.worktrees().get(repo.path(state["worktree"])) != state["branch"]:
            lines.append(f"worktree not on {state['branch']}: {state['worktree']}")
    elif step == "merge":
        if not repo.has_branch(state["branch"]):
            lines.append(f"branch missing: {state['branch']}")
            lines.append(f"no squash commit: {state['squash_subject']}")
        if repo.run("diff", "--cached", "--name-only"):
            lines.append("staged changes in the main checkout")
    elif step in ("worktree-remove", "done"):
        found = len(repo.squash_commits(state))
        if found == 0:
            lines.append(f"no squash commit: {state['squash_subject']}")
        elif found > 1:
            lines.append(f"squash subject matches {found} commits")
    elif step == "fold":
        if not repo.squash_commits(state):
            lines.append(f"no squash commit: {state['squash_subject']}")
        if repo.path(state["worktree"]) in repo.worktrees():
            lines.append(f"worktree still listed: {state['worktree']}")
        before = state.get("head_before_fold")
        if before:
            try:
                repo.run("merge-base", "--is-ancestor", before, repo.base)
            except GitError:
                lines.append(f"history rewritten: head_before_fold {before} "
                             f"is not on {repo.base}")
    if step == "done":
        for path in dict.fromkeys((state["spec"], state["task_doc"])):
            lines += [f"fixup waits: {row}" for row in repo.waiting_fixups(path)]
    return lines


def missing(state, step):
    return [f"missing field: {f}" for f in NEEDS[step] if not state.get(f)]


def check(slug):
    state = read_state(slug)
    if state is None:
        print(f"no state for {slug}")
        return 1
    step = state.get("next", "")
    if step not in STEPS:
        print(f"unknown next: {step}")
        return 1
    repo = Repo()
    lines = [f"in progress: {name}" for name in IN_PROGRESS
             if os.path.exists(os.path.join(repo.git_dir, name))]
    lines += missing(state, step)
    if not lines and step == "merge" and repo.squash_commits(state):
        step = "worktree-remove"
        lines += missing(state, step) or facts(repo, state, step)
        if not lines:
            print("merge done")
            state["next"] = step
            write_state(slug, state)
    elif not missing(state, step):
        lines += facts(repo, state, step)
    for line in lines:
        print(line)
    return 1 if lines else 0


def usage():
    block = __doc__[__doc__.index("Usage:"):].split("\n\n")[0]
    print(block, file=sys.stderr)
    return 2


def main(argv):
    if argv in (["-h"], ["--help"]):
        print(__doc__)
        return 0
    if len(argv) < 2 or not SLUG.fullmatch(argv[1]):
        return usage()
    command, slug, rest = argv[0], argv[1], argv[2:]
    if command == "set" and (not rest or any("=" not in pair for pair in rest)):
        return usage()
    if command in ("get", "check") and rest:
        return usage()
    try:
        if command == "set":
            return set_fields(slug, rest)
        if command == "get":
            state = read_state(slug)
            if state is None:
                print(f"no state for {slug}", file=sys.stderr)
                return 1
            print(json.dumps(state, indent=2, sort_keys=True))
            return 0
        if command == "check":
            return check(slug)
    except GitError as error:
        print(error, file=sys.stderr)
        return 1
    return usage()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
