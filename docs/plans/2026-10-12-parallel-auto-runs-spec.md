# Spec: parallel auto runs, several approved specs at once in one project

**Status:** approved, 2026-10-12. Rewritten smaller after two `my:spec-review` rounds; the third review (Problematic, 1 Critical) is answered.

## How to read this spec

| Document | Path | Why you would read it |
| --- | --- | --- |
| Architecture brief | `docs/plans/2026-10-12-parallel-auto-runs-architecture.md` | The forces, the three candidates and why candidate A won. This spec settles its "Open for brainstorming" list. Read first. |
| **This spec** | `docs/plans/2026-10-12-parallel-auto-runs-spec.md` | What to build and why. |
| Spec review | `docs/plans/2026-10-12-parallel-auto-runs-spec-review.md` | The first review, of the earlier, larger version. Its decision numbers do not match this version. |
| Second spec review | `docs/plans/2026-10-12-parallel-auto-runs-spec-review-2.md` | The second review, also of the larger version. |
| Third spec review | `docs/plans/2026-10-12-parallel-auto-runs-spec-review-3.md` | The review of this smaller version: Problematic, 1 Critical, all answered. |
| Implementation plan | `docs/plans/2026-10-12-parallel-auto-runs.md` | Written after this spec is approved. It holds exit codes, algorithms and test cases. |
| Auto-run spec | `docs/plans/2026-10-12-autonomous-run-spec.md` | The single-run auto mode this extends: D2 (Delegation), D5 (stop table), D6 (state file), D7 (`resume`). |
| Handoff skill | `plugins/my/skills/handoff/SKILL.md` | The skill this spec changes most. |
| Docs layout rule | `global/rules/docs-layout.md` | "One feature, four commits on `main`", steps 4, 8 and 9. |
| Global instructions | `global/CLAUDE.md` | The Git Workflow section and the Medium paragraph. |
| Fold script and tests | `plugins/my/bin/git-fold-fixups.py`, `plugins/my/tests/test_git_fold_fixups.py` | Gets two new refusals (D6). |
| State script and tests | `plugins/my/bin/handoff-state.py`, `plugins/my/tests/test_handoff_state.py` | Gets `live`, `start`, `merge` and new fields (D3, D7). |
| Efficiency critique | `docs/reports/2026-10-09-workflow-efficiency-critique.md` | M1: the timings behind the brief's estimate 1. |

## Context

`my:handoff auto` takes one approved spec to its `done` marks without the user.
It assumes it is the only run in the project. Three things break when two runs
share one project:

1. **The main checkout has many writers.** Plan stages, merges and `done`
   marks of different runs commit there, and so does the user. Two commits at
   once collide on `.git/index.lock`. Two edits of `ROADMAP.md` at once can end
   up in one commit.
2. **A fold rewrites `main`.** `git-fold-fixups.py` rebases from the fixup's
   target to `HEAD`, so every commit in that range gets a new hash. If another
   feature's squash commit is in the range, its `done` mark now cites a commit
   that is not on `main`. No current refusal sees this.
3. **Test stacks are shared.** zitamu's e2e uses one Docker project,
   `realestate_e2e`, and port 54310.

## Goal

1. The user starts 2 to 4 auto runs in one project, each with
   `/my:handoff auto plan <spec>` or `/my:handoff auto code <spec>`.
2. Each run ends in one of the two end states of the auto-run spec: merged with
   its `done` marks, or stopped with a clear line and a state file.
3. No run corrupts `main`. No `done` mark cites a commit that is not on
   `main`. A stop in one run leaves the others going.

## Out of scope

- **Answering "what can we do in parallel?"** from the roadmap. A later spec
  for `my:roadmap-management`. Until then the user picks the specs.
- **A three-way merge for shared docs.** A run stops instead when a shared doc
  holds someone else's edits (D5).
- The user designing a spec alongside live runs, beyond the lock rule (D4).
- Parallel tasks inside one feature.
- The "Parallel runs" sections of zitamu and diagoradisa-annotator, and their
  stack fixes. Each is a later spec in its own repo.
- Runs on more than one machine.
- A merge queue with first-in-first-out order (brief, Candidate B).

## Decisions

**D1: A project opts in with a "Parallel runs" section** in its `CLAUDE.md` or
`CLAUDE.local.md`:

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
| Docs paths | `docs/`, `ROADMAP.md`, `CHANGELOG.md` | Changes only under these paths are not code (D6, D7). A path ending in `/` is a folder. Everything else is code, including Markdown skills. |
| Isolation | `none needed` | What every stage sets for each command it runs in the worktree, so that worktrees do not share test stacks or ports. It may use `<slug>` and `<slot>` (D3). |
| Shared resources | `none` | Commands that only one run may use at a time, each with a lock name. Each runs under its lock (D2). |

Sessions read the section. Scripts take the docs paths as an argument.
Without the section, a second auto run refuses to start (D3). Of the rest of
this spec, only the fold refusal of D6 applies there. The start refusal is new:
today a second run starts.

**D2: `handoff-lock.py` runs one command under a named lock.** New script in
`plugins/my/bin/`, Python standard library:

```text
handoff-lock.py <name> [--timeout <seconds>] -- <command> [<arg> ...]
```

- It takes `fcntl.flock` on `<git common dir>/my-handoff/locks/<name>.lock`, so
  worktrees and the main checkout share each lock. Then it replaces itself with
  the command and keeps the lock open, so the lock lives exactly as long as
  the command. The exit code is the command's.
- The kernel frees the lock when the command ends or dies. A crash never
  leaves a lock held, and no lock spans two tool calls.
- When the wait times out, it runs nothing and exits with a code of its own.
  The default timeout, 90 s, is below the Bash tool's 120 s.
- It disables `git gc --auto` detaching for the command. Otherwise a detached
  `gc` keeps the lock after the command ends.
- A shared resource uses `--timeout 3600` and runs with `run_in_background`,
  because the brief's estimate 2 puts the worst wait at 30 minutes.

"Rules for every stage" in `SKILL.md` changes from "never poll for another
session" to: "Wait only inside one `handoff-lock.py` command. Never poll
another session across tool calls, and never message one." A resource named
under **Shared resources** is waited for under its lock; any other busy
resource is still a gate.

Rejected: a lease that spans tool calls (it stays held when a session crashes).
Rejected: a queue daemon (brief, Candidate B).

**D3: Start checks, slot and cap.** `handoff-state.py live` prints one line per
run whose `next` is not `finished`: slug, slot, `next`, stop line, branch.

A new run starts with one locked command, in place of the auto launch's first
`handoff-state.py set`:

```text
handoff-lock.py main -- handoff-state.py start <slug> --max <n> <field>=<value> ...
```

It refuses and writes nothing when other live runs already number `<n>`.
Every other failure of this command, a lock timeout included, is also a
refused start: the launch prints the message and writes nothing. A stop would
write a state file, and that file would count as a live run.
Otherwise it picks `slot`, the lowest whole number from 1 that no live run
uses, writes the state file and prints the slot. Without a "Parallel runs"
section, the launch passes `--max 1`. Because the check and the write are one
locked step, two starts in the same second cannot both pass the cap.

This runs only when a new run starts. A `run auto` stage session and
`auto resume` continue a run that already holds its place. The refusal lines:

- `<name>: another auto run is live (<slug>); this project has no "Parallel runs" section`
- `<name>: <n> auto runs are live (<slugs>), the most this project allows`

A stopped run still counts toward `Max runs`. **To end an abandoned run,** the
user says so in a session. The session runs `git worktree remove <worktree>`
(with `--force` only after the user's yes), then
`handoff-state.py set <slug> next=finished stopped="ended by the user"`. The
branch stays.

**D4: Every commit in the main checkout runs under lock `main`.** This holds,
in a project with the section, for the auto stages and for every Claude
session the user runs there. The `git add` goes inside the same locked
command:

```text
handoff-lock.py main -- sh -c 'git add -- "$@" && git commit -m "<message>" -- "$@"' sh <paths>
```

This leaves no moment for a `git diff --cached` reread. So in a project with
the section, the session reads `git diff -- <paths>` before the locked command,
which shows what it will stage, and `git show --stat HEAD` after it. `/my:commit`
and `my:architect` use this form there.

The merge (D7) and the start (D3) also run under lock `main`. Subagents commit
only in their worktree, whose index is their own, so they never take it.
Commits from a plain terminal take no lock; git refuses them while
`index.lock` exists, and the user retries.

**D5: No fixups, and shared docs only when clean.** In a project with the
section:

- **Nobody makes fixups,** neither the auto stages nor the user's sessions.
  Every later edit to a spec, plan or review is a normal commit. This is the
  brief's decision "auto mode makes no fixups", extended to the user. A fixup
  made while runs are live can get stuck behind another run's squash commit
  once that commit's `done` mark cites it, because D6 then refuses its fold.
  So the handoff fold steps (Plan stage step 8, the auto code stage's step 2,
  the fold in Review stage step 8) and
  `docs-layout.md` step 9 are skipped, and steps 4 and 8 make normal commits.
- **Shared docs** are `ROADMAP.md`, `CHANGELOG.md` and the plans index. A stage
  edits one only when `git diff --quiet HEAD -- <file>` shows no uncommitted
  edits. Before the commit, it checks that every hunk in the file is its own,
  as Plan stage step 6 does today for the run's own files. If either check
  fails, the run stops. The `done` marks follow the same rule. This narrows
  the race between two writers of one shared doc, but does not close it
  (Risk).

Without the section, folds work as today, with the new refusal of D6.

**D6: A new fold refusal.** `git-fold-fixups.py`, for the fold and for
`check`, refuses when a commit after the oldest target is cited in a file
under the docs paths at `HEAD`, by its 7-character short hash. A fold would
give that commit a new hash, and the citation would point at nothing.

A commit that nobody cites yet may get a new hash. This keeps the review
stage's fold working: it folds after its own squash-merge and before the
`done` marks, which find the squash commit by its subject or cite its hash
after the fold.

New option `--docs-paths <path> ...`, with the default list of D1. The
refusal applies in every project, with or without the section.

Rejected: also refusing when a later commit changes code. It blocked the
review stage's own fold, whose range always holds its own squash commit.

**D7: The merge lands only code that was checked on the current `main`.**
`handoff-state.py` gets the fields `checked_base` and `merge_retries`, and the
subcommand `merge <slug> -m <message> [--docs-paths ...]`, run under lock
`main` in the main checkout.

- **`checked_base`** is `git merge-base <base> <branch>`, recorded right after
  the last check run. It is not the tip of `<base>`: if another run merged
  while this branch was built, the tip holds code that these checks never saw.
- **`merge` guarantees:** it refuses, changing nothing, when the main checkout
  has staged changes, or when `git diff <checked_base> <base>` touches a path
  outside the docs paths. On a squash conflict, or when the squash commit
  fails, it runs `git reset --merge` and leaves no staged squash behind.
  Before the squash it records `squash_subject` and `next=merge`, so `check`
  can detect a merge that a crash interrupted, as today.
- **When the base moved,** the review stage, in the worktree, runs
  `git rebase <base>`, reruns the end-of-branch checks, sets `checked_base`,
  adds 1 to `merge_retries`, and runs `merge` again. It does not rerun the
  reviews: the checks cover the combined code. After three retries it stops.
- **`merge-retry`** is a new value of `next`. The review stage sets it once the
  reviews and the fix round are committed. Resume sends it to the review
  stage, which starts at the merge step. `auto resume` resets
  `merge_retries` to 0.

The brief's estimate 1 gives about 28% of runs rebasing once, but it assumes a
0.5 h window. Because `checked_base` is the fork point, the window is the
branch's whole life, 1.1 h at the median, so about half of runs rebase once.
Runs that use up the three retries stay far under 1%.

**D8: Test stacks.**

- Every stage that runs a command in the worktree applies the **Isolation**
  line, with `<slug>` and `<slot>` filled in, to every test and server command.
- Every subagent prompt that a stage writes contains the filled-in Isolation
  values and the locked form of each shared-resource command, because
  subagents read no `CLAUDE.md`.
- Every **Shared resources** command runs as
  `handoff-lock.py <name> --timeout 3600 -- <command>`, with
  `run_in_background`.

## Stop points

The auto-run spec's D5 table gains these cases. Each is a stop with `next`
unchanged unless the row says otherwise.

| Stage | Case |
| --- | --- |
| any | Lock `main` or a shared-resource lock times out, except at the start (D3). |
| any | A shared doc holds someone else's edits (D5). |
| review | The worktree rebase conflicts: `git rebase --abort`, stop with `next=merge-retry`. |
| review | The base moved a fourth time: stop with `next=merge-retry`. |
| review | `merge` hits a squash conflict: stop with `next=merge`, as row 15 today. |
| any | Any other failure of `handoff-lock.py` or `merge`: stop, with the script's message in the stop line. |

Rows 5, 16 and 17 (fixups waiting, the fold) cannot arise in a project with
the section, because nothing folds there. A refused start (D3) is not a stop:
it writes nothing.

## Rule text

- `global/rules/docs-layout.md`, "One feature, four commits on `main`": a
  paragraph saying that in a project with a "Parallel runs" section, every
  commit in the main checkout runs under `handoff-lock.py main`, steps 4 and 8
  make normal commits, and step 9 is skipped. Four commits remain the goal
  elsewhere.
- `global/CLAUDE.md`, Git Workflow: the lock rule of D4, because every session
  reads this file. The Medium paragraph: in a project with the section, the
  `approved` edit is a normal commit, not a fixup. The rule "Read
  `git diff --cached` before every commit" gets the D4 exception.
- `plugins/my/skills/handoff/SKILL.md`: D2 to D8 and the stop points.

## Delegation

- **Dependencies:** `none`
- **Design-changing findings:** `stop`
- **Failing end-of-branch tests:** `none`
- **End-of-branch checks:** `python3 -m unittest discover plugins/my/tests`

## Files

| File | Change |
| --- | --- |
| `plugins/my/bin/handoff-lock.py` | New (D2). |
| `plugins/my/bin/git-fold-fixups.py` | The new refusal and `--docs-paths` (D6). |
| `plugins/my/bin/handoff-state.py` | `live`, `start`, `merge`; fields `slot`, `checked_base`, `merge_retries`; `next` value `merge-retry` (D3, D7). |
| `plugins/my/skills/handoff/SKILL.md` | D2 to D8, stop points. |
| `plugins/my/skills/handoff/README.md` | A "Parallel runs" section for a reader. |
| `plugins/my/commands/commit.md` | The locked form and its reread, in a project with the section (D4). |
| `plugins/my/skills/architect/SKILL.md` | The locked form for the brief's commit, in a project with the section (D4). |
| `global/rules/docs-layout.md` | Rule text. |
| `global/CLAUDE.md` | Rule text. |
| `plugins/my/tests/test_handoff_lock.py` | New. |
| `plugins/my/tests/test_parallel_runs.py` | New: the integration test. |
| `plugins/my/tests/test_git_fold_fixups.py` | Extended. |
| `plugins/my/tests/test_handoff_state.py` | Extended. |
| `README.md` | `handoff-lock.py` under `plugins/my/bin/`. |
| `ROADMAP.md` | A row for this feature under "Design workflow". |

## Trade-offs

- **A lock per command versus a queue.** The lock is one small script and no
  process. It gives no order: whichever run takes the lock first merges first.
  With 2 to 4 runs merging hours apart, order hardly matters (brief, estimate
  1).
- **No fixups versus folding at once.** Normal commits need no new fold mode,
  and no fixup can get stuck. The cost: about 5 to 7 commits per feature
  instead of 4, in projects with the section. Rejected: a `commit` mode that
  folds at once or falls back to a normal commit (an earlier draft); it adds a
  mode, an undo path and its failure cases for a few saved commits.
- **Stop on a dirty shared doc versus a three-way merge.** The stop needs no
  script. The cost: a run stops when the user has uncommitted edits in
  `ROADMAP.md` or `CHANGELOG.md` at that moment, and the user resumes it.
  Rejected: `handoff-merge-file.py` (an earlier draft), a merge through a
  temporary git index.
- **The merge as a script.** One subcommand and its tests, against prose that
  each review stage would have to get right.

## Dependencies

None. Python 3 standard library, git, tmux and Claude Code, as handoff uses
today.

## Risk

- **Hard to reverse: the "Parallel runs" section.** Every project that adopts
  it carries its four keys. A later change means editing those projects, or
  keeping the old keys valid.
- **The locks are advisory.** A session that commits without
  `handoff-lock.py`, or a plain terminal commit, can collide on `index.lock`
  or land between two steps of a run. Detection: git's `index.lock` error;
  `git show --stat` after each commit, which the stages already run.
- **The squash refuses over the user's uncommitted edits** in a file the
  branch changes. That is row 15, a stop.
- **Shared-doc stops.** Editing `ROADMAP.md` by hand while runs are live stops
  the run that reaches its `done` marks at that moment.
- **Two writers of one shared doc can still mix.** The clean check, the
  edit, the hunk check and the locked commit are separate tool calls. If run
  B edits `ROADMAP.md` after run A's hunk check and before A's commit, A's
  commit takes B's hunk. B's commit then has nothing to commit and fails,
  which is a stop. Detection: `git show --stat` after each commit, and that
  stop.
- **A manual fold without `--docs-paths`** uses the default list. In a project
  whose docs paths differ, it may refuse a safe fold or allow an unsafe one.
- **A locked command that starts a background process** passes the lock to
  it, so the lock stays held until that process ends. A locked command must
  not start a server that outlives it. Detection: the next lock times out.
- **A stopped run holds a place under `Max runs`** until the user resumes or
  ends it.
- **Design dependencies between specs are not detected.** The user's choice
  of specs is the only protection. Text overlap is caught by D7.
- **Cost.** Assumed, never confirmed: each run about 3 stage sessions at 1.5M
  to 8M tokens, plus one check rerun per retry.
- **Blast radius.** `git-fold-fixups.py` is called from `docs-layout.md`, the
  Medium paragraph of `global/CLAUDE.md`, handoff's Plan, Code and Review
  stages, and both READMEs. The new refusal applies in every project. The plan
  must sweep the callers with `git grep` before changing them.
- **Manual steps.** One rehearsal, started by the user (Testing).

## Testing

All tests are `unittest` files in `plugins/my/tests/`, written red first, in
temporary fixture repos. The plan lists the cases. Each file must prove:

- **`test_handoff_lock.py`:** a second holder waits, a different name does
  not, a timeout runs nothing, a killed holder frees the lock, a worktree and
  the main checkout share the lock, and the exit code passes through.
- **`test_git_fold_fixups.py`:** the refusal fires for a cited commit after
  the target, an uncited later commit that changes code does not refuse, and
  `--docs-paths` changes the list.
- **`test_handoff_state.py`:** `live` and `start` (lowest free slot, cap
  refusal and every other failure write nothing, two concurrent starts never
  pass the cap), the new
  fields and `next` value, and every `merge` guarantee of D7.
- **`test_parallel_runs.py`:** two simulated runs in one fixture repo, driven
  only through the real scripts and `git`, in two orders. A merges after B's
  checks, and A merges before B's checks run. In both, B's first `merge`
  refuses, B's merge after the rebase succeeds, and every hash cited in a
  `done` mark is on `main`.
- **Rehearsal, once, before the spec is marked `done`.** In a separate tmux
  server, against a fixture repo whose `origin` is a local bare repo, with
  `Max runs: 2` and two tiny Medium specs that change the same source file in
  different places. The user starts both runs. Check: a third start refuses
  with the `Max runs` line, both runs end with their `done` marks on `main`
  (one after a retry), and the bare repo is unchanged.

## Open questions

None.
