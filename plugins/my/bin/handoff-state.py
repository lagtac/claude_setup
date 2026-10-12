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
    handoff-state.py live                             list the runs not finished
    handoff-state.py start <slug> --max <n> <field>=<value> ...
                                                      start a run, if the cap allows
    handoff-state.py merge <slug> -m <message> [--docs-paths <path> ...]
                                                      squash-merge the run's branch

Fields: spec, task_doc, branch, worktree, next, squash_subject,
head_before_fold, stopped, slot, checked_base, merge_retries. `next` is one of
plan, code, review, merge-retry, merge, worktree-remove, fold, done, finished.
An empty value is allowed, as in `stopped=`. `set` writes a temporary file in
the same folder, then renames it over the state file, so a crash never leaves
half a file.

`live` prints one line per state file whose `next` is not finished, sorted by
slug, with five fields separated by tabs: slug, slot, next, stopped, branch. A
missing field prints as empty. A file that is not valid JSON prints its slug
with `unreadable` as next and the other fields empty, and counts as live.

`start` writes a fresh state from the given fields, plus `slot` and
`merge_retries=0`, and prints the slot: the lowest whole number from 1 that no
live run uses. A finished state of the same slug is replaced. It refuses, and
writes nothing, when the slug's own run is live, or when <n> other runs are
live. Run it under `handoff-lock.py main`, so that two starts cannot both pass
the cap.

`check` prints one mismatch per line: no rebase, merge, cherry-pick or
uncommitted squash in progress in the main checkout, every field that `next`
needs is set, then the facts `next` needs. When `next` is merge and the
squash commit is already on the base branch, the merge happened before a
crash: when worktree-remove's fields and facts also match, it prints
`merge done` and sets `next` to worktree-remove. Otherwise it writes nothing.
When `head_before_fold` is set and is no longer on the base branch, a fold
rewrote history, and `check` refuses. The base branch is the branch checked
out in the main checkout.

`merge` runs in the main checkout, under `handoff-lock.py main`. It refuses,
and changes nothing, when a rebase, merge or cherry-pick is in progress, when
`branch` or `checked_base` is empty, when `next` is neither merge-retry nor
merge, or when the main checkout has staged changes. It exits 4 when
`git diff <checked_base> <base>` lists a path outside the docs paths: the base
gained code that the checks never saw. Otherwise it writes `squash_subject`
(the message's first line) and `next=merge`, runs `git merge --squash` and
`git commit`, writes `next=worktree-remove` and prints the squash commit's
short hash. --docs-paths comes last; without it, the docs paths are `docs/`,
`ROADMAP.md` and `CHANGELOG.md`. A path that ends in `/` is a folder.

Exit codes:
    0  done; for check, everything matches; for start, started; for merge, merged
    1  get or check found no state file; check found a mismatch; start or merge
       refused
    2  usage error, unknown field or unknown next (nothing written)
    4  merge: the base gained code since checked_base (nothing changed; the
       paths are on stderr)
    5  merge: the squash or its commit failed; `git reset --merge` ran, and
       next stays merge
"""

import json
import os
import re
import subprocess
import sys
import tempfile

FIELDS = ("spec", "task_doc", "branch", "worktree", "next", "squash_subject",
          "head_before_fold", "stopped", "slot", "checked_base", "merge_retries")
STEPS = ("plan", "code", "review", "merge-retry", "merge", "worktree-remove",
         "fold", "done", "finished")
NEEDS = {
    "plan": ("spec",),
    "code": ("task_doc",),
    "review": ("branch", "worktree"),
    "merge-retry": ("branch", "worktree", "checked_base"),
    "merge": ("branch", "squash_subject"),
    "worktree-remove": ("branch", "worktree", "squash_subject"),
    "fold": ("branch", "worktree", "squash_subject"),
    "done": ("spec", "task_doc", "squash_subject"),
    "finished": (),
}
IN_PROGRESS = ("rebase-merge", "rebase-apply", "MERGE_HEAD", "CHERRY_PICK_HEAD",
               "REVERT_HEAD", "SQUASH_MSG")
DOCS_PATHS = ("docs/", "ROADMAP.md", "CHANGELOG.md")
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


def parse_pairs(pairs):
    """The pairs as a dict, or None after printing why one is not valid."""
    updates = {}
    for pair in pairs:
        field, _, value = pair.partition("=")
        if field not in FIELDS:
            print(f"unknown field: {field}", file=sys.stderr)
            return None
        if field == "next" and value not in STEPS:
            print(f"unknown next: {value}", file=sys.stderr)
            return None
        updates[field] = value
    return updates


def set_fields(slug, pairs):
    updates = parse_pairs(pairs)
    if updates is None:
        return 2
    state = read_state(slug) or {}
    state.update(updates)
    write_state(slug, state)
    return 0


def live_states():
    """(slug, state) for each state file whose next is not finished, sorted by
    slug. The state is None for a file that is not valid JSON."""
    folder = os.path.join(common_dir(), "my-handoff")
    if not os.path.isdir(folder):
        return []
    live = []
    for name in sorted(os.listdir(folder)):
        if name.startswith(".") or not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(folder, name)) as handle:
                state = json.load(handle)
            if not isinstance(state, dict):
                state = None
        except (OSError, ValueError):
            state = None
        if state is None or state.get("next") != "finished":
            live.append((name[:-len(".json")], state))
    return live


def print_live():
    for slug, state in live_states():
        if state is None:
            print(f"{slug}\t\tunreadable\t\t")
            continue
        fields = (state.get(k, "") for k in ("slot", "next", "stopped", "branch"))
        print("\t".join((slug, *fields)))
    return 0


def start(slug, rest):
    if len(rest) < 2 or rest[0] != "--max" or not rest[1].isdigit() or int(rest[1]) < 1:
        return usage()
    cap, pairs = int(rest[1]), rest[2:]
    if any("=" not in pair for pair in pairs):
        return usage()
    updates = parse_pairs(pairs)
    if updates is None:
        return 2
    live = live_states()
    if any(other == slug for other, _ in live):
        print(f"refused: a run for {slug} exists; use resume", file=sys.stderr)
        return 1
    if len(live) >= cap:
        names = ", ".join(other for other, _ in live)
        print(f"refused: {len(live)} auto runs are live ({names}); the most is {cap}",
              file=sys.stderr)
        return 1
    used = {state.get("slot") for _, state in live if state}
    slot = next(n for n in range(1, len(live) + 2) if str(n) not in used)
    write_state(slug, {**updates, "slot": str(slot), "merge_retries": "0"})
    print(slot)
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
    elif step in ("review", "merge-retry"):
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


def is_docs_path(path, docs_paths):
    return any(path == entry or (entry.endswith("/") and path.startswith(entry))
               for entry in docs_paths)


def merge(slug, message, docs_paths):
    state = read_state(slug)
    if state is None:
        print(f"no state for {slug}", file=sys.stderr)
        return 1
    repo = Repo()
    reasons = [f"in progress: {name}" for name in IN_PROGRESS
               if os.path.exists(os.path.join(repo.git_dir, name))]
    reasons += [f"missing field: {f}" for f in ("branch", "checked_base") if not state.get(f)]
    if state.get("next") not in ("merge-retry", "merge"):
        reasons.append(f"next is {state.get('next', '')}, not merge-retry or merge")
    if not repo.base:
        reasons.append("no base branch")
    if not reasons and repo.run("diff", "--cached", "--name-only"):
        reasons.append("staged changes in the main checkout")
    if reasons:
        for reason in reasons:
            print(f"refused: {reason}", file=sys.stderr)
        return 1
    moved = repo.run("diff", "--name-only", "--no-renames", state["checked_base"],
                     repo.base).splitlines()
    code = [path for path in moved if not is_docs_path(path, docs_paths)]
    if code:
        print(f"{repo.base} gained code since checked_base: {', '.join(code)}",
              file=sys.stderr)
        return 4
    state.update(squash_subject=message.split("\n", 1)[0], next="merge")
    write_state(slug, state)
    for args in (("merge", "--squash", state["branch"]), ("commit", "-q", "-m", message)):
        result = subprocess.run(["git", *args], cwd=repo.root, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"git {args[0]} failed: {(result.stderr or result.stdout).strip()}",
                  file=sys.stderr)
            repo.run("reset", "--merge", check=False)
            if repo.run("status", "--porcelain", check=False):
                print("the main checkout is not clean after git reset --merge",
                      file=sys.stderr)
            return 5
    state["next"] = "worktree-remove"
    write_state(slug, state)
    print(repo.run("rev-parse", "--short", "HEAD"))
    return 0


def merge_args(rest):
    """(message, docs paths) from merge's arguments after the slug, or None."""
    if len(rest) < 2 or rest[0] != "-m":
        return None
    message, tail = rest[1], rest[2:]
    if not tail:
        return message, list(DOCS_PATHS)
    if tail[0] != "--docs-paths" or len(tail) < 2:
        return None
    return message, tail[1:]


def usage():
    block = __doc__[__doc__.index("Usage:"):].split("\n\n")[0]
    print(block, file=sys.stderr)
    return 2


def main(argv):
    if argv in (["-h"], ["--help"]):
        print(__doc__)
        return 0
    if argv == ["live"]:
        try:
            return print_live()
        except GitError as error:
            print(error, file=sys.stderr)
            return 1
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
        if command == "start":
            return start(slug, rest)
        if command == "merge":
            parsed = merge_args(rest)
            return merge(slug, *parsed) if parsed else usage()
    except GitError as error:
        print(error, file=sys.stderr)
        return 1
    return usage()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
