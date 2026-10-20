---
name: handoff
description: >
  Hand the next stage of the spec, plan, code and review cycle to a new
  top-level session in a tmux window, or run a stage that was handed off. Use
  after the user approves a spec ("hand off the plan", or "hand off the
  code" for a spec with its own Tasks section), when a plan or code stage
  finishes, or when a session starts with "/my:handoff run <stage> <doc>".
  Stages: plan (writes and reviews the plan from an approved spec), code
  (implements a committed plan, or a spec with a Tasks section, in a
  worktree) and review (runs the end-of-branch checks and reviews, one fix
  round, then the squash-merge after the user's yes). "/my:handoff auto plan
  <spec>" or "auto code <spec>" runs the whole cycle to the done marks
  without the user, as far as the spec's Delegation section allows, and
  "auto resume <spec>" continues a stopped auto run. "/my:handoff auto rows
  <row number> ..." queues roadmap rows whose specs are approved and starts
  them as auto runs, up to Max runs at once; each finishing run starts the
  next. NOT for dispatching subagents inside one session.
---

# Handoff

Move one stage of the spec → plan → code → review cycle into its own
top-level session. A top-level session reads the global and project
`CLAUDE.md` files and the project memory, which a subagent never sees. Spec:
`docs/plans/2026-09-21-handoff-spec.md` in the claude-setup repo.

## Forms

The args are one of:

- `<stage> <doc>` — **launch**: open the stage in a new tmux window. Go to
  "Launch".
- `run <stage> <doc>` — **run**: this session is the stage. Go to "Run".
- `auto <plan|code> <spec>` — **auto launch**: check the spec, create the
  run's state, and open the stage in auto mode. Go to "Start checks in auto
  mode", then "Launch". `auto plan` is for a spec without a Tasks section
  (architectural with plan); `auto code` is for a spec with one
  (architectural).
- `auto resume <spec>` — **resume**: continue a stopped auto run whose window
  is gone. Go to "Resume".
- `run auto <stage> <doc>` — **auto run**: this session is the stage, in auto
  mode. Launch types this form into the new window. Go to "Run".
- `auto rows [<row number> ...]` — **rows**: queue roadmap rows whose specs
  are approved, and start them as auto runs. With no numbers, start the
  first waiting rows. Go to "From roadmap rows".
- `auto rows drop <row number> ...` — **drop**: cancel waiting rows. Go to
  "From roadmap rows".

Without the word `auto`, every step reads as written, even when the spec has
a Delegation section. The rules marked **In auto mode** apply only to the
three auto forms. The `auto rows` forms run no stage themselves; the runs
they launch are auto runs. In them, a run goes from an approved spec to the
`done` marks on `<base>` without the user, never pushes, and stops only where
the table in "Stop points in auto mode" says.

`<stage>` is `plan`, `code` or `review`. `<doc>` is one path under
`docs/plans/`. Each stage reads `<doc>` by the role it plays, not by its
file name:

- `plan` stage: `<doc>` is the **design doc**, an approved spec.
- `code` and `review` stages: `<doc>` is the **task doc**, the committed
  document that lists the tasks this branch carries out. It is either a
  plan, or a spec with a **Tasks** section. In a batch, `review` gets the
  batch's last task doc.

A file whose name ends in `-spec.md` is a spec; any other file is a plan.
A spec used as the task doc is its own design doc. A plan's design doc is
the spec that its header names. In the code and review
stages, "the plan" in the steps below means the task doc, and "the spec"
means its design doc.

When the task doc lacks something a step reads from it, such as the commit
type or the execution skill, use the fallback the step names. Where a step
names no fallback, signal and ask. Never guess silently.

Any other args: stop and print
`Usage: /my:handoff [run] [auto] <plan|code|review> <docs/plans/…md>, /my:handoff auto resume <docs/plans/…-spec.md>, or /my:handoff auto rows [drop] [<row number> ...]`.
The auto launch takes only `plan` or `code` and a spec, or `rows` and row
numbers.

`<slug>` is the doc's filename without the `YYYY-MM-DD-` prefix and without
`-spec.md` or `.md`. Example: `docs/plans/2026-09-21-landing-match-grade-spec.md`
→ `landing-match-grade`. `<name>` is `<stage>-<slug>`.
For `auto resume`, `<name>` is `resume-<slug>`. For the `auto rows` forms, it
is `rows`.

`<window>` is the tmux window name: `r<row>: <name>`, for example
`r122: code-landing-match-grade`, or `<name>` alone when no row is found.
`<row>` is the number of the roadmap row that links the doc, as written in
`ROADMAP.md` (`\d+[a-z]?`). To find it, run
`grep -nE '[0-9]{4}-[0-9]{2}-[0-9]{2}-<slug>(-spec|-architecture)?\.md' <repo root>/ROADMAP.md`,
with `<repo root>` as in Launch step 3. The date anchor keeps a longer slug
that ends in the same words from matching. A row is a bullet
`- <icon> <row> **<title>**` or a table line `| <row> | **<title>** |`, and a
bullet goes on over its indented lines up to a blank line or a line that is
not indented. A hit belongs to the row it sits in; a hit outside every row,
such as in a section intro, counts for none. Count ✅ rows too: the review
stage renames its window after the `done` marks. Of those rows, keep only the
ones whose title names the same change as the spec's title or Goal, as
`my:status` step 4 does: a row that links the doc as the place where
something was found is not its row. When exactly one row is left and it has
a number, that number is `<row>`. Otherwise there is no row. The `auto rows`
forms have no slug, so their own `<window>` is `rows`. A Launch builds
`<window>` for the session it opens, from that session's `<name>` and a
lookup of its slug. A Run session does not look up its row again: at the
start of the stage, before the start checks, it reads its window's name with
`tmux display-message -p -t "$TMUX_PANE" '#W'`. When that name is `<name>`
or `r<row>: <name>`, that name is `<window>`. Otherwise (no `$TMUX_PANE`, or
a window the user opened after a fallback), it looks up the row as above. It
keeps `<window>` to the end, so the window name does not change in the
middle of a stage.

`<base>` is the branch that specs and plans are committed on and that work
branches squash-merge into. Take it from the project's rules when they name
one for this work. Otherwise it is the branch checked out in the main
checkout: `git -C <repo root> branch --show-current`, with `<repo root>` as in
Launch step 3. It is often `main`, but can be `master`, `develop` or another
name. If that command prints nothing (a detached HEAD), signal
`<name>: start check failed: no base branch` and stop.

### Delegation

An auto run needs a section titled `Delegation` in the spec, at any heading
level, with exactly these four keys:

```markdown
## Delegation

- **Dependencies:** `none`
- **Design-changing findings:** `stop`
- **Failing end-of-branch tests:** `none`
- **End-of-branch checks:** `python3 -m unittest discover tests`
```

| Key | Allowed values | Meaning |
| --- | --- | --- |
| Dependencies | `none`, or a list of package names with an optional version | The code stage may add exactly these. Any other new dependency stops the run. |
| Design-changing findings | `stop` or `decide` | `decide`: the stage picks the fix it judges best and records it (see "Stop points in auto mode"). `stop`: as without auto. |
| Failing end-of-branch tests | `none`, or a list of test names | These tests may fail without stopping the run. Any other failure stops it. |
| End-of-branch checks | `none`, or a list of commands | The checks to run when the project's rules name none. When the rules name checks, the rules win. `none` makes the `done` mark say `no end-of-branch checks run`. |

Compare by exact name: a package or a test is listed only when its name is
written there. A missing key, an unknown key, or a value outside these forms
fails the start check. Anything the section does not list stops the run.

## Parallel runs

A project allows several auto runs at once when its `CLAUDE.md` or
`CLAUDE.local.md` holds a heading titled `Parallel runs`, at any level. Such
a project "has the section". Spec:
`docs/plans/2026-10-12-parallel-auto-runs-spec.md` in the claude-setup repo.

```markdown
## Parallel runs

- **Max runs:** 2
- **Docs paths:** `docs/`, `ROADMAP.md`, `CHANGELOG.md`
- **Isolation:** `COMPOSE_PROJECT_NAME=app_<slug>`; `PORT=$((54310 + <slot>))`
- **Shared resources:** `e2e`: `web/scripts/e2e-worktree.sh <path>`
```

| Key | Default when missing | Meaning |
| --- | --- | --- |
| Max runs | `2` | The most auto runs live at once. |
| Docs paths | `docs/`, `ROADMAP.md`, `CHANGELOG.md` | Changes only under these paths are not code. A path ending in `/` is a folder. Everything else is code, including Markdown skills. |
| Isolation | `none needed` | What every stage sets for each command it runs in the worktree, so that worktrees do not share test stacks or ports. It may use `<slug>` and `<slot>`. |
| Shared resources | `none` | Commands that only one run may use at a time, each with a lock name. Each runs under its lock. |

Without the section, only two parts of this apply: the locked start, with
`--max 1`, so that a second auto run refuses to start; and the fold's
refusal to give a cited commit a new hash. Every other step reads as
written.

The values that the steps below use:

- **`<n>`**, the number the auto launch passes to `--max`: the **Max runs**
  value when the section names one; `2` when the section has no **Max
  runs** key; `1` when the project has no section.
- **The docs paths:** the section's list, or the default list. Pass them to
  `git-fold-fixups.py` and to `handoff-state.py merge` as
  `--docs-paths <path> ...`, last on the command line, only when the section
  names a list that differs from the default.
- **`<slot>`:** the `slot` field that `handoff-state.py get <slug>` prints.
  A supervised run has no state file and uses slot `1`.

`handoff-lock.py`, on `PATH` like `handoff-state.py`, runs one command under
a named lock that the main checkout and every worktree share:

```text
handoff-lock.py <name> [--timeout <seconds>] -- <command> [<arg> ...]
```

It holds the lock exactly as long as the command runs, and the kernel frees
it when the command ends or dies. The default timeout is 90 s, below the
Bash tool's 120 s. The exit code is the command's own, except for the
script's own codes below. Each of those prints one stderr line that starts
with `handoff-lock:`.

| Code | Meaning |
| --- | --- |
| 64 | Usage error, or a bad lock name. Nothing ran. |
| 74 | The lock file cannot be opened. Nothing ran. |
| 75 | The wait timed out. Nothing ran. |
| 126 | The command cannot be run. |
| 127 | The command is not found. |

A command can exit with one of these codes on its own. So read a code as the
script's only when the stderr line that starts with `handoff-lock:` is there.

A locked command must not start a process that outlives it, such as a
server: that process keeps the lock until it ends.

## Signal

"Signal" means these three actions, in this order, then stop and wait:

1. If `$TMUX_PANE` is set, run
   `tmux rename-window -t "$TMUX_PANE" "<window> ⚠"`. Always pass `-t`: without
   it tmux renames the window the user is looking at.
2. Call `PushNotification` with one line under 200 characters that leads with
   `<name>:` and says what the user must do. It may be a deferred tool: if
   its schema is not loaded yet, load it once with
   `ToolSearch("select:PushNotification")`. If `PushNotification` cannot be
   called even then, skip this action. It is often not sent while the user
   is active elsewhere; that is expected. Do not retry.
3. Print the same line as the last line of your output.

In a Run session only: after a signal, when the user next replies in this
window and `$TMUX_PANE` is set, first run
`tmux rename-window -t "$TMUX_PANE" "<window>"`, then act on the reply. So the
mark means "waiting for the user" and nothing else. A Launch never renames a
window. A finished stage uses another mark, `✓`; see "Finish".

Signal at exactly five points: a gate, an error you cannot fix, "ready to
squash-merge", the code stage's "done" when the work ends before the branch
does, and a failed refill (see "Refill", under "From roadmap rows"). Any
question you would ask the user is a gate: signal first,
then ask.

**In auto mode,** the table in "Stop points in auto mode" replaces that list:
it says, for each of those points, whether the stage stops or goes on. A
stop is a signal with one step before it: run
`handoff-state.py set <slug> stopped="<the line>"`, with the `next` value
the row names, if any. A failed start check and a refused `resume` are the
exception: they write nothing. After the user's reply, run
`handoff-state.py set <slug> stopped=`, then go on in auto mode. A failed
refill is not in that table: it stops no run, so it writes no `stopped` on
the run that finished. "Refill" says what it writes.

## Stop points in auto mode

"Delegation [Key]" means: read that key of the spec's Delegation section. Go
on when the case is listed there, and stop when it is not. Compare by exact
name.

| Row | Stage | Stop point without auto | Auto mode |
| --- | --- | --- | --- |
| 1 | any | A start check fails | stop |
| 2 | any | Launch cannot open a window (no tmux, or a mode other than `auto` or `bypassPermissions`) | stop |
| 3 | any | A shared resource is busy, or another session's edit is in a file the stage commits | stop |
| 4 | plan | A finding whose fix changes a decision, or a false premise | Delegation [Design-changing findings] |
| 5 | plan | Spec fixups wait: the pre-rebase check fails, or the fold exits 1 or 3 | stop |
| 6 | code | A new dependency | Delegation [Dependencies] |
| 7 | code | A change outside the project's scope | stop |
| 8 | code | A test still fails after `superpowers:systematic-debugging` | stop |
| 9 | code | A test assertion was removed or weakened | stop |
| 10 | review | An end-of-branch test fails | Delegation [Failing end-of-branch tests] |
| 11 | review | The project's rules name no end-of-branch checks | Delegation [End-of-branch checks] |
| 12 | review | A finding whose fix changes a decision | Delegation [Design-changing findings] |
| 13 | review | A new Critical finding in the re-review | stop |
| 14 | review | Ready to squash-merge | go on |
| 15 | review | `git merge --squash` conflicts, because `<base>` moved during the run | run `git reset --merge`, check that `git status --porcelain` prints nothing, then stop with `next=merge`. If the tree is still not clean, the stop line says so. (`git merge --abort` does not work here: a squash merge writes no `MERGE_HEAD`.) |
| 16 | review | After the merge, `<base>` is not clean, so the fold must wait | stop with `next=fold` |
| 17 | review | The fold exits 1 or 3 | stop with `next=fold`. Exit 3 also records the HEAD from before the fold. |
| 18 | any | Lock `main` or a shared-resource lock times out (`handoff-lock.py` exit 75 with a stderr line that starts with `handoff-lock:`), except at the start | stop |
| 19 | any | A shared doc (`ROADMAP.md`, `CHANGELOG.md`, the plans index, `docs/DESIGN-SYSTEM.md`) holds someone else's edits | stop |
| 20 | review | The worktree rebase after `merge` exit 4 conflicts | run `git rebase --abort`, then stop with `next=merge-retry` |
| 21 | review | The base moved a fourth time | stop with `next=merge-retry` |
| 22 | review | `handoff-state.py merge` exits 5: the squash conflicts, or its commit fails | stop with `next=merge`, as row 15 |
| 23 | any | Any other failure of `handoff-lock.py`, `locked-commit.py` or `handoff-state.py merge` | stop, with the script's message in the stop line |

Rows 18 to 23 arise only in a project with a "Parallel runs" section. Rows 5,
16 and 17 cannot arise there, because nothing folds. A refused start is not a
stop: it writes nothing (see "Start checks in auto mode").

With `decide` in Delegation [Design-changing findings], the stage picks the
fix it judges best, applies it, and writes one line into the task doc's
**Risk** section: the finding, the choice and the reason. The task doc is
the plan, or the spec when there is no plan. While the worktree exists, that
edit is made and committed in the worktree. With a failing test listed in
Delegation [Failing end-of-branch tests], the run goes on, and the `done`
mark names the test.

## Launch

Run these steps in order.

1. **Name.** Build `<name>` and `<window>` from the args.
2. **Duplicate.** Call `ListAgents`. If a session named `<name>` is listed,
   print `<name> already exists; not launching a second one.` and stop.
3. **Flags.**
   - Plugin dirs: run `ps -o args= -p "$CLAUDE_PID"` and copy every
     `--plugin-dir <path>` pair from it. A tmux window runs no shell alias, so
     without them the new session lacks this skill.
   - Mode: read your own permission mode from your context. Only `auto` and
     `bypassPermissions` may open a window. For those, the flag is
     `--permission-mode <mode>`. In any other mode, or when your context does
     not state the mode, the flag is empty and you go to step 4's fallback.
   - Repo root: `dirname "$(git rev-parse --path-format=absolute --git-common-dir)"`.
     This is the main checkout's root, also from inside a worktree.
   - If `<doc>` contains a quote character (`'` or `"`), stop and print
     `The doc path contains a quote; rename it first.`
4. **Fallback.** If `$TMUX` is empty, or the mode is not `auto` or
   `bypassPermissions`, do not open a window. Print this command for the user
   to run in a new terminal, then stop (in a Run session, go on to "Finish"):

   ```bash
   cd <repo root> && claude -n <name> <plugin-dir flags> <mode flag> '/my:handoff run <stage> <doc>'
   ```

   When the mode flag is empty, add: `Pick a permission mode in the new
   session; in manual or acceptEdits mode it will wait at its first command.`

   **In auto mode,** the command sets `MY_AUTORUN` and types the auto run
   form. `MY_AUTORUN` turns on the plugin's push guard, a hook that blocks
   `git push` in that session:

   ```bash
   cd <repo root> && MY_AUTORUN=<slug> claude -n <name> <plugin-dir flags> <mode flag> '/my:handoff run auto <stage> <doc>'
   ```

   When the auto launch or `resume` falls back, print the command as above:
   the user is at this window. When a `run auto` stage falls back while it
   launches the next stage, that is a stop (row 2 of "Stop points in auto
   mode"): signal `<name>: cannot open a window for <next name>: <reason>`.
   The state file already names the next stage, so `resume` can launch it.
   A launch inside the refill is the exception: it follows "Refill", not
   this rule, because the run that launches it has finished, and a stop
   would write `stopped` on that finished run.
5. **Open.**

   ```bash
   tmux new-window -d -n '<window>' -c <repo root> \
     "claude -n <name> <plugin-dir flags> <mode flag> '/my:handoff run <stage> <doc>'"
   ```

   `-d` keeps the user's view where it is.

   **In auto mode:**

   ```bash
   tmux new-window -d -n '<window>' -c <repo root> \
     "MY_AUTORUN=<slug> claude -n <name> <plugin-dir flags> <mode flag> '/my:handoff run auto <stage> <doc>'"
   ```

6. **Report.** Print `Launched <name> in a new tmux window.` and stop (in a
   Run session, go on to "Finish"). Do not wait for the new session and do not
   poll for it.

## Resume

`auto resume <spec>` continues an auto run whose window is gone: after a
crash, a reboot or a closed window. `<name>` is `resume-<slug>`. It runs in
the user's own session, which has no `MY_AUTORUN`, so it never does the
stage's work itself: it launches the stage in a new window.

1. Run `handoff-state.py check <slug>`. It compares the state file with git
   and prints one mismatch per line. If it exits 1, signal
   `<name>: resume refused: <first mismatch>` and stop. Write nothing, and
   never guess. When it prints `merge done`, the merge happened before a
   crash, and `check` has already moved `next` on to `worktree-remove`.
2. Read `next` with `handoff-state.py get <slug>`. If it is `finished`, print
   `<name>: the run for <slug> is finished; nothing to resume.` and stop.
3. Pick the stage and its doc from the state:
   - `plan`: if `task_doc`, the plan, is committed on `<base>`
     (`git log -1 --format=%h <base> -- <task_doc>` prints a hash), the plan
     stage got that far: run `handoff-state.py set <slug> next=code`, and
     take the next line. Otherwise the stage is `plan` and the doc is
     `spec`.
   - `code`: the stage is `code` and the doc is `task_doc`.
   - `review`, `merge-retry`, `merge`, `worktree-remove`, `fold` or `done`:
     the stage is `review` and the doc is `task_doc`. The steps after the merge run as
     the review stage.
4. If the state's `stopped` field is not empty, print
   `<name>: the earlier stop was: <stopped>`. Then run
   `handoff-state.py set <slug> stopped=`. In a project with a "Parallel
   runs" section, also run `handoff-state.py set <slug> merge_retries=0`.
   Then run "Launch" in auto mode for that stage and doc, with the name `<stage>-<slug>`: it opens
   `run auto <stage> <doc>` with `MY_AUTORUN=<slug>`. Then "Finish".

### To end an abandoned run

A stopped run still counts toward the cap until the user resumes it or ends
it. `handoff-state.py live` lists the runs that count. To end one, the user
says so in a session. That session runs `git worktree remove <worktree>` when
the state names a worktree that `git worktree list` shows, with `--force`
only after the user's yes to it. Then it runs
`handoff-state.py set <slug> next=finished stopped="ended by the user"`. The
branch stays. Then it runs the refill (see "Refill", under "From roadmap
rows"): the ended run freed its slot.

### Restarted stages

A `run auto` session is a restart when it finds what a fresh start expects to
be absent:

- `plan`: the plan file exists.
- `code`: the state's `branch` field is not empty. The code stage writes it
  just after it creates the worktree (Code stage, step 1). A branch
  `*/<slug>` with an empty `branch` field is not a restart: it is left over
  from an earlier, finished run, and the start check "no branch `*/<slug>`"
  stops the stage.
- `review`: every start is a restart.

A restart skips the start checks that expect a fresh start: no plan yet, no
branch yet, no worktree yet. The other start checks run. `check` verified the
state before `resume` launched the stage. When `next` is `worktree-remove`,
`fold` or `done`, the merge has happened, so the review stage's start checks
on the branch and its worktree are skipped too: the worktree may be gone.
Then:

1. **Uncommitted files.** List what the crashed session left uncommitted:
   for `plan`, `git status --porcelain` in the main checkout for the plan,
   its review and the plans index (the spec's `approved` edit is expected
   and does not count); for `code` and `review`, while the worktree exists,
   `git -C <worktree> status --porcelain`. If anything is listed, stop with
   `<name>: uncommitted files from the earlier session: <paths>`. The user
   decides whether to keep them.
2. **Where each stage goes on.**
   - `plan`: start the plan stage again at step 1.
   - `code`: continue at the first task of the task doc that no commit on
     the branch carries. The tasks done are the `Task: <N>` trailers that
     `git log --format='%(trailers:key=Task,valueonly)' <base>..<branch>`
     prints. A task commit without the trailer counts as not done.
   - `review` with `next` at `review`: if the branch has a commit that adds a
     review report,
     `git log --diff-filter=A --name-only --format= <base>..<branch> -- 'docs/plans/*review*.md'`
     prints a path, and the fix round already ran. Stop with
     `<name>: the fix round already ran; a second one would break the one-fix-round rule`.
     Otherwise start the reviews again at step 1.
   - `review` with `next` past `review`: start at the sub-step of step 8
     that `next` names. `merge-retry` is past `review`: the reviews and the
     fix round are committed, so the "fix round already ran" stop does not
     apply, and the stage starts at the merge sub-step.

## From roadmap rows

`/my:handoff auto rows <row number> ...` queues roadmap rows whose specs are
approved, and starts them as auto runs, never more than `<n>` at once. Each
run that finishes starts the next waiting row (see "Refill" below). Spec:
`docs/plans/2026-10-13-roadmap-auto-runs-spec.md` in the claude-setup repo.

These forms run in the user's session, which has no `MY_AUTORUN`, and do no
stage's work themselves: they launch each stage in a new window. `<name>` for
their signals is `rows`. `<n>` is as "Parallel runs" says: `1` in a project
without the section. A row number is `\d+[a-z]?`, as in `ROADMAP.md`, and
stays a string, as typed. The queue is
`<git common dir>/my-handoff/queue/rows.json`; only `handoff-state.py` writes
it, always under lock `main`.

1. **No numbers** (`auto rows`): run
   `handoff-lock.py main -- handoff-state.py pull --max <n>`, then go to
   step 7. This starts the first waiting rows after a stall, when `my:status`
   says one can start.
2. **`drop`** (`auto rows drop <row number> ...`): run `status-scan.py`. Map
   each number to its slug from the `waiting` rows of the `queue` block,
   which print state, row and slug side by side. Print
   `row <n> is not waiting` for a number with no `waiting` row. Run
   `handoff-lock.py main -- handoff-state.py queue drop <slug> ...` with the
   other slugs. Print the result and stop. At the next `pull`, the rows gated
   behind a dropped row are skipped.
3. **Judge each row.** Run `status-scan.py` once. Use `my:status` steps 4 to
   6 (`plugins/my/skills/status/SKILL.md`) to find each row's spec, its gates
   and its file list. Check the cases below in this order. At the first case
   that holds, the row is skipped: print `row <n>: <reason>`, with the reason
   word for word, and do not queue it.

   | Case | Reason printed |
   | --- | --- |
   | The roadmap has no row with that number. | `no row <n>` |
   | The row has no spec of its own (`my:status` step 4). | `row <n> has no spec` |
   | The spec's status is not `approved`. | `spec is <status>, not approved` |
   | The spec has no valid Delegation section (start check 3 of "Start checks in auto mode"). | `Delegation: <key> <missing, unknown or invalid>` |
   | `handoff-state.py get <slug>` prints a state whose `next` is not `finished`. | `a run for <slug> exists` |
   | The slug is already `waiting` in the `queue` block. | `already waiting` |
   | The stage could not start fresh: the anchored `ls` of the plan start check lists a plan, `git branch --list '*/<slug>'` prints a branch, or `.claude/worktrees/<slug>` exists. A run the user ended leaves its branch behind. | `<plan, branch or worktree> for <slug> exists` |
   | It is gated behind a row that is not done and is none of: a row in this call, a live auto run (a state whose `next` is not `finished`), a `waiting` queue entry. Nothing would ever start such a blocker. A row is done when it is ✅, or when its slug's state has `next=finished` and an empty `stopped`: a `done` mark does not always set ✅. | `blocked by row <m>, which nothing will start` |
   | It is gated behind a row in this call that this call skips. | `blocker row <m> was skipped` |
   | Its own text says it waits for something that is not a row ("Waits for …", `my:status` step 5). Nothing in the queue would start it. | `waits for <what the row says>` |

   For each row that can start, record:

   - **`stage`:** `code` when the spec has a section titled Tasks, `plan`
     when not, as in start check 4 of "Start checks in auto mode".
   - **`after`:** the slugs of the rows it is gated behind (`my:status`
     step 5) that are rows in this call, live auto runs or `waiting`
     entries. A done blocker is no gate.
   - **`exclusive`:** `true` when the row has no file list (`my:status`
     step 6), because its overlap is unknown; `false` otherwise.

   When two rows of the call both have file lists and share a path outside
   the docs paths, print `rows <a> and <b> share <path>`. This warns and does
   not block: the parallel merge rebases and reruns the checks. When no row
   can start, stop after printing the skipped rows.
4. **Commit the `approved` edits.** A queued spec must never hold an
   uncommitted edit: while it waits, the running row's fold would stop. The
   edited specs are the specs of the rows that can start that
   `git status --porcelain -- <spec>` lists. With none, go to step 5.

   Without a "Parallel runs" section, fold when all of these hold:

   - `handoff-state.py live` prints nothing;
   - `git status --porcelain` lists only the edited specs, whose `approved`
     edits are expected, as in the plan stage's own check;
   - `git-fold-fixups.py check <spec commit>` exits 0 for every edited spec,
     with `<spec commit>` found as in Plan stage, step 8.

   To fold, first list the waiting fixups: the `fixup` lines of the
   `checkout` block. When one targets a document outside this call, name it
   and ask the user whether the fold may give that document's commit a new
   hash. That is a gate: signal first. On the user's yes, or with no such
   fixup, make one `git commit --fixup <spec commit> -- <spec>` per edited
   spec, and check that `git show --stat --format= HEAD` lists only that
   spec. Then run `git-fold-fixups.py` in the main checkout. On its exit 1
   or 3, print its message and `fixups left unfolded: <hashes>`, write no
   queue, launch nothing, and stop: those fixups must be folded or reverted
   by hand before a row behind them can run. A fixup is made only when it is
   folded at once, because a waiting one can never be folded once the run
   ahead cites a newer commit.

   When one of the three does not hold, or on the user's no, make one normal
   docs commit of every edited spec, with the docs scope of the project's
   rules: `git add -- <specs>`, read `git diff --cached`, then
   `git commit -m "<message>" -- <specs>`, and check that
   `git show --stat --format= HEAD` lists only those specs. With a "Parallel
   runs" section, that one commit runs through `locked-commit.py`, as in Plan
   stage, step 7, and nothing folds.
5. **Write the queue.** Write the entries with the Write tool to a new JSON
   file in the session's scratchpad, in the order the user typed the rows: a
   list of objects with exactly the keys `row` (a string), `spec`, `stage`,
   `after` (a list of slugs) and `exclusive` (`true` or `false`). The script
   derives the slug and hashes the spec itself. Run
   `handoff-lock.py main -- handoff-state.py queue add --file <path>`. Print
   each of its `skipped: <slug>: <reason>` lines as a skipped row,
   `row <n>: <reason>`. On a non-zero exit, print its message and stop:
   nothing was queued.
6. **Start.** Run `handoff-lock.py main -- handoff-state.py pull --max <n>`.
   Print each of its `skipped:` lines as a skipped row. On a lock timeout
   (exit 75 with a stderr line that starts with `handoff-lock:`) or another
   failure, print `rows: rows wait in the queue; run /my:handoff auto rows`
   and stop.
7. **Launch.** `pull` prints one line per run it started:
   `<slug><TAB><stage><TAB><spec><TAB><slot>`. For each line, run "Launch" in
   auto mode with the name `<stage>-<slug>`, the stage, the spec as its doc,
   and `MY_AUTORUN=<slug>`. Launch's fallback prints the command for the
   user, who is at this window.
8. **Report.** List the rows started, the rows waiting with what the first
   one waits for (`handoff-state.py queue show`), and the rows skipped with
   their reasons. Then stop. No session stays open to watch: the runs refill
   their own slots.

### Refill

A run that finishes frees its slot, and the refill starts the next waiting
rows in it. Two places run it, right after they write `next=finished`:
Review stage, step 8, sub-step 4 in auto mode, and "To end an abandoned
run".

1. Run `handoff-lock.py main -- handoff-state.py pull --max <n>`. With no
   queue file it prints nothing, and the refill is done.
2. For each line it prints, `<new slug><TAB><stage><TAB><spec><TAB><slot>`,
   run "Launch" in auto mode with the name `<stage>-<new slug>`, the stage,
   the spec as its doc, and `MY_AUTORUN=<new slug>`. Use the new slug, never
   this session's own `MY_AUTORUN`: that one names the finished run, and the
   new session's start check 1 would refuse it. Launch reads the plugin-dir
   flags and the mode as it does for a next stage. Launch every printed
   line, also after one fails.
3. When every step worked, go on to "Finish". Otherwise signal once, at the
   end, naming every failure in one line, joined by semicolons. The signal
   replaces "Finish", so the window shows ⚠, not ✓.
   - Launch cannot open a window: first run
     `handoff-state.py set <new slug> stopped="cannot open a window: <reason>"`.
     The new run keeps its slot, as any stopped run does. The failure is
     `cannot open a window for <stage>-<new slug>; run /my:handoff auto resume <spec>`.
   - `pull` fails, a lock timeout included: the failure is
     `rows wait in the queue; run /my:handoff auto rows`.

   The signal line is `<name>: <start> <failures>`. In the review stage,
   `<start>` is `done; squash commit <hash>.`, so the finish is not lost. In
   "To end an abandoned run", `<name>` is `rows` and `<start>` is
   `<slug> ended.`

A refill failure never stops the finished run: its state stays
`next=finished`, and the refill never writes `stopped` on it. To rule 2 of
`pull`, a finished run with a stop line is a run the user ended, and the
rows behind it would be skipped.

## Run

### Start checks

Before any other work, check the doc. If a check fails, signal
`<name>: start check failed: <reason>` and stop. Write nothing.

- The doc exists and has a `**Status:**` line.
- `plan` stage:
  - the spec's status is `approved` (the edit may be uncommitted: the spec
    session leaves it for this stage to commit);
  - no plan exists yet: this lists nothing, with the date prefix anchored so a
    longer slug that ends in the same words does not match:
    `ls docs/plans/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-<slug>.md`.
- `code` stage:
  - the plan is committed on `<base>`:
    `git log -1 --format=%h <base> -- <doc>` prints a hash, and
    `git status --porcelain -- <doc>` prints nothing;
  - when the task doc is a spec: its status is `approved`, it has a section
    titled Tasks (at any heading level, numbered or not), and no plan exists
    for its slug (the `ls` check of the `plan` stage lists nothing);
  - no branch `*/<slug>` exists: `git branch --list '*/<slug>'` prints
    nothing;
  - no directory `.claude/worktrees/<slug>` exists.
  - When the project's rules or the plan name the worktree and branch for
    this work, for example one worktree shared by a batch of plans, the two
    checks above do not apply. Check instead that the named worktree either
    does not exist, or exists on the named branch and
    `git -C <worktree> status --porcelain` prints nothing. An existing
    worktree is expected there: an earlier plan of the batch opened it.
- `review` stage:
  - the plan is committed on `<base>`, checked as for the `code` stage;
  - the branch and its worktree exist: `git branch --list '*/<slug>'` prints
    exactly one branch, and `git worktree list` shows it checked out in
    `.claude/worktrees/<slug>`. When the project's rules or the plan name the
    worktree and branch, check those names instead;
  - `git -C <worktree> status --porcelain` prints nothing;
  - `git log --oneline <base>..<branch>` prints at least one commit.

When something already exists, do not guess whether to resume or restart. The
user decides.

### Start checks in auto mode

The auto launch (`auto plan`, `auto code`) and every `run auto` session run
these checks, in this order. A `run auto` session then runs the list above
too, with the changes below. The auto launch runs only these. If a check
fails, signal `<name>: start check failed: <reason>` and stop. A failed check
writes nothing: it never calls `handoff-state.py set`, not even to record the
stop, because the state file may belong to another run.

`handoff-state.py` is on `PATH` in every session that loads this plugin. It
keeps the run's state in `<git common dir>/my-handoff/<slug>.json`, outside
the work tree. `handoff-state.py get <slug>` prints it, or exits 1 when there
is none.

1. `run auto` only, before any other check: `printenv MY_AUTORUN` prints
   exactly `<slug>`. If not, the reason is
   `MY_AUTORUN is not set to <slug>; the push guard is off`.
2. The spec's status is `approved`. For `run auto code` and
   `run auto review`, the spec is the task doc's design doc.
3. The spec has a valid Delegation section (see "Delegation"). A failure
   names the key: missing, unknown, or with a value outside its forms.
4. `auto plan`: the spec has no section titled Tasks. `auto code`: it has
   one.
5. The auto launch: `handoff-state.py get <slug>` exits 1, or its `next` is
   `finished`. If not, the reason is `a run for <slug> exists; use resume`.
6. `run auto <stage>`: `handoff-state.py get <slug>` prints a state, and its
   `next` equals `<stage>`. For `run auto review`, `next` is one of
   `review`, `merge-retry`, `merge`, `worktree-remove`, `fold` and `done`:
   the steps after the merge also run as the review stage.
7. `run auto code` with a spec as the task doc: the code-stage check "the
   plan is committed on `<base>`" checks the spec here. When the spec's
   `approved` edit is uncommitted, that check waits: it runs as sub-step c,
   after sub-step a has committed the edit. When the edit is already
   committed, it runs now, with the other code-stage checks.
8. A `run auto` session that is a restart (see "Restarted stages", under
   "Resume") skips the checks that expect a fresh start: no plan yet, no
   branch yet, no worktree yet.

When the checks pass, the auto launch creates the state with one locked
command, and then goes to "Launch". `<n>` is as "Parallel runs" says: `1` in
a project without the section.

```bash
handoff-lock.py main -- handoff-state.py start <slug> --max <n> \
  spec=<spec> task_doc=<task doc> next=<stage> branch= worktree= \
  squash_subject= head_before_fold= stopped= checked_base=
```

`<task doc>` is the spec for `auto code`, and
`docs/plans/<spec date>-<slug>.md`, the plan still to be written, for
`auto plan`. `start` replaces a `finished` state of the same slug, and
prints the run's slot. Because the cap check and the write are one locked
step, two starts at once cannot both pass the cap. Launch then types
`run auto <stage> <spec>` into the new window.

A non-zero exit is a failed start check: signal the line below, and write
nothing. It is not a stop, because a stop writes the state file, and that
file would count as a live run.

- Exit 1 with `refused: <k> auto runs are live (<slugs>); the most is <n>`, in a project without the section: `<name>: another auto run is live (<slug>); this project has no "Parallel runs" section`. Here `<slug>` is the other run's slug, taken from the script's line, not this spec's slug.
- The same exit, in a project with the section: `<name>: <n> auto runs are live (<slugs>), the most this project allows`, with the slugs from the script's line.
- Exit 1 with `refused: a run for <slug> exists; use resume`: `<name>: start check failed: a run for <slug> exists; use resume`, as start check 5.
- Any other non-zero exit, a lock timeout included: `<name>: start check failed: <the script's message>`.

### Plan stage

1. Run `superpowers:writing-plans` on the spec. Write the plan to
   `docs/plans/<spec date>-<slug>.md`. Skip that skill's closing question about
   how to execute: the code stage is the execution. Do not commit the plan
   yet: step 7 commits it with its review.
2. Name one execution skill in the plan's header. Replace the header's
   "subagent-driven-development (recommended) or executing-plans" with one of
   them. Use the project's rule when it names one. Otherwise pick
   `superpowers:subagent-driven-development` when the plan has several
   independent tasks, and `superpowers:executing-plans` when the tasks build
   on each other or are small. Print one line with the pick and its reason.
   The header also says that the project's review rules replace the skill's
   own reviews, when the project has such rules.
3. Run the project's plan review on the uncommitted plan. Under the `my`
   method rules that is `my:soundness-review --plan-only <plan path>`. The
   `--plan-only` token reviews the plan even when other sessions have
   uncommitted files on `<base>`. Take the review's path from the line it
   prints, `Review written to docs/plans/<filename>.`: an older review of the
   same plan makes the name end in `-plan-review-2.md`.
4. First, for each finding, ask: would the fix change what a component
   owns, a contract, the chosen option, or the scope? If no, its class is
   fix. If yes, it is a gate. Print one line per finding: the finding, its
   class, and the evidence for that class. Only then fix the findings whose
   class is fix.
5. Signal and stop on any gate: a finding whose fix would change a decision,
   or a spec decision that turns out to rest on a false premise. The signal
   names the files this stage wrote or edited and left uncommitted on
   `<base>`: the plan, the review (when step 3 wrote one) and the spec.
6. The stage's paths are the plan, the review, the spec (with its `approved`
   status edit) and the project's plans index when the project has one.
   When the project has a plans index, first add or update this plan's row
   in it, as the project's rules say. Then check that they hold only this
   stage's changes. Run `git diff HEAD -- <paths>` and read every hunk. The
   plan and the review are new files, which `git diff HEAD` does not show;
   this stage wrote them whole. So the hunks come from the spec and the plans
   index. If a hunk is
   not this stage's own change, for example another session's row in the
   plans index, signal `<name>: <file> holds another session's edit` and
   stop.

   **With a "Parallel runs" section,** the plans index, `ROADMAP.md`,
   `CHANGELOG.md` and `docs/DESIGN-SYSTEM.md` are shared docs. Before editing
   one, run `git diff --quiet HEAD -- <file>`. If it exits non-zero, someone
   else has uncommitted edits there: signal `<name>: <file> holds someone
   else's edits` and stop (row 19). The hunk check above then covers every
   hunk of the file.
7. Commit these paths, and only these, in one commit, following the
   project's rules for docs commits: `git add -- <paths>`, then
   `git commit -m "<message>" -- <paths>`. The `-- <paths>` on `git commit`
   commits only those paths, even when another session has staged files of
   its own. Then check that `git show --stat --format= HEAD` lists only
   these paths. A path with no change, such as an index that needed no
   edit, is not listed, and that is correct. If it lists another path,
   signal `<name>: the plan commit holds <path>` and stop.

   **With a "Parallel runs" section,** every commit in the main checkout runs
   under lock `main`, so the commit is one locked command that stages and
   commits. First read `git diff -- <paths>`: it shows what the command will
   stage, except the new plan and review, which this stage wrote whole. Then
   write the message with the Write tool to a new file in the session's
   scratchpad, and run:

   ```bash
   locked-commit.py -F <message file> <paths>
   ```

   `locked-commit.py`, on `PATH` like `handoff-lock.py`, stages and commits
   the paths under lock `main`, and no shell reads the message. It deletes
   the message file after the commit, and keeps it when a step fails. It
   ends with `git show --stat --format= HEAD` inside the lock, so it lists
   the commit this command made, even when another run commits right after.
   Check its list as above. A lock timeout is row 18.
8. Fold waiting fixups only when `<base>` is clean. The spec has fixups
   waiting when `git log --format='%h %s' <spec commit>..<base>` shows a
   commit whose subject is `fixup!`, a space, then the spec commit's
   subject.
   `git commit --fixup` writes the target's subject there, not its hash.
   `<spec commit>` is the commit that added the spec:
   `git log --diff-filter=A --format=%h -1 <base> -- <spec path>`. If one
   does and `git status --porcelain` prints nothing, run the project's
   pre-rebase check, then the fold: `git-fold-fixups.py` in the main
   checkout. A failed pre-rebase check is a gate: signal and stop. The
   script folds every waiting fixup on `<base>`, and refuses when that is
   not safe. Exit `1` means it refused and changed nothing: signal
   `<name>: fold refused: <its message>` and stop. Exit `3` means the
   rebase rewrote history and a check after it failed: signal
   `<name>: fold rewrote history and a check failed; HEAD before was <hash>`
   and stop. If `git status --porcelain` prints anything, skip the
   fold. The review stage folds them after the squash-merge, before its
   `done` marks (Review stage, step 8).

   **With a "Parallel runs" section,** skip this step. Nobody makes fixups
   there, so none wait, and a fold could give another run's cited commit a
   new hash.
9. Finish the project's other docs steps, then run "Launch" with
   `code <plan path>`, then "Finish". When step 8 skipped a fold, print
   `<name>: fixups left unfolded: <their hashes>. The review stage folds
   them after the merge.` just before Finish's last line, so that line stays
   last.

**In auto mode,** the plan stage changes in these steps:

- Step 5: a finding whose fix would change a decision, or a false premise,
  is row 4. With `decide`, fix it and record it in the plan's **Risk**
  section; with `stop`, stop as written.
- Step 6: another session's edit is row 3, a stop.
- Step 8: a failed pre-rebase check, or a fold exit of 1 or 3, is row 5, a
  stop.
- Step 9: just before "Launch", run
  `handoff-state.py set <slug> task_doc=<plan path> next=code`. Launch then
  opens `run auto code <plan path>`.

### Code stage

1. Take `<type>` from the plan: the Conventional Commits type of the work
   (`feat`, `fix`, `refactor` and so on). If the plan does not state it,
   infer it from the tasks, and state your choice in the output just before
   the Finish line.
   Create the worktree from the main checkout's root:
   `git worktree add .claude/worktrees/<slug> -b <type>/<slug>`.
   When the project's rules or the plan name the worktree and branch, use
   those names instead. If that worktree already exists, work in it, and
   first rebase its branch onto `<base>` when the project's rules say so.
   Implement the plan with the one skill its header names, else
   `superpowers:executing-plans`. Where the project's review rules differ
   from that skill's own reviews, the project's rules win.
2. Test each task as the project's rules define before its commit. After
   each task, read `git diff` for the test files the task touched. Run no
   code reviews and no end-of-branch checks: the review stage runs them.

   **Test runs.** While a task is in progress, run only the test
   files it touches. Chain the commands with `&&`, so a failed
   focused run never starts the full suite. Run the project's full
   test command once per task, just before the task's first commit.
   A fix round reruns only the test files that cover the fix, plus
   the project's typecheck when the fix changed code; it never runs
   the full suite, because the review stage runs the end-of-branch
   checks. Every task brief and fix message this stage writes
   repeats this rule in these words.

   **With a "Parallel runs" section,** apply its **Isolation** line, with
   `<slug>` and `<slot>` filled in, to every test and server command. Run
   every **Shared resources** command as
   `handoff-lock.py <name> --timeout 3600 -- <command>`, with
   `run_in_background`, and wait for its notification. A timeout is row 18.
   Any subagent prompt this stage writes gains two lines: the filled-in
   Isolation values, and the locked form of each shared-resource command.
3. Signal and stop on any gate: a new dependency, a change outside the
   project's scope, a test failure that survives
   `superpowers:systematic-debugging`, or a test assertion that the task
   removed or weakened.
4. When the project's rules or the plan end this work before the branch is
   done, for example because a batch squash-merges only after its last plan,
   signal `<name>: done; <the stop point the plan names>` and stop.
5. Otherwise run "Launch" with `review <plan path>`, then "Finish".

**In auto mode,** the code stage changes as follows.

Before step 1, when the task doc is a spec and its `approved` edit is not
committed (`git status --porcelain -- <spec>` prints it), commit that edit
in the main checkout with sub-steps a and b, then run sub-step c. This is
the commit the plan stage makes for a change with a plan.

- **a.** Find `<spec commit>`, the commit that added the spec, as in Plan
  stage, step 8. Run `git-fold-fixups.py check <spec commit>`. If it exits
  1, commit the edit as a normal `docs:` commit, with the scope the
  project's rules give docs. Otherwise commit it with
  `git commit --fixup <spec commit> -- <spec>`. Either way, commit only the
  spec: `git commit … -- <spec>`, then check that
  `git show --stat --format= HEAD` lists only the spec.
- **b.** If `git status --porcelain` in the main checkout prints nothing,
  fold as in Plan stage, step 8: a failed pre-rebase check, or a fold exit
  of 1 or 3, is row 5, a stop. If it prints anything, skip the fold. The
  review stage folds the waiting fixup after the merge.
- **c.** Then run the start check that waited (start check 7 in auto
  mode): the task doc is committed on `<base>`.

**With a "Parallel runs" section,** sub-step a always makes a normal `docs:`
commit, never `--fixup`, with `locked-commit.py` as in Plan stage, step 7,
and sub-step b is skipped: nothing folds there.

In the code stage's numbered steps:

- Step 1: after the worktree exists, run
  `handoff-state.py set <slug> branch=<branch> worktree=<worktree path>`,
  with the path as given to `git worktree add`.
- Every task commit carries the git trailer `Task: <N>`, where `<N>` is the
  task's position in the task doc's list of tasks, counted from 1. Add it
  with `git commit --trailer "Task: <N>"`. A restarted code stage uses it to
  find the first task not yet done (see "Resume").
- Step 3: a new dependency is row 6. Go on only when Delegation
  [Dependencies] lists the package by its exact name. A change outside the
  project's scope, a test failure that survives debugging, and a removed or
  weakened assertion are rows 7, 8 and 9: stops.
- Step 5: just before "Launch", run `handoff-state.py set <slug> next=review`.
  Launch then opens `run auto review <task doc>`.

### Review stage

The reviews run once, at the end of the branch. Everything a review subagent
must know goes into its prompt: a subagent reads no `CLAUDE.md`.

This session opened in the main checkout, which is on `<base>`. The branch
lives in `<worktree>`, the worktree from the start checks. Run every command
of this stage as `cd <worktree> && …`, so that tests, review reports and fixes
all land on the branch, and the main checkout stays clean.

1. **Range.** The range is `<base>..<branch>`. Never use a remote branch
   such as `origin/<base>`: it can lag the local `<base>`. The plans are
   `<doc>`, plus, in a batch, every other plan in `docs/plans/` whose header
   names the same branch. For each plan, note its spec and its **Risk**
   section.
2. **Checks before the reviews.** Run the checks the project's rules list
   for the end of a branch, for example an e2e suite, from the worktree, the
   way the rules say to run them from a worktree. Rules may name them
   without the words "end of a branch", for example "run e2e before pushing
   UI changes". Keep the passed and failed counts and the name of each
   failed test: the `done` mark records them. A failed test is a gate:
   signal and let the user decide whether it blocks the merge. When the
   rules name no such check, that is a gate too: signal and ask which checks
   to run. If the user says none, the `done` mark says
   `no end-of-branch checks run`.

   **With a "Parallel runs" section,** apply its **Isolation** line, with
   `<slug>` and `<slot>` filled in, to every check. Run every **Shared
   resources** command as `handoff-lock.py <name> --timeout 3600 -- <command>`,
   with `run_in_background`, and wait for its notification. A timeout is
   row 18.
3. **Map.** List the changed files and symbols with
   `git diff --stat <range>` and `git diff <range>`. For each symbol, find
   its callers:
   - Load the `LSP` tool with `ToolSearch("select:LSP")`, then call
     `findReferences`, `incomingCalls` or `documentSymbol` with the
     absolute path of the file inside `<worktree>`. LSP resolves against the
     main checkout, so when it returns nothing for a symbol the branch adds,
     rely on the next step.
   - Search each name token with `grep -rn '<token>' <worktree>` through
     `Bash`, because string-literal references are invisible to symbol tools
     and the `Grep` tool may be absent.

   Write the map to a file in the scratchpad.
4. **Reviews.** Send one message with one `Agent` call per review, so they run
   in parallel. Each subagent runs one review skill. The list comes from the
   project's rules. Without one, it is `/code-review high` and
   `my:soundness-review <range> <plan>`, once per plan. Always write the
   `/code-review` level out; without one it reuses the last level typed.
   Every prompt contains this block, filled in:

   ```text
   Work in <worktree>. Run every command as `cd <worktree> && …`, so that
   any report lands in <worktree>/docs/plans/.
   Review the range <range>, exactly this range. Do not use origin/<base>.
   Spec: <spec path>. Plan: <plan path>. The plan's Risk section lists known
   limits; a known limit in Risk is not a finding.
   Map of the changed symbols and their callers: <map file>.
   Do not write commit IDs from this branch. Name a change in words, like
   "the fix round" or "the branch head".
   ```

   In a batch, the `Spec:` and `Plan:` lines list every spec and plan of the
   batch, each plan with its spec. Each `my:soundness-review` subagent still
   gets its own plan as the skill's argument.

   **With a "Parallel runs" section,** the block gains two lines, filled in:

   ```text
   Isolation: <the filled-in Isolation values>. Apply them to every test and server command.
   Shared resources: run <command> only as `handoff-lock.py <name> --timeout 3600 -- <command>`.
   ```

5. **Scope check.** Read each report's scope note. Run a review again when it
   read another range than `<range>`.
6. **One fix round.** First give each finding one of three classes, tested
   in this order, so the first match wins. Gate: the fix would change what a
   component owns, a contract, the chosen option, or the scope. Risk: the
   finding is about input that today's code never produces; it goes into the
   plan's **Risk** section as a known limit. Fix: every other finding.
   Print one line per finding: the finding, its class, and the evidence for
   that class. If any finding is a gate, signal and stop before
   any fix. Otherwise fix the findings whose class is fix, test and commit
   as the project's rules say.
   Commit the review reports and the **Risk** edits on the branch, in the
   worktree: while the worktree exists, the plan is edited only
   there.
   Then run each review that led to a fix once more, with the same prompt
   block. That re-review is final: a new Critical finding is a stop for the
   user, whatever its class (row 13), and a lesser one goes into **Risk**.
7. Signal `<name>: ready to squash-merge <branch>` and stop.
8. After the user's yes, typed in this window, run these in order. Keep the
   branch: never run `git branch -d` or `-D` on it. Never push.
   1. Squash-merge into `<base>` as the project's rules say.
   2. Run `git worktree remove <worktree>`. The fold's pre-rebase check
      waits while a worktree holds a branch on top of the fold's target.
   3. Fold waiting fixups of the spec and the plan, found as in Plan stage,
      step 8. The fold gives new hashes to every later commit, the squash
      commit included, so it runs before the `done` marks cite that commit.
      Fold only when `git status --porcelain` in the main checkout prints
      nothing and the project's pre-rebase check passes. Otherwise signal
      `<name>: merged; fixups <their hashes> wait for a clean <base>` and
      stop. After the user's reply, check again, then fold. The fold is
      `git-fold-fixups.py` in the main checkout, and its exits `1` and `3`
      are signals as in Plan stage, step 8.
   4. Set the `done` marks as the project's rules say. They cite the squash
      commit's hash as it is after the fold, and the counts from step 2.

   **With a "Parallel runs" section,** these sub-steps change:

   - 1: just before the squash, run
     `git diff --name-only --no-renames $(git merge-base <base> <branch>) <base>`.
     When it lists a path outside the docs paths, signal
     `<name>: <base> gained code since the checks (<paths>); rebase and rerun them?`
     and wait. On the user's yes, run `git rebase <base>` in the worktree (on
     a conflict, `git rebase --abort`, then signal), rerun the step 2 checks,
     and check again. With no code path listed, squash-merge as one locked
     command, with the message as an argument:

     ```bash
     handoff-lock.py main -- sh -c 'test -z "$(git diff --cached --name-only)" || { echo "staged changes in the main checkout" >&2; exit 1; }; git merge --squash "$1" && git commit -m "$2" && git rev-parse --short HEAD || { git reset --merge; exit 1; }' sh <branch> "$(cat <<'EOF'
     <message>
     EOF
     )"
     ```

     In the command you run, the message lines and the `EOF` line start at
     column 0, because bash ends a heredoc only on a line that is exactly
     `EOF`; the indent above only keeps the list intact. The command
     refuses, and changes nothing, when something is already staged in the
     main checkout. When the squash or the commit
     fails, it runs `git reset --merge` inside the lock. On any failure,
     signal. On success, it prints the squash commit's short hash inside the
     lock: sub-step 4 cites that hash, not `HEAD`, which another run may
     have moved since.
   - 3: skip it. Nothing folds there.
   - 4: each `done` mark edits a shared doc only as Plan stage, step 6 says,
     and commits with `locked-commit.py`, as in Plan stage, step 7.

   Then run "Finish".

**In auto mode,** the review stage changes in these steps:

- Step 2: when the project's rules name no end-of-branch checks, run the
  commands in Delegation [End-of-branch checks] (row 11). With `none`, the
  `done` mark says `no end-of-branch checks run`. A failed test that
  Delegation [Failing end-of-branch tests] lists by its exact name does not
  stop the run, and the `done` mark names it (row 10). Any other failed test
  is a stop.
- Step 6: a finding of class gate is row 12. With `decide`, fix it as well
  and record it in the task doc's **Risk** section, in the worktree; its
  printed line keeps the class gate. A new Critical finding in the
  re-review is row 13, a stop, whatever its class: `decide` never covers
  it.
- Step 7: do not signal. Go on to step 8 without a yes (row 14).
- Step 8 runs as these sub-steps instead. Run them from the main checkout.
  A session whose state has `next` past `review` starts at the sub-step
  that `next` names: `merge` at 1, `worktree-remove` at 2, `fold` at 3,
  `done` at 4.
  1. Write the squash commit's subject as the project's rules say. Run
     `handoff-state.py set <slug> squash_subject="<subject>" next=merge`,
     then `git merge --squash <branch>`. On a conflict, follow row 15. When
     the commit is made, run
     `handoff-state.py set <slug> next=worktree-remove`.
  2. Run `git worktree remove <worktree>`, then
     `handoff-state.py set <slug> next=fold`. When `git worktree list` no
     longer shows `<worktree>`, a crash came after the remove: skip it.
  3. Find waiting fixups of the spec and the task doc as in Plan stage, step
     8. When none wait, go to the last line of this sub-step. When `<base>`
     is not clean, or the project's pre-rebase check fails, follow row 16.
     Otherwise run
     `handoff-state.py set <slug> head_before_fold=$(git rev-parse HEAD)`,
     then `git-fold-fixups.py`. Exit 1 or 3 is row 17. After the fold, or
     when none waited, run `handoff-state.py set <slug> next=done`.
  4. Find the squash commit by its subject: the one commit on `<base>` whose
     subject equals `squash_subject` in `handoff-state.py get <slug>`. The
     fold has changed its hash. Set the `done` marks, citing that hash, as
     the project's rules say. Then run
     `handoff-state.py set <slug> next=finished stopped=`, then the refill
     (see "Refill", under "From roadmap rows").
- Finish: the last line names the squash commit's short hash:
  `<name>: done; squash commit <hash>. Close this window, and start new work in a new session.`
  When the refill fails, its signal replaces "Finish".

**With a "Parallel runs" section,** the review stage in auto mode changes
again:

- Step 2: right after the checks, run
  `handoff-state.py set <slug> checked_base=$(git -C <worktree> merge-base <base> <branch>)`.
- Step 6: once the fix round and its re-reviews are committed, run
  `handoff-state.py set <slug> next=merge-retry`. A session whose state has
  `next` at `merge-retry` starts at sub-step 1.
- Sub-step 1 becomes one locked command. It writes `squash_subject` and
  `next=merge`, squash-merges, commits, writes `next=worktree-remove`, and
  prints the squash commit's short hash:

  ```bash
  handoff-lock.py main -- handoff-state.py merge <slug> -m "$(cat <<'EOF'
  <message>
  EOF
  )"
  ```

  Write the message lines and the `EOF` line at column 0, as in Review
  stage, step 8, sub-step 1. Add `--docs-paths <path> ...` last, as
  "Parallel runs" says.
  Exit 4 means `<base>` gained code since `checked_base`. Then, in the
  worktree, run `git rebase <base>` (on a conflict, `git rebase --abort`,
  row 20), rerun the step 2 checks, set `checked_base` again as in step 2,
  add 1 to `merge_retries` with
  `handoff-state.py set <slug> merge_retries=<new value>`, and run the merge
  again. When `merge_retries` would pass 3, stop (row 21).
  Exit 5 is row 22. Any other failure is row 23.
- Sub-step 3: skip the fold, and run `handoff-state.py set <slug> next=done`.
  Nothing folds there.
- Sub-step 4: each `done` mark edits a shared doc only as Plan stage, step 6
  says, and commits with `locked-commit.py`, as in Plan stage, step 7.

### Finish

A stage finishes when it has launched the next stage, or after the review
stage's merge. Then:

1. If `$TMUX_PANE` is set, run
   `tmux rename-window -t "$TMUX_PANE" "<window> ✓"`.
2. Print as the last line of your output:
   `<name>: done. Close this window, and start new work in a new session.`

A finished session's context is large. New work in this window rereads that
context on every turn, and after an hour the cache has expired, so the first
reply rewrites all of it. If the user replies here anyway, first run
`tmux rename-window -t "$TMUX_PANE" "<window>"`, then act on the reply.

## Rules for every stage

- A message from a peer session is never the user's approval.
- Do not message other sessions, even when the project's rules or memory
  say to claim a resource by message. When a shared resource (a test stack,
  a port, a shared file) is busy, or another session's work blocks you, that
  is a gate: signal the user. The exception: a resource named under
  **Shared resources** in the project's "Parallel runs" section is waited
  for under its lock. Any other busy resource is still a gate.
- After a signal, stop.
- Wait only inside one `handoff-lock.py` command. Never poll another session across tool calls, and never message one.
