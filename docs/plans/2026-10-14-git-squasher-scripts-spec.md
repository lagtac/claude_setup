# Spec: `git-squash.py`, plan and apply scripts for `kit:git-squasher`

**Status:** draft, 2026-10-14. Drafted in a fork without the user; the
choices it made alone are listed in "Choices made without the user".

**Size: Medium.** One new script with its tests, and edits to one skill and
`README.md`. No stored data, permission, message contract or build changes.
The skill's arguments stay the same. The script is a new command-line
interface, but only this skill calls it, as with `locked-commit.py`.

## How to read this spec

1. `docs/reports/2026-10-14-scriptable-skill-steps.md`, finding S7, and B1 for
   the bug class. Where this work comes from. Also "Where scripts go, and the
   cost": a `kit` helper goes in `plugins/kit/bin`, and the prose a script
   replaces is deleted in the same change.
2. `ROADMAP.md`, rows 41 "`git-squasher` loses `$1`" and 46 "`git-squasher`
   plan and apply scripts", and "Order of work", which puts 41 before 46.
3. `plugins/kit/skills/git-squasher/SKILL.md`. The skill this spec changes.
   Line numbers below are from commit `e0bf1b1`, before row 41's fix.
4. `docs/plans/2026-10-12-locked-commit-spec.md`. The model for a script that
   reads a commit message from a file, so no shell reads it. Its D5 explains
   why the script deletes the file after success.
5. `plugins/my/bin/locked-commit.py` and `plugins/my/tests/test_locked_commit.py`.
   The script and test style the new files copy: a docstring with a Usage
   block and exit codes, throwaway repositories, git without user config.
6. `plugins/kit/tests/test_neutral_core.py`, `test_kit_cites_no_method`. It
   scans every file under `plugins/kit/`, so it also scans the new script.
7. `README.md`, section "`kit` skills", lines 127 to 149.

## Context

`kit:git-squasher` squashes runs of small consecutive commits (`fix:`,
`chore:`, `style:`, `docs:`) into one commit per run. Today all six steps
are prose that the model carries out by hand:

- Step 1 (`SKILL.md:23`–`49`) picks the range, makes a backup branch and runs
  three safety checks.
- Steps 2 and 3 (`SKILL.md:51`–`95`) sort each commit into squashable or
  boundary, and group runs of squashable commits.
- Step 4 (`SKILL.md:97`–`123`) shows the plan and asks the user.
- Step 5 (`SKILL.md:125`–`159`) writes a shell script, `squash-todo.sh`, that
  edits the rebase todo (the list of commands `git rebase -i` runs). Each
  group's message sits inside single quotes in a `sed` command.
- Step 6 (`SKILL.md:161`–`170`) checks that the file tree did not change.

Steps 1 to 3 and 5 to 6 follow fixed rules. They are the steps a script can
run. Step 5 also carries two known faults:

- **B1.** The `squash-todo.sh` example uses `"$1"` (`SKILL.md:147`). Claude
  Code replaces `$1` in a loaded skill with the skill's arguments. Row 41
  fixes this one line first.
- **The single-quote rule.** A message cannot hold `'`, because step 5 puts it
  inside single quotes (`SKILL.md:119`). A message read from a file needs no
  such rule.

Reading the steps for this spec found three more faults in the prose:

- **Pushed commits.** Step 1 finds unpushed commits with
  `git log origin/<branch>..HEAD 2>/dev/null` (`SKILL.md:41`). When the
  branch has no `origin/<branch>`, that prints nothing, so every commit looks
  pushed and the skill asks for a force-push confirmation it does not need.
- **Merge commits.** The skill says to skip merge commits and treat them as
  boundaries (`SKILL.md:185`). But `git rebase -i <base>` without
  `--rebase-merges` drops merge commits and replays their parents in a line.
  So a squash on a range with a merge flattens history the user did not ask
  to change.
- **Unlisted prefixes.** `perf:`, `build:`, `ci:` and `revert:` are in neither
  list (`SKILL.md:57`–`70`). Unprefixed "trivial messages" end in "etc."
  (`SKILL.md:62`), which leaves the call to the model.

## Goal

- One script, `plugins/kit/bin/git-squash.py`, runs the fixed rules:
  `plan` does steps 1 to 3 and prints the groups; `apply` does steps 5 and 6.
- `apply` reads each group's message from a file that the model writes with
  the Write tool. No shell reads a message, so `'`, `` ` `` and `$(` are
  committed as written.
- The skill keeps the judgment: it writes the combined messages, shows the
  plan, asks the user, and decides from the user's answer which groups to
  squash.
- The skill text holds no shell script, so the `$1` class of bug cannot come
  back to this skill.

## Out of scope

- **Writing the messages.** Combining several subjects into one message is
  judgment. The model still writes it (`SKILL.md:114`–`118`).
- **Ranges with merge commits.** `apply` refuses them (D6). Squashing around a
  merge with `--rebase-merges` is a later row, if anyone needs it.
- **Pushing, and deleting backup branches.** Both stay with the user, as
  today.
- **The skill's arguments.** `/kit:git-squasher [<base>] [--dry-run]` stays as
  it is (`SKILL.md:12`–`19`).
- **Row 33's half of B1** (`my:handoff`). It is a separate row.

## Decisions

### D1. One script with two subcommands

```text
git-squash.py plan [<base>] [--keep <hash>]... --out <plan file>
git-squash.py apply <plan file> <messages file> [--allow-pushed] [--allow-main]
git-squash.py todo <plan file> <messages file> <todo file>
```

- `plan` reads and never writes to the repository. It prints the plan
  (D3) and writes the plan file (D4).
- `apply` changes history (D5).
- `todo` is the rebase's sequence editor. `apply` sets it; nobody else calls
  it. Its docstring line says so.
- `-h` and `--help` print the docstring, which holds the Usage block, the
  rules of D2 and the exit codes of D7.

The script lives in `plugins/kit/bin/` as a real file, with its tests in
`plugins/kit/tests/`. `plugins/my/bin` is on `PATH` only while `my` is on,
and `kit` is on in every project.

### D2. The rules `plan` applies

**Range.** With `<base>`, the range is `<base>..HEAD`. Without it, the base
is `main`, else `master`. With neither, the base is `HEAD~20`. When that base
does not exist, `plan` refuses (exit 1) and says to pass a base.

**Classes.** `plan` reads each commit's subject and body. A commit is
*squashable* when its subject matches, ignoring case:

- `fix`, `chore`, `style` or `docs`, with an optional `(scope)`, then `:`.
- One of a fixed list of unprefixed subjects, compared after trimming
  spaces and a final `.`: `cleanup`, `clean up`, `formatting`, `format`,
  `whitespace`, `lint`, `typo`, `fix typo`, `fix typos`, `update gitignore`,
  `update .gitignore`.

Every other commit is a *boundary*. This includes `feat`, `feature`,
`refactor`, `test`, `perf`, `build`, `ci` and `revert`; a type with `!`
before the `:`; a body that holds `BREAKING CHANGE`; `fixup!` and `squash!`
subjects; merge commits; any other unprefixed subject; and every commit named
with `--keep`.

**Groups.** Walk the commits from oldest to newest. A run of two or more
consecutive squashable commits is a group. A single squashable commit between
boundaries is no group.

**Checks.** `plan` reports, and does not judge:

- whether the working tree is dirty (`git status --porcelain` prints
  anything);
- the current branch, and whether it is `main` or `master`;
- each group that holds a pushed commit. A commit is pushed when a
  remote-tracking ref (`refs/remotes/*`) reaches it, that is, when
  `git rev-list <range> --not --remotes` does not list it;
- each group whose commits have more than one author (`%an`);
- the merge commits in the range.

### D3. What `plan` prints

Plain text, one fact per line, fields separated by one tab, in this order:

```text
range   <base ref>..HEAD   <base sha>   <head sha>
branch  <name>   main|other
dirty   yes|no
merges  none | <short hash> ...
group   <n>   <count>   pushed|unpushed   <author>[, <author>...]
commit  <short hash>   <n>|-   squashable|boundary   <subject>
```

The `commit` lines list every commit of the range, oldest first. The second
field is the group number, or `-` for a commit in no group. The skill turns
these lines into the step 4 view for the user.

### D4. The plan file and the messages file

**The plan file** is JSON that `plan` writes to `--out`. The model never edits
it. It holds the base sha, the head sha at plan time, the branch, and each
group with its number, its full hashes oldest first, its authors and its
pushed flag.

**The messages file** is plain text that the model writes with the Write tool
after the user approves:

```text
--- group 1
fix: improve YOLO export queries and mysql.sh diagnostics

--- group 2
fix: it's the tar paths and `SECRETS_DIR` defaults
```

- A line that is exactly `--- group <n>` starts a group's message. The message
  is every line up to the next such line, with blank lines at its start and
  end removed. A message may have a body.
- **A group with no block is not squashed.** This is how the user's
  "exclude group 2" and "include the mixed-author group" reach the script:
  the model writes a block only for each group the user approved.
- `apply` refuses (exit 1, nothing changed) when: text other than blank lines
  comes before the first marker; a block names a group the plan file does not
  have; a group has two blocks; a message is empty; or no block remains.

Both files must lie outside the repository's work tree, as in
`locked-commit.py`. A file inside it would make the tree dirty. The skill
writes them to the session's scratchpad, with the time in the name.

### D5. What `apply` does

Checks first. Each failure exits 1 and changes nothing:

1. The working tree is clean.
2. `HEAD` is the head sha in the plan file. Otherwise history moved since the
   plan, and the skill runs `plan` again.
3. The range holds no merge commit (D6).
4. No group with a message holds a pushed commit, unless `--allow-pushed`.
5. The branch is not `main` or `master`, unless `--allow-main`.
6. The messages file passes D4's checks.

Then:

1. Create the backup branch `backup/squash-<YYYYmmdd-HHMMSS>` at `HEAD`, and
   print its name. This moves out of step 1 (`SKILL.md:30`–`35`), so a
   `--dry-run` or a cancel leaves no branch behind.
2. Write each message to its own file in a new temporary folder outside the
   repository.
3. Run `git rebase -i --no-autosquash <base sha>`, with
   `GIT_SEQUENCE_EDITOR` set to this script's `todo` subcommand and
   `GIT_EDITOR` set to `false`, so no editor can start.
4. `todo` rewrites the todo file. For each group with a message, it turns
   every commit after the first from `pick` into `fixup`, and adds after the
   group's last commit
   `exec git commit --amend -F <that group's message file>`. It accepts both
   long (`pick`) and short (`p`) command words, because
   `rebase.abbreviateCommands` changes them, and it matches hashes by prefix.
5. When the rebase fails at any point, for example when a `commit-msg` hook
   rejects a message: run `git rebase --abort`, print git's error unchanged,
   and exit 3. History is as before, and the backup branch stays.
6. Run `git diff --quiet <head sha> HEAD`. When it reports a difference, print
   the backup branch and the command `git reset --hard <backup branch>`, do
   not run it, and exit 4.
7. Print `git log --oneline <base sha>..HEAD`, delete the plan file, the
   messages file and the temporary folder, and exit 0.

The tip-only path of today's step 5 (`git reset --soft HEAD~<N>`,
`SKILL.md:129`–`134`) goes. The rebase handles a group at the tip as well,
and one path is one thing to test.

### D6. Ranges with merge commits

`plan` still prints the groups of such a range, so `--dry-run` shows them.
`apply` refuses with exit 1 and names the merge commits. The skill tells the
user that a squash here would flatten the merges, and stops. Today the skill
would flatten them without saying so (Context).

### D7. Exit codes

- **0.** `plan`: printed the plan and wrote the plan file. `apply`:
  squashed; the log is printed.
- **1.** `plan`: refused, because there is no base or `--out` is inside the
  work tree. `apply`: refused by a check of D5; nothing changed, and no
  backup branch exists.
- **2.** Usage error, for every subcommand.
- **3.** `apply` only: the rebase failed and was aborted. History is as
  before; the backup branch exists.
- **4.** `apply` only: the tree differs after the squash. History changed;
  the backup branch is printed.

Every message on stderr starts with `git-squash:`.

### D8. The new skill text

The skill keeps its frontmatter, the Arguments section, step 4's message rules
without the single-quote rule, and the user question. The steps become:

1. **Plan.** Run `git-squash.py plan [<base>] --out <scratchpad>/squash-plan-<time>.json`,
   with `--keep` for each commit the user named. On exit 1, report the line
   and stop.
2. **Read the checks.** Dirty tree: stop and tell the user to commit or
   stash; do not stash for them. A pushed group, or the branch `main` or
   `master`: explain the force-push or the risk, and go on only when the user
   says so in this conversation. Merge commits: say a squash would flatten
   them, and stop after the plan.
3. **Show the plan** (today's step 4 view), with a proposed message for each
   group. A mixed-author group is shown, but left out unless the user
   includes it. With `--dry-run`, stop here.
4. **Ask** with `AskUserQuestion`, as today (`SKILL.md:123`).
5. **Apply.** Write the messages file with the Write tool: one block per
   approved group. Run `git-squash.py apply <plan file> <messages file>`,
   adding `--allow-pushed` or `--allow-main` only when the user said yes to
   that in step 2.
6. **Report.** Exit 0: give the user the backup branch name; do not delete
   it. Exit 3: report git's error as printed, and do not resolve conflicts.
   Exit 4: tell the user at once, name the backup branch and the reset
   command, and do not run it.

The skill names the script's `--help` as the full list of classes, so the
rules exist once.

## Choices made without the user

Each line is a question brainstorming would have asked, the answer this
draft picked, and why.

1. **One script or two?** One, `git-squash.py`, with `plan`, `apply` and
   `todo`, as `handoff-state.py` does: the rules and the file formats stay in
   one file.
2. **A real file or a symlink to `~/src/scripts/`, like the md-tables
   filters?** A real file in `plugins/kit/bin/`, with tests in
   `plugins/kit/tests/`. The kit test command then covers it, and every
   install of the plugin has it.
3. **How does the model hand over the messages?** A plain-text messages file
   with `--- group <n>` markers, next to a plan file only the script writes.
   One JSON file that the model edits was the other option (Trade-offs).
4. **How does the user's "exclude a group" reach the script?** By leaving that
   group out of the messages file. No separate flag.
5. **When is the backup branch made?** In `apply`, not at the start. A dry run
   or a cancel then leaves nothing behind. Today it is made before the checks.
6. **What counts as pushed?** Reachable from any remote-tracking ref. Today's
   `origin/<branch>` test calls every commit pushed when that ref does not
   exist. The new rule misses a push to a remote that was never fetched.
7. **How does the user's yes for a force-push or for `main` reach `apply`?**
   As the flags `--allow-pushed` and `--allow-main`. The script then refuses
   by default, and the model must pass a flag on purpose.
8. **What about unprefixed subjects the list does not name?** Boundary. The
   fixed list in D2 replaces "etc.", so the result does not depend on the
   model.
9. **What about `perf:`, `build:`, `ci:` and `revert:`?** Boundary. They change
   behaviour or the build, so they should not disappear into a `fix:`.
10. **What about `fix!:` and `BREAKING CHANGE` in a body?** Boundary. Today only
    the subject is read.
11. **What about merge commits?** `apply` refuses the range (D6). This is a
    change of behaviour: today the skill flattens them.
12. **Keep the `reset --soft` path for a group at the tip?** No. One rebase path
    for all groups.
13. **Delete the two files after success?** Yes, as `locked-commit.py` does,
    because the Write tool refuses to overwrite a file it has not read. They
    are kept on failure.
14. **Name and exit codes.** `git-squash.py`; exit codes as in D7.

## Trade-offs

The main choice is how the model's messages reach `apply`.

- **Option A: a plan file from the script, and a messages file from the
  model (chosen).** Pros: the model writes plain text, with no escaping; the
  model never edits a file the script relies on; leaving a group out is the
  natural way to exclude it. Cons: two files per run; a message cannot hold
  a line that is exactly `--- group <n>`.
- **Option B: one JSON plan file; the model fills in a `message` field per
  group.** Pros: one file. Cons: the model must escape `"`, `\` and line
  breaks in JSON; one bad edit corrupts the hashes the rebase uses.
- **Option C: script only `apply`; keep steps 1 to 3 as prose.** Pros: smaller
  change. Cons: the grouping rules stay as prose the model can get wrong, and
  the report's finding is half done.
- **Recommendation:** Option A. Escaping is the class of fault this row
  removes, so the format the model writes should need none.

## Dependencies

- **Row 41 "`git-squasher` loses `$1`" ships first.** It fixes the `"$1"` in
  step 5's example (`SKILL.md:147`). This spec builds on that fix, then
  removes step 5's shell code from the skill text. After this change the
  skill holds no shell script, so the `$1` bug class cannot come back here.
- No new packages: Python 3 standard library (`argparse`, `json`, `os`,
  `re`, `shlex`, `subprocess`, `tempfile`) and git 2.43.0.

## Risk

1. **`apply` rewrites history.** A bug could lose commits. Guards: the
   backup branch before any change, the head check (D5 check 2), the tree
   check after (D5 step 6), and tests that run the real script on throwaway
   repositories. Rollback for the user: `git reset --hard <backup branch>`.
2. **User git config changes the rebase.** `rebase.autoSquash` would reorder
   `fixup!` commits, and `rebase.abbreviateCommands` shortens the todo words.
   `apply` passes `--no-autosquash`, and `todo` reads both word forms. A test
   sets `rebase.abbreviateCommands=true`. Other config, such as
   `rebase.instructionFormat`, is not tested.
3. **Hooks run on each amend.** `exec git commit --amend` runs `pre-commit`
   and `commit-msg` hooks. A hook that rejects a message aborts the whole
   squash (exit 3). That is safe, but the user may have to fix the message
   and run again.
4. **`README.md` is shared.** Row 45 "Review preparation as a script" adds a
   `bin/` sentence to it, and row 9 "Start auto runs from roadmap rows" edits
   lines 157 to 165. This change edits the `kit:git-squasher` line (138) and
   adds one sentence near the `kit` bin paragraph (143 to 148). If two of
   these branches merge close together, the second squash-merge may need a
   text merge in `README.md`.
5. **The neutrality test scans the script.** `test_kit_cites_no_method` fails
   if the script or its docstring names `docs/plans`, `superpowers:` or a
   `my` skill such as `spec-review`. The script has no reason to.
6. **Line numbers drift.** The numbers here are from `e0bf1b1`. Row 41 lands
   first and edits step 5. The code stage finds each site by its text.
7. **Exit 4 has no test.** Squashing consecutive commits in their own order
   cannot change the tree, so no real history reaches that path. It guards
   against a bug in `todo`. A test would need a fake `git`, which the other
   tests in this repo do not use.
8. **A message line equal to a marker.** A message cannot contain a line that
   is exactly `--- group <n>`. No commit message in practice holds one.

## Testing

`plugins/kit/tests/test_git_squash.py`, run with the kit suite:
`cd plugins/kit && python3 -m unittest discover tests`. Each test builds a
throwaway repository and runs the real script, with git config cut off and
`GIT_EDITOR=false`, as `test_locked_commit.py` does. So any test where an
editor would start fails. Task 7 rehearses the skill headless.

## Files

- Create: `plugins/kit/bin/git-squash.py` (executable),
  `plugins/kit/tests/test_git_squash.py`.
- Modify: `plugins/kit/skills/git-squasher/SKILL.md`, `README.md`.

## Tasks

Run in a worktree of `claude-setup`. Commit type `feat`, scope `kit-plugin`.

### Task 1: tests (Red)

File: `plugins/kit/tests/test_git_squash.py`.

Helpers, no bodies here: `clean_env(extra={}) -> dict` and
`git(repo, *args, check=True) -> str` (as in `test_locked_commit.py`, plus
`GIT_EDITOR=false`); `make_repo(tmp, branch="feature") -> Path` (root commit
on `main`, then a checkout of `branch`); `commit(repo, subject, body="",
author="Ann <ann@example.com>") -> str` (changes a file, returns the full
hash); `plan(repo, *args) -> CompletedProcess`;
`plan_json(repo, *args) -> tuple[CompletedProcess, dict]`;
`messages(tmp, text) -> Path`; `apply(repo, *args) -> CompletedProcess`;
`groups(out) -> dict[int, list[str]]` (reads the `commit` lines of D3).

The history the grouping tests use is the example at `SKILL.md:87`–`94`:
`feat`, `fix`, `chore`, `fix`, `fix`, `fix`, `fix`, `refactor`, with the
fifth `fix` alone between boundaries made by `--keep`.

```python
def test_plan_groups_consecutive_squashable_runs(self):
    assert groups(r.stdout) == {1: [c2, c3, c4], 2: [c5, c6]}

def test_plan_skips_single_squashable_commit(self):
    assert commit_line(r.stdout, c7)[1] == "-"

def test_plan_boundary_classes_split_runs(self):
    # fix, <boundary>, fix for each boundary below; no group may form
    for subject in ["feat: a", "feature: a", "refactor: a", "test: a",
                    "perf: a", "build: a", "ci: a", 'revert: "a"',
                    "fix!: a", "fixup! fix: a", "squash! fix: a",
                    "rename things"]:
        assert groups(r.stdout) == {}

def test_plan_breaking_change_in_body_is_boundary(self):
    # fix, fix (body "BREAKING CHANGE: x"), fix
    assert groups(r.stdout) == {}

def test_plan_prefix_ignores_case_and_scope(self):
    # "FIX(api): a", "Chore: b"
    assert groups(r.stdout) == {1: [c1, c2]}

def test_plan_listed_unprefixed_subjects_are_squashable(self):
    # "cleanup", "Fix typo."
    assert groups(r.stdout) == {1: [c1, c2]}

def test_plan_keep_makes_a_boundary(self):
    r = plan(repo, "--keep", c3[:7], "--out", out)
    assert groups(r.stdout) == {}  # fix, fix(keep), fix

def test_plan_reports_mixed_authors(self):
    assert "Ann, Bob" in group_line(r.stdout, 1)

def test_plan_default_base_is_main_then_master(self):
    assert range_line(r.stdout)[1] == "main..HEAD"
    # repo with master and no main
    assert range_line(r2.stdout)[1] == "master..HEAD"

def test_plan_refuses_without_base(self):
    # no main, no master, fewer than 20 commits
    assert r.returncode == 1 and r.stderr.startswith("git-squash:")

def test_plan_reports_dirty_tree(self):
    assert fact(r.stdout, "dirty") == "yes"

def test_plan_reports_pushed_group(self):
    # bare remote; first two commits pushed to origin/other-name
    assert group_line(r.stdout, 1)[3] == "pushed"

def test_plan_without_upstream_reports_unpushed(self):
    assert group_line(r.stdout, 1)[3] == "unpushed"

def test_plan_reports_main_branch(self):
    assert fact(r.stdout, "branch") == ["main", "main"]

def test_plan_reports_merge_commits(self):
    assert fact(r.stdout, "merges") == [merge[:7]]

def test_plan_changes_nothing(self):
    assert refs_after == refs_before and status_after == status_before

def test_plan_refuses_out_file_inside_work_tree(self):
    assert r.returncode == 1

def test_apply_squashes_middle_and_tip_groups(self):
    assert subjects(repo, base) == ["feat: a", "fix: one", "refactor: b",
                                    "fix: two"]
    assert git(repo, "diff", head_before, "HEAD") == ""

def test_apply_message_is_verbatim(self):
    text = "fix: it's `x` and $(id)\n\nbody line"
    assert git(repo, "log", "-1", "--format=%B").strip() == text

def test_apply_group_without_block_is_not_squashed(self):
    assert c5 in hashes(repo, base) and c6 in hashes(repo, base)

def test_apply_makes_backup_branch_at_old_head(self):
    assert git(repo, "rev-parse", backup) == head_before
    assert backup in r.stdout

def test_apply_deletes_its_files_after_success(self):
    assert not plan_file.exists() and not msgs.exists()

def test_apply_works_with_abbreviated_commands(self):
    git(repo, "config", "rebase.abbreviateCommands", "true")
    assert r.returncode == 0 and len(hashes(repo, base)) == expected

def test_apply_refuses_dirty_tree(self):
    assert_refused(r)

def test_apply_refuses_when_head_moved(self):
    assert_refused(r)

def test_apply_refuses_range_with_merge(self):
    assert_refused(r) and merge[:7] in r.stderr

def test_apply_refuses_pushed_group_without_flag(self):
    assert_refused(apply(repo, plan_file, msgs))
    assert apply(repo, plan_file, msgs, "--allow-pushed").returncode == 0

def test_apply_refuses_main_without_flag(self):
    assert_refused(apply(repo, plan_file, msgs))
    assert apply(repo, plan_file, msgs, "--allow-main").returncode == 0

def test_apply_refuses_bad_messages_file(self):
    for text in ["junk\n--- group 1\nfix: a\n", "--- group 9\nfix: a\n",
                 "--- group 1\nfix: a\n--- group 1\nfix: b\n",
                 "--- group 1\n\n", ""]:
        assert_refused(apply(repo, plan_file, messages(tmp, text)))

def test_apply_rejected_message_aborts_and_restores(self):
    # commit-msg hook that exits 1
    assert r.returncode == 3
    assert git(repo, "rev-parse", "HEAD") == head_before
    assert not (repo / ".git" / "rebase-merge").exists()
    assert plan_file.exists() and msgs.exists()
```

`assert_refused(r)` checks `r.returncode == 1`, that stderr starts with
`git-squash:`, that `HEAD` did not move, and that no `backup/squash-*` branch
exists. Each test must fail first, because the script does not exist.

### Task 2: `plan` (Green)

File: `plugins/kit/bin/git-squash.py`, executable.

Functions: `fail(code, message) -> int`;
`resolve_base(repo_args) -> tuple[str, str] | None` (ref name, sha);
`list_commits(base, head) -> list[Commit]` (hash, author, subject, body,
parent count); `classify(commit, keep) -> str` (`"squashable"` or
`"boundary"`); `build_groups(commits, classes) -> list[list[Commit]]`;
`pushed_hashes(base, head) -> set[str]`; `checks() -> dict`;
`print_plan(...) -> None` (D3); `write_plan(path, ...) -> None` (D4);
`inside_work_tree(path) -> bool`; `cmd_plan(args) -> int`;
`main(argv) -> int`. `Commit` is a `namedtuple`.

All `test_plan_*` tests pass.

### Task 3: `apply` and `todo` (Green)

Same file. Functions: `read_plan(path) -> dict`;
`read_messages(path, plan) -> dict[int, str] | str` (messages, or the reason
to refuse); `apply_checks(plan, messages, args) -> str | None`;
`make_backup() -> str`; `rewrite_todo(lines, plan, message_files) -> list[str]`;
`cmd_todo(args) -> int`; `cmd_apply(args) -> int`.
The sequence editor is `shlex.join([sys.executable, __file__, "todo", <plan
file>, <messages file>])`; git appends the todo path.

All tests pass.

### Task 4: refactor

The docstring holds the Usage block, the rules of D2 (the full list of
classes), the file formats of D4 and the exit codes of D7, in the style of
`locked-commit.py`. Remove any duplicate git calls between `plan` and
`apply`. The whole kit suite passes, `test_neutral_core.py` included.

### Task 5: the skill

File: `plugins/kit/skills/git-squasher/SKILL.md`, as D8 says. Delete the
prose the script replaces:

- step 1's range rules, backup commands and check commands
  (`SKILL.md:25`–`43`); the stop rules (`:45`–`49`) move to the new step 2;
- step 2's command and both lists (`:51`–`70`), replaced by one sentence that
  names the classes and points to `git-squash.py --help`;
- step 3's rules and example (`:72`–`95`);
- the single-quote rule (`:119`);
- step 5 whole (`:125`–`159`), including `squash-todo.sh`;
- step 6's commands (`:161`–`170`); the reporting rules stay as the new
  step 6;
- the Edge Cases lines that point to removed steps (`:184`–`188`) are updated:
  merge commits now stop the squash.

Then:

- `git grep -n -e 'squash-todo' -e 'ORIG=' -e '"\$1"' -- plugins/kit` prints
  nothing.
- `markdownlint-cli2 plugins/kit/skills/git-squasher/SKILL.md` adds no error
  beyond those on `main`.

### Task 6: `README.md`

Line 138: the `kit:git-squasher` line says the plan and the squash run
through `plugins/kit/bin/git-squash.py`. One sentence after the md-tables
paragraph (lines 143 to 148) names the script and its tests:
`cd plugins/kit && python3 -m unittest discover tests`.

### Task 7: rehearsal

No repo change. In a scratch repository with the example history of Task 1,
run the skill headless with the plugin dir added:
`claude -p "/kit:git-squasher main" --add-dir <scratch dir> --add-dir
<plugin dir>`, approving with a message that holds `'` and a backtick. Pass:
the session ran `git-squash.py plan` and `apply`, the log shows the two
squashed groups with the messages as asked, `git diff <backup branch> HEAD`
prints nothing, and no editor started. Then run it with `--dry-run`: no
backup branch exists afterwards. Record the result in the squash commit
message.

## Open questions

1. May this spec run in auto mode (`/my:handoff auto`)? If yes, a Delegation
   section is added before approval.
2. Should `apply` refuse ranges with merge commits (D6), or should a later
   row add `--rebase-merges`? This draft refuses.
3. Is the fixed list of unprefixed subjects in D2 the right one? Any subject
   not on it becomes a boundary.
