#!/usr/bin/env python3
"""Print the facts my:status judges: roadmap rows, open documents, the main
checkout, worktrees, auto runs and branches that may hold unmerged work.

The script reads and never writes. Run it from anywhere inside the repository
or one of its worktrees. The base branch is the branch checked out in the main
checkout, as in handoff-state.py.

Usage:
    status-scan.py

The output is plain text in blocks, in this order: roadmap, order, docs,
checkout, worktrees, runs, branches. Each block starts with a line
`== <name>`. Each fact is one line, with fields separated by one tab. An empty
block prints one line, `none`. When a block's source cannot be read, the block
prints one line `error`, tab, the reason, and the next block still prints.

    roadmap    icon, row number or -, title, docs/plans/ links or -, row text
    order      a line of the `## Order of work` section
    docs       status or no-status, date or -, path
    checkout   dirty, path; or fixup, fixup hash, target hash or ?, target subject
    worktrees  path, branch, commits ahead of the base, clean or dirty
    runs       slug, slot, next, stop line, branch; - for an empty field
    branches   maybe-unfinished, branch, missing line count, last subject;
               then skipped, count, when more than 30 branches qualify

A branch is maybe-unfinished when one of its added lines, or one of its
deleted lines, of 8 or more characters, was never added (or deleted) by a
commit on the base branch since the branch split off.

Exit codes:
    0  every block printed, including error lines
    2  not inside a git repository, no branch checked out in the main
       checkout, or a usage error
"""

import glob
import json
import os
import re
import subprocess
import sys

ICONS = ("✅", "🚧", "📋", "💭")
OPEN_STATUSES = ("draft", "approved", "planned", "current", "parked")
DOC_FOLDERS = ("docs/plans", "docs/reports")
FIXUP = "fixup! "
FIXUP_DEPTH = 200
MIN_LINE = 8
BULLET = re.compile(r"- (\S+) \*\*(.+?)\*\*")
TITLE = re.compile(r"\*\*(.+?)\*\*")
PLAN_LINK = re.compile(r"\((docs/plans/[^)\s#]+)")
STATUS = re.compile(r"\*\*Status:\*\*\s*([A-Za-z-]+)(.*)")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
HERE = os.path.dirname(os.path.abspath(__file__))


class GitError(Exception):
    pass


def git(*args, cwd=None):
    """Run git and return its stdout without the last newline."""
    command = ["git", "-c", "log.showSignature=false", "-c", "core.quotePath=false",
               *args]
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        reason = result.stderr.strip() or f"exit {result.returncode}"
        raise GitError(f"git {' '.join(args)}: {reason}")
    return result.stdout.rstrip("\n")


def main_root():
    common = git("rev-parse", "--path-format=absolute", "--git-common-dir")
    return common, os.path.dirname(common)


def base_branch(root):
    return git("branch", "--show-current", cwd=root)


def roadmap_rows(text):
    """Open rows, as (icon, number, title, links, text)."""
    rows = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        bullet = BULLET.match(line)
        if bullet and bullet.group(1) in ICONS:
            parts = [line.strip()]
            for more in lines[index + 1:]:
                if not more.strip() or not more[0].isspace():
                    break
                parts.append(more.strip())
            rows.append((bullet.group(1), "-", bullet.group(2), " ".join(parts)))
        elif line.startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            icon = next((cell for cell in cells[2:] if cell in ICONS), None)
            title = TITLE.match(cells[1]) if len(cells) > 1 else None
            if icon and title and cells[0]:
                rows.append((icon, cells[0], title.group(1), line.strip()))
    result = []
    for icon, number, title, whole in rows:
        if icon == "✅":
            continue
        links = list(dict.fromkeys(PLAN_LINK.findall(whole)))
        result.append((icon, number, title, " ".join(links) or "-", whole))
    return result


def order_lines(text):
    lines, inside = [], False
    for line in text.splitlines():
        if re.match(r"#{1,2} ", line):
            inside = line.strip() == "## Order of work"
        elif inside and line.strip():
            lines.append(line.rstrip())
    return lines


def doc_states(root):
    """Open documents, and documents with no status line, as (status, date, path)."""
    states = []
    for folder in DOC_FOLDERS:
        for path in sorted(glob.glob(os.path.join(root, folder, "*.md"))):
            with open(path, encoding="utf-8") as handle:
                head = [handle.readline() for _ in range(10)]
            found = next((STATUS.match(l) for l in head if STATUS.match(l)), None)
            relative = os.path.relpath(path, root)
            if found is None:
                states.append(("no-status", "-", relative))
            elif found.group(1) in OPEN_STATUSES:
                date = DATE.search(found.group(2))
                states.append((found.group(1), date.group(0) if date else "-", relative))
    return states


def checkout_facts(root, base):
    facts = []
    entries = git("status", "--porcelain", "-z", cwd=root).split("\0")
    skip = False
    for entry in entries:
        if skip or not entry:
            skip = False
            continue
        facts.append(("dirty", entry[3:]))
        skip = entry[0] in "RC" or entry[1] in "RC"
    rows = git("log", f"-{FIXUP_DEPTH}", "--format=%H%x00%s", base, cwd=root)
    commits = [row.split("\0", 1) for row in rows.splitlines()]
    for index, (sha, subject) in enumerate(commits):
        if not subject.startswith(FIXUP):
            continue
        target_subject = subject
        while target_subject.startswith(FIXUP):
            target_subject = target_subject[len(FIXUP):]
        target = next((s for s, subj in commits[index + 1:] if subj == target_subject),
                      "?")
        facts.append(("fixup", sha, target, target_subject))
    return facts


def worktree_list(root):
    """Listed worktrees, as [(path, branch or "")], the main checkout first."""
    listed = []
    for chunk in git("worktree", "list", "--porcelain", cwd=root).split("\n\n"):
        lines = chunk.splitlines()
        path = next((l[9:] for l in lines if l.startswith("worktree ")), None)
        branch = next((l[7:] for l in lines if l.startswith("branch ")), "")
        if path:
            listed.append((path, branch.removeprefix("refs/heads/")))
    return listed


def worktree_facts(root, base):
    facts = []
    for path, branch in worktree_list(root)[1:]:
        if not os.path.isdir(path):
            facts.append((path, branch or "-", "-", "missing"))
            continue
        ahead = git("rev-list", "--count", f"{base}..HEAD", cwd=path)
        dirty = git("status", "--porcelain", cwd=path)
        facts.append((path, branch or "-", ahead, "dirty" if dirty else "clean"))
    return facts


def run_facts(common):
    """Auto runs whose next is not finished: slug, slot, next, stop line, branch."""
    live = subprocess.run([sys.executable, os.path.join(HERE, "handoff-state.py"), "live"],
                          capture_output=True, text=True)
    if live.returncode == 0:
        rows = [(line.split("\t") + [""] * 5)[:5] for line in live.stdout.splitlines()]
        broken = [row[0] for row in rows if row[2] == "unreadable"]
        if broken:
            raise ValueError(f"state file is not valid JSON: {broken[0]}.json")
    elif live.returncode == 2:
        rows = []
        for path in sorted(glob.glob(os.path.join(common, "my-handoff", "*.json"))):
            slug = os.path.basename(path)[:-len(".json")]
            if slug.startswith("."):
                continue
            try:
                with open(path, encoding="utf-8") as handle:
                    state = json.load(handle)
            except ValueError:
                raise ValueError(f"state file is not valid JSON: {slug}.json")
            if state.get("next") == "finished":
                continue
            rows.append([slug] + [str(state.get(key, "")) for key in
                                  ("slot", "next", "stopped", "branch")])
    else:
        raise ValueError(f"handoff-state.py live: {live.stderr.strip()}")
    return [tuple(field or "-" for field in row) for row in rows]


def changed_lines(diff):
    """Added and deleted lines of a -U0 patch, stripped, of MIN_LINE or more characters."""
    added, deleted, in_hunk = [], [], False
    for line in diff.splitlines():
        if line.startswith("diff --git"):
            in_hunk = False
        elif line.startswith("@@"):
            in_hunk = True
        elif in_hunk and line[:1] in "+-":
            text = line[1:].strip()
            if len(text) >= MIN_LINE:
                (added if line[0] == "+" else deleted).append(text)
    return added, deleted


def branch_facts(root, base, limit=30):
    checked_out = {branch for _, branch in worktree_list(root) if branch}
    rows = git("for-each-ref", "--sort=-committerdate",
               "--format=%(refname:lstrip=2)%00%(subject)", "refs/heads/", cwd=root)
    candidates = []
    for row in rows.splitlines():
        branch, subject = row.split("\0", 1)
        if branch == base or branch in checked_out:
            continue
        if git("rev-list", "--count", f"{base}..refs/heads/{branch}", cwd=root) != "0":
            candidates.append((branch, subject))
    facts, seen = [], {}
    for branch, subject in candidates[:limit]:
        try:
            fork = git("merge-base", base, f"refs/heads/{branch}", cwd=root)
            since = f"{fork}..{base}"
        except GitError:
            # No shared history: compare with every change main ever made.
            fork = git("hash-object", "-t", "tree", os.devnull, cwd=root)
            since = base
        if fork not in seen:
            patch = git("log", "-p", "-U0", "--root", "--no-color", "--no-ext-diff",
                        "--format=", since, cwd=root)
            added, deleted = changed_lines(patch)
            seen[fork] = (set(added), set(deleted))
        main_added, main_deleted = seen[fork]
        added, deleted = changed_lines(git("diff", "-U0", "--no-color", "--no-ext-diff",
                                           fork, f"refs/heads/{branch}", cwd=root))
        missing = sum(1 for l in added if l not in main_added) + \
            sum(1 for l in deleted if l not in main_deleted)
        if missing:
            facts.append(("maybe-unfinished", branch, str(missing), subject))
    if len(candidates) > limit:
        facts.append(("skipped", str(len(candidates) - limit)))
    return facts


def print_block(name, rows):
    print(f"== {name}")
    if not rows:
        print("none")
    for row in rows:
        if isinstance(row, str):
            row = (row,)
        print("\t".join(str(field).replace("\t", " ") for field in row))


def read_roadmap(root):
    path = os.path.join(root, "ROADMAP.md")
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def usage():
    block = __doc__[__doc__.index("Usage:"):].split("\n\n")[0]
    print(block, file=sys.stderr)
    return 2


def main(argv):
    if argv in (["-h"], ["--help"]):
        print(__doc__)
        return 0
    if argv:
        return usage()
    try:
        common, root = main_root()
    except GitError:
        print("status-scan.py: not inside a git repository", file=sys.stderr)
        return 2
    base = base_branch(root)
    if not base:
        print("status-scan.py: no branch is checked out in the main checkout",
              file=sys.stderr)
        return 2
    blocks = [
        ("roadmap", lambda: roadmap_rows(read_roadmap(root))),
        ("order", lambda: order_lines(read_roadmap(root))),
        ("docs", lambda: doc_states(root)),
        ("checkout", lambda: checkout_facts(root, base)),
        ("worktrees", lambda: worktree_facts(root, base)),
        ("runs", lambda: run_facts(common)),
        ("branches", lambda: branch_facts(root, base)),
    ]
    for name, collect in blocks:
        try:
            rows = collect()
        except (GitError, OSError, ValueError) as error:
            rows = [("error", str(error).replace("\n", " "))]
        print_block(name, rows)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
