# Spec: `locked-commit.py`, one script for the locked commit

**Status:** approved, 2026-10-12. Replaces the five copies of the locked commit command with one
script that reads the message from a file.

## How to read this spec

1. `docs/reports/2026-10-12-handoff-instructions-audit.md`, finding P3, and P5 for the term
   *locked commit*. Where this work comes from. D6 corrects one claim of P3.
2. `ROADMAP.md`, section "Order of work" and the row "One script for the locked commit". The
   order puts this spec before the P4 and P5 trims.
3. `docs/plans/2026-10-12-parallel-auto-runs-spec.md`. Where the lock `main` and the locked
   commit were designed: why every commit in the main checkout of a parallel project runs under
   one lock.
4. `plugins/my/bin/handoff-lock.py` and its `--help`. The lock the new script uses. Its exit
   codes are part of the new script's contract (D2).
5. `plugins/my/tests/test_handoff_lock.py`. The test style the new tests copy.
6. The five files that hold the command today: `global/CLAUDE.md:173`,
   `global/rules/docs-layout.md:168`–`178`, `plugins/my/commands/commit.md:11`,
   `plugins/my/skills/architect/SKILL.md:248`–`256`, and
   `plugins/my/skills/handoff/SKILL.md:565`–`588`.

## Context

In a project whose `CLAUDE.md` or `CLAUDE.local.md` has a "Parallel runs" section, every commit
in the main checkout runs under lock `main`. Today that is one long shell command:

```bash
handoff-lock.py main -- sh -c 'm=$1; shift; git add -- "$@" && git commit -m "$m" -- "$@" && git show --stat --format= HEAD' sh "$(cat <<'EOF'
<message>
EOF
)" <paths>
```

The command is copied word for word into five files. The copies match today, but a fix to one
must be made in all five. The message goes in through a quoted heredoc, so that an apostrophe,
a backtick or `$(` in it does not run. A heredoc ends only on a line that is exactly `EOF`, so
`my:handoff` adds a rule that the message lines start at column 0.

## Goal

- One script, `locked-commit.py`, does the locked commit. Each of the five copies becomes one
  line.
- The message reaches git from a file, so no shell reads it, and the locked commit needs no
  heredoc and no column-0 rule.
- The lock, its timeout and its exit codes stay exactly as they are.

## Out of scope

- **The two merge commands keep their heredoc.** The squash-merge in a parallel project
  (`my:handoff` review stage, sub-step 1, `SKILL.md:822`) and `handoff-state.py merge -m`
  (`SKILL.md:895`) are not commits of paths. Giving them a message file changes the interface of
  `handoff-state.py`. That is the new 💭 row "Merges read a message file".
- **Other P4 and P5 edits.** Only the cross-reference "the locked form of Plan stage, step 7"
  changes here, because this spec removes what it points to.
- **Commits outside a parallel project, and commits in a worktree.** They take no lock and stay
  as they are.

## Decisions

### D1. The interface

```text
locked-commit.py [--timeout <seconds>] -F <message file> <path> ...
```

- `-F <message file>` is required. The file holds the whole commit message.
- `<path> ...` is one or more paths, relative to the current folder, as `git add` takes them.
  A deleted path is committed as a deletion.
- `--timeout` is passed to `handoff-lock.py` unchanged. Without it, `handoff-lock.py`'s default
  of 90 seconds applies.
- `-h` and `--help` print the docstring and exit 0, as `handoff-lock.py` does.

### D2. The script hands the lock to `handoff-lock.py`

The script checks its input (D3), then replaces itself with:

```text
handoff-lock.py main [--timeout <s>] -- sh -c '<steps>' sh <message file> <path> ...
```

The steps, in order, each only if the one before succeeded:

1. `git add -- <paths>`
2. `git commit -F <message file> -- <paths>`
3. `git show --stat --format= HEAD`
4. delete the message file

`handoff-lock.py` is found next to the script (`Path(__file__).parent`), not on `PATH`.

Why: `handoff-state.py start` and `merge` take the same lock through `handoff-lock.py main`. One
implementation keeps the lock file path, the `autoDetach` settings and the exit codes in one
place. Exit 75 still means "the lock wait timed out, nothing ran", which `my:handoff` stop row 18
relies on.

`git commit -- <paths>` commits only those paths. Anything else already staged stays staged and
stays out of the commit, as with today's command. Step 3 runs inside the lock, so its list is
the commit this command made, even when another run commits right after.

The lock is named `main` even when the base branch is named `master`. It is a lock name, not a
branch name.

### D3. Input checks before the lock

The script refuses with exit 64, a line on stderr that starts with `locked-commit:`, and no
command run, when:

- `-F` or the paths are missing, or an option is unknown;
- the message file does not exist, cannot be read, or holds only whitespace;
- the message file is inside the current repository's work tree, that is, under the folder
  `git rev-parse --show-toplevel` prints. A file there would make the main checkout dirty, and
  `my:status` would report it as uncommitted work that needs the user.

Outside a git repository, `git rev-parse` fails, and the script exits 64 too.

### D4. Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Committed. The stat is printed. The message file is deleted. |
| 64 | Input refused (D3), or `handoff-lock.py`'s own usage error. Nothing ran. |
| 74, 75, 126, 127 | As in `handoff-lock.py --help`. Nothing ran. |
| other | A git step failed under the lock, with git's own code. The message file is kept. |

"Nothing to commit" is a git failure (exit 1): the message file is kept.

### D5. Where the agent writes the message

The instructions say: write the message with the Write tool to a new file in the session's
scratchpad, then run `locked-commit.py -F <that file> <paths>`.

- Each session has its own scratchpad, so parallel runs cannot write the same file.
- The script deletes the file after a commit succeeds (D2, step 4). This matters because the
  Write tool refuses to overwrite a file it has not read. A file left from an earlier commit
  would block the next one with the same name.
- The file is kept when the commit fails, so the message is not lost.

### D6. The column-0 rule leaves the commit, not the skill

The audit (P3) said the script makes the column-0 heredoc rule unneeded. That holds only for
the locked commit. The rule has three uses in `my:handoff/SKILL.md`, and two belong to the merge
commands that keep their heredoc (Out of scope). So:

- the rule and its reasons leave Plan stage, step 7 (`SKILL.md:578`–`583`);
- the rule moves, in one sentence, to the squash-merge command (`SKILL.md:828`), which is now its
  first use;
- `SKILL.md:901` points to it there instead of to Plan stage, step 7.

The roadmap row is corrected to match, and the new 💭 row records the rest. Both roadmap edits
go into the commit that adds this spec, not into the code branch.

### D7. The new text of each copy

Each copy says, in its own file's words: in the main checkout of a project with a "Parallel
runs" section, write the message to a new file in the scratchpad, then run
`locked-commit.py -F <file> <paths>`; before it, read `git diff -- <paths>` and each new file
whole; after it, read the `git show --stat` list it printed.

- `global/CLAUDE.md:173`: the command and the two heredoc sentences become the line above. The
  sentence about fixups and the one about worktrees stay.
- `global/rules/docs-layout.md:168`–`178`: the code block becomes
  `locked-commit.py -F <message file> <paths>`, and "with the message in a quoted heredoc so that
  nothing in it runs" goes.
- `plugins/my/commands/commit.md:11`: the command and the heredoc clause become the line above.
  It also says that, in this case, step 4 writes the message to the file instead of the
  heredoc that step 4 (`commit.md:19`) asks for.
- `plugins/my/skills/architect/SKILL.md:248`–`256`: the code block becomes the new command, with
  `<message file>` holding `docs(plans): add architecture brief for <SLUG>`.
- `plugins/my/skills/handoff/SKILL.md:565`–`588`: the code block becomes the new command; the
  paragraph keeps the stat check and "A lock timeout is row 18", and drops the heredoc and
  column-0 text (D6).
- "the locked form of Plan stage, step 7" at `SKILL.md:683`, `:837` and `:913` becomes "with
  `locked-commit.py`". `README.md:361`–`363` says the same in its own words, and its list of
  locked commands adds the script.
- `README.md` (repo root), the paragraph on `plugins/my/bin/`: one sentence for the script.
- `plugins/my/skills/handoff/SKILL.md`, stop row 23: "Any other failure of `handoff-lock.py` or
  `handoff-state.py merge`" becomes "Any other failure of `handoff-lock.py`, `locked-commit.py`
  or `handoff-state.py merge`". The action stays: stop, with the script's message in the stop
  line. Row 18 does not change: a lock timeout still comes from `handoff-lock.py`, with exit 75
  and its `handoff-lock:` line.

## Trade-offs

- **Message file against stdin heredoc.** A heredoc on stdin is one tool call, but keeps the
  column-0 rule. A file costs one Write call per commit, and no shell ever reads the message.
  The user chose the file.
- **Hand off to `handoff-lock.py` against taking the lock in the script.** Taking it directly
  would avoid an `exec` and a `sh -c`. It would also copy the lock path and the `autoDetach`
  settings into a second file, and two copies of a lock can drift apart with no error: both
  scripts would think they hold the lock. One lock implementation wins.
- **Commit only against commit and both merges.** Covering the merges would remove the heredoc
  from `my:handoff` entirely, but changes `handoff-state.py`, which auto runs depend on, and
  makes this a Large change. The user chose commit only.

## Dependencies

None. Python standard library, `sh` and git. `handoff-lock.py` already ships in the same folder.

## Risk

1. **The locked commit is shared.** Every commit in the main checkout of a parallel project goes
   through it. A bug stops or corrupts all of them. The end-to-end tests run the real script
   against a real repository, including the message with shell characters and the lock timeout.
2. **An agent may still write a heredoc.** Old habits or a stale copy elsewhere would keep the
   old form working: `handoff-lock.py` itself does not change. That costs nothing but length.
   Detection: `git grep "handoff-lock.py main -- sh -c 'm=\$1" -- global plugins README.md`
   finds no copy after Task 4.
3. **The scratchpad may be missing.** A session without a scratchpad has nowhere obvious to write
   the file. Every Claude Code session has one today. If not, any folder outside the repository
   works, and D3 refuses a file inside it.
4. **Projects that use the old command keep working.** `zitamu` and other projects read the
   global files, which change in this branch. A session that loaded the old text before the
   change still runs the old command, which still works.
5. **The `README.md` and audit line numbers drift.** The line numbers in this spec are from
   2026-10-12, at commit `0386275`. The code stage finds each site by its text, not its
   number.

## Testing

`plugins/my/tests/test_locked_commit.py`, run with the whole suite:
`python3 -m unittest discover plugins/my/tests`. Each test runs the real script in a throwaway
repository, without the user's git config, as `test_handoff_lock.py` does. Task 5 rehearses the
new text with a headless `/my:commit` in a scratch project that has a "Parallel runs" section.

## Delegation

- **Dependencies:** `none`
- **Design-changing findings:** `stop`
- **Failing end-of-branch tests:** `none`
- **End-of-branch checks:** `python3 -m unittest discover plugins/my/tests`

## Files

- Create: `plugins/my/bin/locked-commit.py` (executable), `plugins/my/tests/test_locked_commit.py`.
- Modify: `global/CLAUDE.md`, `global/rules/docs-layout.md`, `plugins/my/commands/commit.md`,
  `plugins/my/skills/architect/SKILL.md`, `plugins/my/skills/handoff/SKILL.md`,
  `plugins/my/skills/handoff/README.md`, `README.md`.

## Tasks

Run in a worktree of `claude-setup`. Commit type `feat`, scope `my-plugin`.

### Task 1: tests (Red)

File: `plugins/my/tests/test_locked_commit.py`.

Helpers, no bodies here: `clean_env(extra={}) -> dict` and `git(repo, *args, check=True) -> str`
(as in `test_handoff_lock.py`); `make_repo(tmp) -> Path` (git init on `main`, user set, one root
commit); `message(tmp, text) -> Path` (writes the message file outside the repository);
`run(repo, *args, timeout=30) -> CompletedProcess` (runs `bin/locked-commit.py` in `repo`).

```python
def test_message_with_shell_characters_is_verbatim(self):
    text = "docs: it's `x` and $(id)\n\nbody line\n"
    r = run(repo, "-F", msg, "a.md")
    assert r.returncode == 0
    assert git(repo, "log", "-1", "--format=%B") == text.strip()

def test_prints_stat_of_its_commit(self):
    r = run(repo, "-F", msg, "a.md")
    assert " a.md | " in r.stdout
    assert git(repo, "show", "--stat", "--format=", "HEAD") in r.stdout

def test_other_staged_file_stays_staged(self):
    # b.md staged before the run; a.md is the path given
    run(repo, "-F", msg, "a.md")
    assert git(repo, "show", "--name-only", "--format=", "HEAD") == "a.md"
    assert git(repo, "diff", "--cached", "--name-only") == "b.md"

def test_deleted_path_committed_as_deletion(self):
    # c.md committed earlier, then removed from disk
    run(repo, "-F", msg, "c.md")
    assert git(repo, "show", "--name-status", "--format=", "HEAD") == "D\tc.md"

def test_message_file_deleted_after_success(self):
    run(repo, "-F", msg, "a.md")
    assert not msg.exists()

def test_message_file_kept_when_commit_fails(self):
    # a.md unchanged: nothing to commit
    r = run(repo, "-F", msg, "a.md")
    assert r.returncode != 0 and msg.exists()

def test_refuses_without_paths(self):
    assert_refused(run(repo, "-F", msg))

def test_refuses_without_message_file_option(self):
    assert_refused(run(repo, "a.md"))

def test_refuses_missing_message_file(self):
    assert_refused(run(repo, "-F", tmp / "nope", "a.md"))

def test_refuses_blank_message_file(self):
    # message file holds " \n\n"
    assert_refused(run(repo, "-F", blank, "a.md"))

def test_refuses_message_file_inside_work_tree(self):
    # message file at repo / "msg.txt"
    assert_refused(run(repo, "-F", repo / "msg.txt", "a.md"))

def test_refuses_outside_repository(self):
    assert_refused(run(tmp_not_repo, "-F", msg, "a.md"))

def test_lock_timeout_exits_75_and_commits_nothing(self):
    # holder: handoff-lock.py main -- sleep 5, started first
    r = run(repo, "--timeout", "0", "-F", msg, "a.md")
    assert r.returncode == 75
    assert git(repo, "rev-parse", "HEAD") == head_before
    assert msg.exists()
```

`assert_refused(r)` checks `r.returncode == 64`, that stderr starts with `locked-commit:`, and
that `HEAD` and the index did not change. Each test must fail first because the script does not
exist.

### Task 2: the script (Green)

File: `plugins/my/bin/locked-commit.py`, executable, with a docstring holding a Usage block and
the exit codes of D4, in the style of `handoff-lock.py`.

Functions: `fail(code, message) -> int`, `parse(argv) -> tuple | None` (timeout, message file,
paths), `check_message(path) -> str | None` (the refusal reason, or `None`),
`main(argv) -> int`. `main` ends in `os.execv` of `handoff-lock.py` as in D2.

All Task 1 tests pass. Run the whole suite.

### Task 3: `my:handoff`

File: `plugins/my/skills/handoff/SKILL.md` and `README.md` in its folder, as D6 and D7 say.
After the edit, the column-0 rule appears once, at the squash-merge command, and `SKILL.md:901`
points to it. Stop row 23 names `locked-commit.py`, as D7 says.

### Task 4: the other copies

Files: `global/CLAUDE.md`, `global/rules/docs-layout.md`, `plugins/my/commands/commit.md`,
`plugins/my/skills/architect/SKILL.md`, and the repo-root `README.md`, as D7 says. Then:

- `git grep -n "sh -c 'm=\$1" -- global plugins README.md` prints nothing.
- `git grep -n "locked form of Plan stage" -- global plugins README.md` prints nothing.

  Both greps leave out `docs/`: older plans, reviews and the audit quote the old text as a
  record.
- `markdownlint-cli2` on every changed `.md` file reports 0 errors.

### Task 5: rehearsal

No repo change. Make a scratch repository with a `CLAUDE.md` holding a `## Parallel runs`
heading, and one changed file. Run `/my:commit` headless in it with the plugin dir added:
`claude -p "/my:commit" --add-dir <scratch dir> --add-dir <plugin dir>`, asking for a message
with a backtick in its body. Pass: the session ran `locked-commit.py`,
and the commit exists with the message as asked. `git status --porcelain`
prints nothing, and no message file is left in the scratch repository.
Record the result in the squash commit message.

## Open questions

None.
