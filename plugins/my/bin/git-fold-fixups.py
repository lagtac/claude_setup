#!/usr/bin/env python3
"""Fold waiting fixup commits on the current branch, or check that a fixup is safe.

A fixup is a commit whose subject starts with `fixup! `. Its target is the one
older commit, on the first-parent history, whose subject is the rest of the line.
The fold runs `git rebase -i --autosquash` without an editor, and only when it
is safe. Otherwise it refuses, prints one line that says why, and changes nothing.

Usage:
    git-fold-fixups.py              fold every waiting fixup on the current branch
    git-fold-fixups.py check SHA    is a fixup of SHA safe? (the fold would accept it)

A worktree holds a commit when it has a branch, or a detached HEAD, that
contains the commit. `check` runs the fold's rules on the fixup that
`git commit --fixup SHA` would make. When SHA is itself a fixup, that is SHA's
own target. It leaves out the rules that do not depend on SHA: uncommitted
changes (the fixup's own edits are not committed yet when `check` runs), a
rebase, merge or cherry-pick in progress, and other waiting fixups.

The fold refuses when a rebase, merge or cherry-pick is in progress; when a
tracked file has uncommitted changes; when a fixup has no target, or more than
one; when another worktree holds a target; when a target is already on the
upstream, or the upstream is configured but its ref is missing; and when the
range holds a merge, `squash!` or `amend!` commit.

Exit codes:
    0  folded, nothing to fold, or safe
    1  refused, nothing changed (the reason is on stderr)
    2  usage error
    3  the rebase finished but a check after it failed; history is rewritten,
       and the old HEAD is printed so that `git reset --hard <old HEAD>` undoes it

The script never pushes, never resets, and never deletes a branch.
"""

import os
import subprocess
import sys

FIXUP = "fixup! "


class GitError(Exception):
    pass


def git(*args, check=True, env=None):
    """Run git in the current directory and return its stdout without the last newline."""
    command = ["git", "-c", "log.showSignature=false", *args]
    result = subprocess.run(command, capture_output=True, text=True, env=env)
    if check and result.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.rstrip("\n")


def short(sha):
    return sha[:7]


def strip_fixup(subject):
    while subject.startswith(FIXUP):
        subject = subject[len(FIXUP):]
    return subject


def held_branches(sha):
    """Other worktrees that hold SHA, as (holder, worktree path) pairs. The
    holder is "branch <name>", or "a detached HEAD" for a worktree with no
    branch checked out, such as one in the middle of a rebase."""
    here = os.path.realpath(git("rev-parse", "--show-toplevel"))
    rows = git(
        "for-each-ref", "--contains", sha, "refs/heads",
        "--format=%(refname:short)%00%(worktreepath)",
    )
    held = []
    for row in rows.splitlines():
        branch, _, path = row.partition("\0")
        if path and os.path.realpath(path) != here:
            held.append((f"branch {branch}", path))
    for block in git("worktree", "list", "--porcelain").split("\n\n"):
        fields = dict(line.partition(" ")[::2] for line in block.splitlines())
        path, head = fields.get("worktree"), fields.get("HEAD")
        if "detached" not in fields or not path or os.path.realpath(path) == here:
            continue
        if is_ancestor(sha, head):
            held.append(("a detached HEAD", path))
    return held


def is_ancestor(sha, ref):
    return subprocess.run(["git", "merge-base", "--is-ancestor", sha, ref], capture_output=True).returncode == 0


def upstream():
    """The upstream's short name, or None when the branch has none. Raises
    GitError when an upstream is configured but its ref is missing."""
    head = git("symbolic-ref", "-q", "HEAD", check=False)
    name = git("for-each-ref", "--format=%(upstream:short)", head) if head else ""
    if not name:
        return None
    if not git("rev-parse", "--verify", "-q", name, check=False):
        raise GitError(f"refused: upstream {name} is configured but missing; fetch it or unset it")
    return name


def target_refusal(target, up):
    """Why a fixup of TARGET is not safe because of other worktrees or the
    upstream UP, or None."""
    for holder, path in held_branches(target):
        return f"target {short(target)} is held by {holder}, checked out in {path}"
    if up and is_ancestor(target, up):
        return f"target {short(target)} is already pushed to {up}"
    return None


def first_parent_log():
    """(hash, subject) pairs on the first-parent history of HEAD, newest first."""
    out = git("log", "--first-parent", "--format=%H%x00%s", "HEAD")
    return [tuple(line.split("\0", 1)) for line in out.splitlines()]


def waiting_fixups():
    """(fixup hash, candidate target hashes) for each waiting fixup, newest first.
    No candidate means no target; two or more mean an ambiguous one."""
    log = first_parent_log()
    up = upstream()
    unpushed = set(git("rev-list", f"{up}..HEAD").splitlines()) if up else None
    fixups = []
    for index, (sha, subject) in enumerate(log):
        if not subject.startswith(FIXUP) or (unpushed is not None and sha not in unpushed):
            continue
        wanted = strip_fixup(subject)
        candidates = [
            older for older, older_subject in log[index + 1:]
            if older_subject == wanted
        ]
        fixups.append((sha, candidates))
    return fixups


def in_progress():
    for name in ("rebase-merge", "rebase-apply", "MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD"):
        if os.path.exists(git("rev-parse", "--git-path", name)):
            return True
    return False


def oldest_target(targets):
    """The oldest of TARGETS. HEAD's first-parent log is newest first, so it is
    the target that comes last in it."""
    order = {sha: index for index, (sha, _) in enumerate(first_parent_log())}
    return max(targets, key=order.__getitem__)


def parent(sha):
    return git("rev-parse", "--verify", "-q", f"{sha}^", check=False) or None


def range_args(oldest):
    """The rev-list arguments for the commits from OLDEST to HEAD, OLDEST included."""
    base = parent(oldest)
    return [f"{base}..HEAD"] if base else ["HEAD"]


def refusal(fixups):
    """The reason the fold is not safe, or None. The first rule that applies wins."""
    if git("status", "--porcelain", "--untracked-files=no"):
        return "uncommitted changes to tracked files; commit or stash them first"
    for sha, candidates in fixups:
        subject = git("log", "-1", "--format=%s", sha)
        if not candidates:
            return f"fixup {short(sha)} ({subject}) has no target"
        if len(candidates) > 1:
            names = ", ".join(short(c) for c in candidates)
            return (
                f"fixup {short(sha)} has an ambiguous target: "
                f"{names} share the subject '{strip_fixup(subject)}'"
            )
    return range_refusal({candidates[0] for _, candidates in fixups})


def range_refusal(targets):
    """Why folding into TARGETS is not safe because of other worktrees, the
    upstream, or the commits from the oldest target to HEAD, or None."""
    up = upstream()
    for target in targets:
        reason = target_refusal(target, up)
        if reason:
            return reason
    span = range_args(oldest_target(targets))
    merges = git("rev-list", "--merges", *span).splitlines()
    if merges:
        return f"merge commit {short(merges[0])} is in the range; the rebase would flatten it"
    for line in git("log", "--format=%H%x00%s", *span).splitlines():
        sha, subject = line.split("\0", 1)
        if subject.startswith(("squash! ", "amend! ")):
            return f"commit {short(sha)} ({subject}) is in the range; its rebase stops for an editor"
    return None


def check_refusal(sha):
    """Why a fixup of SHA is not safe, or None. The fixup's subject names the
    original target, so a fixup of a fixup folds into that target."""
    subject = git("log", "-1", "--format=%s", sha)
    wanted = strip_fixup(subject)
    log = first_parent_log()
    order = {older: index for index, (older, _) in enumerate(log)}
    if sha not in order:
        return f"no target: {short(sha)} is not on the first-parent history"
    candidates = [older for older, older_subject in log if older_subject == wanted]
    if not candidates:
        return f"no target: no commit on the first-parent history has the subject '{wanted}'"
    if len(candidates) > 1:
        names = ", ".join(short(c) for c in candidates)
        return f"ambiguous: {names} share the subject '{wanted}'"
    if order[candidates[0]] < order[sha]:
        return f"no target: fixup {short(sha)} is older than {short(candidates[0])} ({wanted})"
    return range_refusal(candidates)


def fold(fixups):
    before = git("rev-parse", "HEAD")
    oldest = oldest_target([candidates[0] for _, candidates in fixups])
    base = parent(oldest)
    env = dict(os.environ, GIT_SEQUENCE_EDITOR="true")
    command = ["-c", "rebase.updateRefs=false", "rebase", "-i", "--autosquash"]
    command += [base] if base else ["--root"]
    result = subprocess.run(["git", *command], capture_output=True, text=True, env=env)
    if result.returncode != 0:
        if in_progress():
            git("rebase", "--abort", check=False)
        if in_progress() or git("rev-parse", "HEAD", check=False) != before:
            print(f"the rebase failed and its abort did not restore HEAD. HEAD before was {before}", file=sys.stderr)
            print(result.stderr.strip(), file=sys.stderr)
            return 3
        print(f"refused: the rebase failed, HEAD is back at {short(before)}", file=sys.stderr)
        print(result.stderr.strip(), file=sys.stderr)
        return 1
    try:
        after = git("rev-parse", "HEAD")
        left = [
            line for line in git("log", "--format=%s", f"{base}..HEAD" if base else "HEAD").splitlines()
            if line.startswith(FIXUP)
        ]
        changed = bool(git("diff", before, "HEAD"))
    except GitError as error:
        print(f"rebased, but a check after it failed: {error}. HEAD before was {before}", file=sys.stderr)
        return 3
    if left:
        reason = f"{len(left)} fixup commits are still in the range"
    elif changed:
        reason = "the tree after the rebase differs from the tree before it"
    else:
        targets = {candidates[0] for _, candidates in fixups}
        print(
            f"folded {len(fixups)} fixups into {len(targets)} commits; "
            f"HEAD {short(before)} -> {short(after)}"
        )
        return 0
    print(f"rebased, but {reason}. HEAD before was {before}", file=sys.stderr)
    return 3


def usage():
    block = __doc__[__doc__.index("Usage:"):].split("\n\n")[0]
    print(block, file=sys.stderr)
    return 2


def main(argv):
    if argv in (["-h"], ["--help"]):
        print(__doc__)
        return 0
    if len(argv) not in (0, 2) or (argv and argv[0] != "check"):
        return usage()
    try:
        if argv:
            sha = git("rev-parse", "--verify", "-q", f"{argv[1]}^{{commit}}", check=False)
            if not sha:
                print(f"not a commit: {argv[1]}", file=sys.stderr)
                return usage()
            reason = check_refusal(sha)
            if reason:
                print(reason, file=sys.stderr)
                return 1
            return 0
        if in_progress():
            print("refused: a rebase, merge or cherry-pick is in progress", file=sys.stderr)
            return 1
        fixups = waiting_fixups()
        if not fixups:
            print("nothing to fold")
            return 0
        reason = refusal(fixups)
        if reason:
            print(f"refused: {reason}", file=sys.stderr)
            return 1
        return fold(fixups)
    except GitError as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
