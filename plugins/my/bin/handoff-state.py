#!/usr/bin/env python3
"""Keep the state of a my:handoff run, auto or supervised, and check it against git.

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
    handoff-state.py start <slug> --supervised <field>=<value> ...
                                                      start a supervised run, or take its slot again
    handoff-state.py merge <slug> -m <message> [--docs-paths <path> ...]
                                                      squash-merge the run's branch
    handoff-state.py queue add --file <path>          queue roadmap rows
    handoff-state.py queue drop <slug> ...            cancel waiting rows
    handoff-state.py queue show                       print what the queue waits for
    handoff-state.py pull --max <n>                   start waiting rows, if the cap allows

Fields: spec, task_doc, branch, worktree, next, squash_subject,
head_before_fold, stopped, slot, checked_base, merge_retries, mode. `next` is
one of plan, code, review, merge-retry, merge, worktree-remove, fold, done,
finished. `mode` is auto or supervised; a state without it is auto. An empty
value is allowed, as in `stopped=`. `set` writes a temporary file in
the same folder, then renames it over the state file, so a crash never leaves
half a file.

`live` prints one line per state file whose `next` is not finished, sorted by
slug, with six fields separated by tabs: slug, slot, next, stopped, branch,
mode. A missing field prints as empty, and a missing mode as auto. A file that
is not valid JSON prints its slug with `unreadable` as next and the other
fields empty, and counts as live.

`start` has two forms: `--max <n>` starts an auto run, and `--supervised`
a supervised one. Each writes `mode` itself, so a `mode=` pair is a usage
error. With no state of the same slug, or a finished one, it writes a fresh
state from the given fields, plus `mode`, `slot` and `merge_retries=0`, and
prints the slot: the lowest whole number from 1 that no live run uses, of
either mode. When the slug's own run is live:

    own run live   --max <n>                          --supervised
    auto           refused: a run for <slug> exists;  refused: an auto run for
                   use resume                         <slug> exists
    supervised     refused: a supervised run for      writes the given fields,
                   <slug> exists                      keeps the slot, prints it

An unreadable state of the same slug counts as auto. The auto form also
refuses when <n> auto runs are live; supervised runs never count toward the
cap, and an unreadable state does. A refusal writes nothing. Run
`start` under `handoff-lock.py main`, so that two starts cannot take the same
slot or both pass the cap.

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

The queue of `/my:handoff auto rows` is one JSON list,
`<git common dir>/my-handoff/queue/rows.json`, in a subfolder so that `live`
never counts it as a run. Each entry has the fields row, slug, spec, stage,
after, exclusive, spec_hash, state (waiting, started or skipped) and reason.
Write it only under `handoff-lock.py main`.

`queue add --file <path>` reads a JSON list of objects with exactly the keys
row (a non-empty string), spec (docs/plans/YYYY-MM-DD-<slug>-spec.md, present
in the main checkout), stage (plan or code), after (a list of slugs) and
exclusive (true or false). It derives slug from spec, hashes the spec in the
main checkout, and adds each entry as waiting. An invalid entry refuses the
whole file with `invalid entry <i>: <why>`, and a file that cannot be read or
is not a list with `invalid entries: <why>`. An entry whose slug is already
waiting is not added (`skipped: <slug>: already waiting`), nor is one that
waits in a loop (`skipped: <slug>: gate cycle`) or behind one
(`skipped: <slug>: behind a gate cycle`). An added slug replaces its
older skipped entries. The waiting entries are then sorted blockers first,
old ones first, otherwise in the given order. Last, it drops each started
entry whose run finished and each skipped entry that no waiting entry names in
after. It prints `added<TAB><slug>` per added entry, in queue order.

`queue drop <slug> ...` marks each named waiting entry skipped, with the
reason `dropped by the user`. It refuses, and changes nothing, when a slug is
not waiting.

`pull --max <n>` first drops each started entry whose run finished, as
`queue add` does. Then it walks the waiting entries in queue order. Rule 1:
an entry whose spec in the main checkout no longer hashes to spec_hash is skipped
(`spec changed since the call`). Rule 2: an entry is skipped
(`blocker <slug> did not finish`) when a slug in its after belongs to a
skipped entry, has a finished state with a non-empty stopped, or has neither
an entry nor a state file. Rule 3: an entry waits, and stops the walk, until
every slug in its after has a finished state with an empty stopped. Rule 4:
while a started exclusive entry's run is live, nothing starts; an exclusive
entry starts only when no run of either mode is live, and the walk stops after
it. Rule 5: the walk stops when <n> auto runs are live; an unreadable state
counts as auto. Rule 6: a start writes the state as
`start` does, marks the entry started and prints
`<slug><TAB><stage><TAB><spec><TAB><slot>`; when the slug's own run is live,
the entry is skipped (`a run for <slug> exists`); when the slug cannot start
fresh, because a plan docs/plans/<date>-<slug>.md, a branch */<slug> or a
directory .claude/worktrees/<slug> exists in the main checkout, the entry is
skipped (`<plan, branch or worktree> for <slug> exists`). Each skip prints
`skipped: <slug>: <reason>` on stderr. `pull` writes the queue once, when
something changed. Run it under `handoff-lock.py main`; it never takes that
lock itself. No queue file: no output.

`queue show` runs rules 1 to 4 and writes nothing. It ignores the cap. It
prints `ready<TAB><slug>` for the first entry that could start,
`waits<TAB><slug><TAB><what>` when that entry waits for a blocker's slug,
`exclusive <slug>` or `live runs`, and `none` when nothing waits.

Exit codes:
    0  done; for check, everything matches; for start, started; for merge, merged
    1  get or check found no state file; check found a mismatch; start (either
       form) or merge refused; queue drop refused; for queue add, queue drop,
       queue show and pull, the queue file is not valid JSON or git failed
    2  usage error, unknown field, unknown next, unknown mode, or an invalid
       queue entry (nothing written)
    4  merge: the base gained code since checked_base (nothing changed; the
       paths are on stderr)
    5  merge: the squash or its commit failed; `git reset --merge` ran, and
       next stays merge
"""

import functools
import json
import os
import re
import subprocess
import sys
import tempfile

FIELDS = ("spec", "task_doc", "branch", "worktree", "next", "squash_subject",
          "head_before_fold", "stopped", "slot", "checked_base", "merge_retries", "mode")
MODES = ("auto", "supervised")
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


@functools.cache
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


def write_json(path, data):
    """Write data as JSON through a temporary file in the same folder."""
    folder = os.path.dirname(path)
    os.makedirs(folder, exist_ok=True)
    name = os.path.basename(path)[:-len(".json")]
    handle = tempfile.NamedTemporaryFile("w", dir=folder, prefix=f".{name}.",
                                         suffix=".tmp", delete=False)
    try:
        with handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(handle.name, path)
    except BaseException:
        os.unlink(handle.name)
        raise


def write_state(slug, state):
    write_json(state_path(slug), state)


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
        if field == "mode" and value not in MODES:
            print(f"unknown mode: {value}", file=sys.stderr)
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
            print(f"{slug}\t\tunreadable\t\t\t")
            continue
        fields = (state.get(k, "") for k in ("slot", "next", "stopped", "branch"))
        print("\t".join((slug, *fields, state.get("mode", "auto"))))
    return 0


class Refused(Exception):
    """start_run refused; `exists` is True when the slug's own run is live."""

    def __init__(self, message, exists):
        super().__init__(message)
        self.message = message
        self.exists = exists


def is_auto(state):
    """True for an auto state, a state without mode, and an unreadable one (None)."""
    return state is None or state.get("mode", "auto") == "auto"


def start_run(slug, mode, cap, updates):
    """Write the state for slug and return its slot, or raise Refused.

    `cap` is the cap of an auto start, and None for a supervised one. A
    supervised start beside the slug's own live supervised run writes the
    fields into that state and keeps its slot."""
    live = live_states()
    own = next((state for other, state in live if other == slug), False)
    if own is not False:
        if mode == "auto":
            if is_auto(own):
                raise Refused(f"refused: a run for {slug} exists; use resume", True)
            raise Refused(f"refused: a supervised run for {slug} exists", True)
        if is_auto(own):
            raise Refused(f"refused: an auto run for {slug} exists", True)
        write_state(slug, {**own, **updates, "mode": "supervised"})
        return own.get("slot", "")
    if mode == "auto":
        auto = [other for other, state in live if is_auto(state)]
        if len(auto) >= cap:
            raise Refused(f"refused: {len(auto)} auto runs are live ({', '.join(auto)}); "
                          f"the most is {cap}", False)
    used = {state.get("slot") for _, state in live if state}
    slot = next(n for n in range(1, len(live) + 2) if str(n) not in used)
    write_state(slug, {**updates, "mode": mode, "slot": str(slot), "merge_retries": "0"})
    return str(slot)


def cap_arg(rest):
    """The cap from `--max <n>`, n at least 1, or None."""
    if len(rest) < 2 or rest[0] != "--max" or not rest[1].isdigit() or int(rest[1]) < 1:
        return None
    return int(rest[1])


def start_args(rest):
    """(mode, cap, pairs) from start's arguments after the slug, or None."""
    if rest[:1] == ["--supervised"]:
        mode, cap, pairs = "supervised", None, rest[1:]
    else:
        mode, cap, pairs = "auto", cap_arg(rest), rest[2:]
        if cap is None:
            return None
    if any("=" not in pair or pair.partition("=")[0] == "mode" for pair in pairs):
        return None
    return mode, cap, pairs


def start(slug, rest):
    parsed = start_args(rest)
    if parsed is None:
        return usage()
    mode, cap, pairs = parsed
    updates = parse_pairs(pairs)
    if updates is None:
        return 2
    try:
        print(start_run(slug, mode, cap, updates))
    except Refused as refusal:
        print(refusal.message, file=sys.stderr)
        return 1
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


QUEUE_KEYS = ("row", "spec", "stage", "after", "exclusive")
SPEC_PATH = re.compile(r"docs/plans/\d{4}-\d{2}-\d{2}-(.+)-spec\.md")


class QueueError(Exception):
    def __init__(self, path):
        super().__init__(f"refused: the queue file is not valid JSON: {path}")


def queue_path():
    return os.path.join(common_dir(), "my-handoff", "queue", "rows.json")


def read_queue():
    """The queue's entries, or [] when there is no queue file."""
    path = queue_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path) as handle:
            entries = json.load(handle)
    except (OSError, ValueError):
        raise QueueError(path)
    if not isinstance(entries, list) or not all(isinstance(e, dict) for e in entries):
        raise QueueError(path)
    return entries


def slug_of(spec):
    """The slug of a spec path docs/plans/YYYY-MM-DD-<slug>-spec.md, else None."""
    match = SPEC_PATH.fullmatch(spec)
    return match[1] if match and SLUG.fullmatch(match[1]) else None


def spec_hash(repo, spec):
    """`git hash-object` of the spec in the main checkout, or None when it is missing."""
    if not os.path.isfile(os.path.join(repo.root, spec)):
        return None
    return repo.run("hash-object", "--", spec)


def run_state(slug):
    """The state of a run, None without a state file, and a state whose next is
    `unreadable` for a file that is not valid JSON, which counts as live."""
    try:
        state = read_state(slug)
    except (OSError, ValueError):
        return {"next": "unreadable"}
    return state if state is None or isinstance(state, dict) else {"next": "unreadable"}


def entry_problem(entry, repo):
    """Why an entry of `queue add` is not valid, or None."""
    if not isinstance(entry, dict):
        return "not an object"
    unknown = sorted(set(entry) - set(QUEUE_KEYS))
    if unknown:
        return f"unknown key: {unknown[0]}"
    absent = [key for key in QUEUE_KEYS if key not in entry]
    if absent:
        return f"missing key: {absent[0]}"
    if not isinstance(entry["row"], str) or not entry["row"]:
        return "row is not a non-empty string"
    if not isinstance(entry["spec"], str) or slug_of(entry["spec"]) is None:
        return f"spec is not docs/plans/YYYY-MM-DD-<slug>-spec.md: {entry['spec']}"
    if entry["stage"] not in ("plan", "code"):
        return f"stage is not plan or code: {entry['stage']}"
    after = entry["after"]
    if not isinstance(after, list) or not all(isinstance(s, str) and SLUG.fullmatch(s)
                                              for s in after):
        return "after is not a list of slugs"
    if type(entry["exclusive"]) is not bool:
        return "exclusive is not true or false"
    if not os.path.isfile(os.path.join(repo.root, entry["spec"])):
        return f"spec missing in the main checkout: {entry['spec']}"
    return None


def blockers_first(entries):
    """(order, stuck): indexes of the entries in a stable order that puts each
    entry after the entries its `after` names, and the indexes it cannot place.
    Each round takes the earliest entry whose named entries are all placed."""
    slugs = {entry.get("slug") for entry in entries}
    order, placed, rest = [], set(), list(range(len(entries)))
    while True:
        index = next((i for i in rest
                      if all(s in placed or s not in slugs
                             for s in entries[i].get("after", []))), None)
        if index is None:
            return order, rest
        order.append(index)
        placed.add(entries[index].get("slug"))
        rest.remove(index)


def in_loop(entries, index):
    """True when entries[index] can reach itself through the `after` slugs of entries."""
    by_slug = {entry.get("slug"): entry for entry in entries}
    own = entries[index].get("slug")
    seen, todo = set(), list(entries[index].get("after", []))
    while todo:
        slug = todo.pop()
        if slug == own:
            return True
        if slug in seen or slug not in by_slug:
            continue
        seen.add(slug)
        todo.extend(by_slug[slug].get("after", []))
    return False


def prune(entries):
    """Drop each started entry whose run finished, and each skipped entry that no
    waiting entry names in `after`."""
    named = {slug for entry in entries if entry.get("state") == "waiting"
             for slug in entry.get("after", [])}
    kept = []
    for entry in entries:
        if entry.get("state") == "started":
            state = run_state(entry.get("slug", ""))
            if state and state.get("next") == "finished":
                continue
        if entry.get("state") == "skipped" and entry.get("slug") not in named:
            continue
        kept.append(entry)
    return kept


def queue_add(path):
    try:
        with open(path) as handle:
            entries = json.load(handle)
    except (OSError, ValueError) as error:
        print(f"invalid entries: cannot read {path}: {error}", file=sys.stderr)
        return 2
    if not isinstance(entries, list):
        print(f"invalid entries: {path} is not a JSON list", file=sys.stderr)
        return 2
    repo = Repo()
    for number, entry in enumerate(entries, 1):
        problem = entry_problem(entry, repo)
        if problem:
            print(f"invalid entry {number}: {problem}", file=sys.stderr)
            return 2
    queue = read_queue()
    waiting = [entry for entry in queue if entry.get("state") == "waiting"]
    seen = {entry.get("slug") for entry in waiting}
    new = []
    for entry in entries:
        slug = slug_of(entry["spec"])
        if slug in seen:
            print(f"skipped: {slug}: already waiting", file=sys.stderr)
            continue
        seen.add(slug)
        new.append({**entry, "slug": slug, "spec_hash": spec_hash(repo, entry["spec"]),
                    "state": "waiting", "reason": ""})
    _, stuck = blockers_first(waiting + new)
    stuck_entries = [(waiting + new)[i] for i in stuck]
    cycle = {i - len(waiting) for i in stuck if i >= len(waiting)}
    for i in sorted(cycle):
        loop = in_loop(stuck_entries, stuck_entries.index(new[i]))
        reason = "gate cycle" if loop else "behind a gate cycle"
        print(f"skipped: {new[i]['slug']}: {reason}", file=sys.stderr)
    new = [entry for i, entry in enumerate(new) if i not in cycle]
    pool = waiting + new
    order, stuck = blockers_first(pool)
    added = {entry["slug"] for entry in new}
    others = [entry for entry in queue if entry.get("state") != "waiting"
              and not (entry.get("state") == "skipped" and entry.get("slug") in added)]
    result = prune(others + [pool[i] for i in order + stuck])
    write_json(queue_path(), result)
    for entry in result:
        if any(entry is item for item in new):
            print(f"added\t{entry['slug']}")
    return 0


def queue_drop(slugs):
    queue = read_queue()
    waiting = {entry.get("slug") for entry in queue if entry.get("state") == "waiting"}
    for slug in slugs:
        if slug not in waiting:
            print(f"refused: {slug} is not waiting", file=sys.stderr)
            return 1
    for entry in queue:
        if entry.get("state") == "waiting" and entry.get("slug") in slugs:
            entry.update(state="skipped", reason="dropped by the user")
    write_json(queue_path(), queue)
    return 0


def walk(entries, repo, ready):
    """Apply rules 1 to 4 of `pull` to the waiting entries, in queue order.

    Skipped entries are marked in `entries`. `ready(entry)` is called for each
    entry that passes the rules, and returns False to stop the walk; it may mark
    the entry skipped. Returns (skip lines, wait), where wait is
    `<slug><TAB><what>` when an entry stopped the walk at rule 3 or 4, else None.
    """
    skips = []

    def skip(entry, reason):
        entry.update(state="skipped", reason=reason)
        skips.append(f"skipped: {entry.get('slug')}: {reason}")

    for entry in entries:
        if entry.get("state") != "waiting":
            continue
        slug = entry.get("slug")
        if spec_hash(repo, entry.get("spec", "")) != entry.get("spec_hash"):
            skip(entry, "spec changed since the call")
            continue
        states = {blocker: run_state(blocker) for blocker in entry.get("after", [])}
        failed = None
        for blocker, state in states.items():
            own = [e for e in entries if e.get("slug") == blocker]
            if (any(e.get("state") == "skipped" for e in own)
                    or (state and state.get("next") == "finished" and state.get("stopped"))
                    or (not own and state is None)):
                failed = blocker
                break
        if failed:
            skip(entry, f"blocker {failed} did not finish")
            continue
        open_blocker = next((b for b, state in states.items()
                             if not (state and state.get("next") == "finished"
                                     and not state.get("stopped"))), None)
        if open_blocker:
            return skips, f"{slug}\t{open_blocker}"
        live = [other for other, _ in live_states()]
        exclusive = next((e.get("slug") for e in entries
                          if e.get("state") == "started" and e.get("exclusive")
                          and e.get("slug") in live), None)
        if exclusive:
            return skips, f"{slug}\texclusive {exclusive}"
        if entry.get("exclusive") and live:
            return skips, f"{slug}\tlive runs"
        go_on = ready(entry)
        if entry.get("state") == "skipped":
            skips.append(f"skipped: {slug}: {entry.get('reason')}")
        if not go_on:
            break
    return skips, None


def plan_path(spec):
    """docs/plans/<date>-<slug>.md for docs/plans/<date>-<slug>-spec.md."""
    return spec[:-len("-spec.md")] + ".md"


def not_fresh(repo, slug):
    """What stops a fresh start of slug, as D2 checks it at call time: `plan`,
    `branch` or `worktree`; None when nothing does."""
    plans = os.path.join(repo.root, "docs", "plans")
    pattern = re.compile(r"\d{4}-\d{2}-\d{2}-" + re.escape(slug) + r"\.md")
    if os.path.isdir(plans) and any(pattern.fullmatch(name) for name in os.listdir(plans)):
        return "plan"
    if repo.run("branch", "--list", f"*/{slug}"):
        return "branch"
    if os.path.isdir(os.path.join(repo.root, ".claude", "worktrees", slug)):
        return "worktree"
    return None


def pull(cap):
    if not os.path.exists(queue_path()):
        return 0
    entries = read_queue()
    before = json.dumps(entries, sort_keys=True)
    entries = [entry for entry in entries if not (
        entry.get("state") == "started"
        and (run_state(entry.get("slug", "")) or {}).get("next") == "finished")]
    repo = Repo()
    started = []

    def ready(entry):
        states = live_states()
        live = [slug for slug, _ in states]
        # Rule 5 before rule 6: at the cap the walk stops without skipping the
        # entry, although start_run would refuse it too.
        if sum(1 for _, state in states if is_auto(state)) >= cap:
            return False
        slug, stage, spec = entry["slug"], entry["stage"], entry["spec"]
        what = None if slug in live else not_fresh(repo, slug)
        if what:
            entry.update(state="skipped", reason=f"{what} for {slug} exists")
            return True
        updates = {"spec": spec, "task_doc": spec if stage == "code" else plan_path(spec),
                   "next": stage, "branch": "", "worktree": "", "squash_subject": "",
                   "head_before_fold": "", "stopped": "", "checked_base": ""}
        try:
            slot = start_run(slug, "auto", cap, updates)
        except Refused as refusal:
            if refusal.exists:
                entry.update(state="skipped", reason=f"a run for {slug} exists")
                return True
            return False
        entry["state"] = "started"
        started.append(f"{slug}\t{stage}\t{spec}\t{slot}")
        return not entry.get("exclusive")

    skips, _ = walk(entries, repo, ready)
    if json.dumps(entries, sort_keys=True) != before:
        write_json(queue_path(), entries)
    for line in started:
        print(line)
    for line in skips:
        print(line, file=sys.stderr)
    return 0


def queue_show():
    entries = read_queue()
    first = []

    def ready(entry):
        first.append(entry["slug"])
        return False

    _, wait = walk(entries, Repo(), ready)
    if wait:
        print(f"waits\t{wait}")
    elif first:
        print(f"ready\t{first[0]}")
    else:
        print("none")
    return 0


def queue_command(rest):
    try:
        if len(rest) == 3 and rest[:2] == ["add", "--file"]:
            return queue_add(rest[2])
        if len(rest) >= 2 and rest[0] == "drop" and all(SLUG.fullmatch(s) for s in rest[1:]):
            return queue_drop(rest[1:])
        if rest == ["show"]:
            return queue_show()
    except (QueueError, GitError) as error:
        print(error, file=sys.stderr)
        return 1
    return usage()


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
    if argv[:1] == ["queue"]:
        return queue_command(argv[1:])
    if argv[:1] == ["pull"]:
        cap = cap_arg(argv[1:])
        if cap is None or len(argv) != 3:
            return usage()
        try:
            return pull(cap)
        except (QueueError, GitError) as error:
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
