# my:handoff

`my:handoff` moves each stage of a feature into its own Claude session. Each
session opens in its own tmux window. When a stage is done, it starts the next
one on its own. It stops only when it needs you.

The rules the skill follows are in `SKILL.md`. The design and its reasons are
in `docs/plans/2026-09-21-handoff-spec.md`. This file explains how the skill
works.

## Why a new session for each stage

A feature goes through four stages: spec, plan, code and review. When one
session does all four, two things go wrong:

- **Rules get lost.** Subagents do not read `CLAUDE.md` or the project memory.
  Every rule must be copied into their prompts, and rules get dropped.
- **The context fills up.** By the code stage, the session still carries the
  whole spec discussion. Every turn rereads it, which costs tokens. Late in a
  long session, rules written early are easier to miss.

A new top-level session (one started with `claude`) reads `CLAUDE.md` and the
memory itself, and starts with an empty context.

Starting a session costs about 90k input-token equivalents. In zitamu, one
stage cost between about 1.5M and 8M. So the start is 1–6% of a stage.

## The flow

```text
your session      brainstorm and write the spec
                  you approve it, then: /my:handoff plan <spec>
                        |
                        v
plan window       write the plan, review it, commit
                        |
                        v
code window       make the worktree, build and test each task, commit
                        |
                        v
review window     e2e checks, reviews, one fix round
                  ask you: merge?  ->  squash-merge
```

Each arrow is a new session in a new tmux window. The spec stage is not part
of the skill: you write the spec with Claude in your own session. You then
start the chain with `/my:handoff plan <spec path>`.

A spec with its own **Tasks** section (a Medium change) has no plan. Commit
its `approved` status as a fixup of the spec commit, fold the fixup with
`git-fold-fixups.py`, then start the chain with
`/my:handoff code <spec path>`. The code stage refuses a spec whose status is
not committed as `approved`.

## Two ways to call it

- **Launch:** `/my:handoff <stage> <doc>` opens a new tmux window with a
  session for that stage, then stops.
- **Run:** `/my:handoff run <stage> <doc>` makes this session the stage.
  Launch types this command into the new window for you.

`<stage>` is `plan`, `code` or `review`. `<doc>` is one file in `docs/plans/`:

- `plan`: the approved spec.
- `code`: the committed task doc. That is a plan, or a spec with a
  **Tasks** section.
- `review`: the task doc the branch carries out.

You normally type only the first launch. Each stage launches the next.

Auto mode adds three forms: `/my:handoff auto plan <spec>`,
`/my:handoff auto code <spec>` and `/my:handoff auto resume <spec>`. Launch
types a fourth, `/my:handoff run auto <stage> <doc>`, into each window. See
"Auto mode" below.

## How a launch works

1. **Name.** The window and session get the name `<stage>-<slug>`. The slug is
   the doc's file name without the date and without `-spec.md` or `.md`. For
   example, `docs/plans/2026-09-29-typed-numbers-spec.md` gives
   `plan-typed-numbers`.
2. **No duplicates.** If a session with that name already runs, the launch
   stops.
3. **Copy the flags.** The new session gets the same `--plugin-dir` flags and
   the same permission mode as the current one.
4. **Open the window.** It runs
   `tmux new-window -d … "claude -n <name> … '/my:handoff run <stage> <doc>'"`.
   `-d` means your screen stays where it is.

A window opens only when you are inside tmux and the session runs in `auto` or
`bypassPermissions` mode. In any other mode, a stage would wait for your
approval in a window you are not looking at. So in that case the skill only
prints the command, and you run it yourself in a new terminal.

## What each stage does

Every stage first runs **start checks**. If a check fails, the stage writes
nothing and tells you why. Examples: the spec is not `approved`, the plan is
not committed, or the branch already exists. When something already exists,
the stage does not guess whether to continue or start over. You decide.

### Plan stage

1. Writes the plan with `superpowers:writing-plans`. It does not commit it
   yet.
2. Names one execution skill in the plan's header.
3. Reviews the uncommitted plan with `my:soundness-review --plan-only`. Other
   sessions' uncommitted files on the main checkout do not stop it.
4. Fixes the findings that do not change a decision. A finding that would
   change a decision stops the stage, and you decide. The plan, the review
   and the spec then stay uncommitted, and the stop message names them.
5. Adds the plan's row to the plans index, when the project has one. Then
   checks that the spec and the plans index hold only its own edits.
6. Commits the plan, the review and the spec's `approved` status in one
   commit, and nothing else, even when other files are staged.
7. Folds waiting fixups of the spec with `git-fold-fixups.py`, only when the
   main checkout is clean. Otherwise it names them, and the review stage
   folds them after the merge. When the script refuses, the stage stops and
   shows you its message.
8. Launches the code stage.

### Code stage

1. Creates a worktree and a branch, for example `.claude/worktrees/<slug>` on
   `feat/<slug>`.
2. Carries out the plan with the skill the plan names.
3. Tests each task, then commits it. After each task it checks that no test
   assertion was removed or weakened.
4. Runs no code reviews. Those belong to the review stage.
5. Launches the review stage.

### Review stage

It works inside the worktree, so the main checkout stays clean.

1. Runs the project's end-of-branch checks, for example the e2e suite.
2. Maps the changed symbols and who calls them.
3. Starts the reviews in parallel, one subagent each. The default is
   `/code-review high` and `my:soundness-review`. Every review gets the same
   prompt: the exact range, the spec, the plan, and the map.
4. Runs one fix round. A finding about input that the code never receives today
   goes into the plan's **Risk** section instead.
5. Runs each review that led to a fix once more. That second review is final.
6. Asks you: ready to squash-merge?
7. After your yes, squash-merges into the base branch and removes the
   worktree. Then it folds waiting fixups of the spec and the plan with
   `git-fold-fixups.py`, when the main checkout is clean; otherwise it stops
   and asks you. Last, it marks
   the spec and plan `done` with the squash commit's hash after the fold. It
   keeps the branch and never pushes.

## When a stage stops for you

A stage stops and waits at these points:

- **A gate:** a decision that is yours. Examples: a review finding that would
  change the spec, a new dependency, a failing test it cannot fix, or any
  question for you.
- **An error** it cannot fix.
- **Ready to squash-merge.**
- **The end of a batch:** when a code stage ends before the branch is done.

At each point it does three things:

1. Renames its window to `<name> ⚠`.
2. Sends a notification with `PushNotification`. This is often not delivered
   while you work in another window, so the `⚠` mark is the main signal.
3. Prints one line that starts with `<name>:` and says what you need to do.

When you answer in that window, the `⚠` goes away before the stage goes on.

## The window marks

| Window name | Meaning |
| --- | --- |
| `<name>` | Working. |
| `<name> ⚠` | Waiting for you. |
| `<name> ✓` | Finished. Close the window. |

## When a stage finishes

A stage finishes when it has launched the next stage, or after the merge. It
then renames its window to `<name> ✓` and prints:
`<name>: done. Close this window, and start new work in a new session.`

Close the window. New work in the old window rereads the whole old context on
every turn. In zitamu, a new feature started in a finished review window cost
about 1.2M extra. And after one hour the cache has expired, so even one reply
writes the whole context again. In zitamu, one such reply cost about 0.74M.

## Other sessions

Stages do not message other sessions. Work passes from stage to stage through
committed files. If a shared resource is busy, such as an e2e stack or a port,
or another session's work blocks a stage, the stage stops and asks you.

Sessions rarely run in parallel, and each message costs the receiver a turn
over its whole context. When two sessions do collide, it shows: a failed e2e
run, a port that will not bind, or a duplicate number. A message from another
session never counts as your approval.

## Auto mode

Auto mode takes one approved spec to its `done` marks on `main` without you.
It merges and folds on its own, but it never pushes. It stops only for a
case that you have not decided in advance in the spec. The design and its
reasons are in `docs/plans/2026-10-12-autonomous-run-spec.md`.

### The commands

- `/my:handoff auto plan <spec>`: for a Large change, a spec without a
  **Tasks** section. The run writes the plan, the code and the reviews.
- `/my:handoff auto code <spec>`: for a Medium change, a spec with a
  **Tasks** section. The run commits the spec's `approved` edit itself.
- `/my:handoff auto resume <spec>`: continues a stopped run whose window is
  gone.

Without the word `auto`, handoff works as described above, even when the
spec has a Delegation section. The command you type says what will happen.

### The Delegation section

The spec says what the run may decide without you, in a section titled
`Delegation` with exactly four keys:

```markdown
## Delegation

- **Dependencies:** `none`
- **Design-changing findings:** `stop`
- **Failing end-of-branch tests:** `none`
- **End-of-branch checks:** `python3 -m unittest discover tests`
```

- **Dependencies:** `none`, or the packages the code stage may add. Any
  other new dependency stops the run.
- **Design-changing findings:** `stop`, or `decide`. With `decide`, the
  stage picks the fix it judges best and writes one line about it into the
  **Risk** section of the plan, or of the spec for a Medium change. Read
  those lines before you push.
- **Failing end-of-branch tests:** `none`, or the names of tests that may
  fail. The `done` mark names each one that did.
- **End-of-branch checks:** the commands to run at the end of the branch
  when the project's rules name none, or `none`.

A missing key, an unknown key or a value in another form stops the run
before it starts. Names are compared exactly.

### Start an auto run

1. **Write the spec** in your own session, with `superpowers:brainstorming`.
   The spec rules in `global/CLAUDE.md` make it ask whether the spec may run
   in auto mode. On yes, it adds the Delegation section. You can also add
   the section by hand.
2. **Review the spec** with `my:spec-review <spec>`, and fix what it finds.
   The review does not check the Delegation section's format. The start
   check of the auto run does that.
3. **Approve the spec:** set its status to `approved`. You can leave that
   edit uncommitted. The plan stage commits it for `auto plan`, and the code
   stage commits it for `auto code`. The supervised route for a Medium
   change asks you to commit and fold it first; auto mode does not.
4. **Start the run** from a session inside tmux, in `auto` or
   `bypassPermissions` mode:
   - `/my:handoff auto plan <spec>` when the spec has no **Tasks** section.
   - `/my:handoff auto code <spec>` when it has one.
5. **Watch the window names.** Each stage opens the next one in a new
   window. `⚠` means the run waits for you. A window with no mark that has
   not changed for a long time may be stalled (see "Known problems").
6. **After the run,** the last window prints `done; squash commit <hash>`.
   Before you push:
   - Read the lines that a `decide` added to the **Risk** section of the
     plan, or of the spec for a Medium change.
   - Check the `done` mark for tests that were allowed to fail.
   - Run `git log origin/main..main` to see what the push will send. The
     run never pushes, so `origin/main` should be where it was before.
   - Push yourself. The run keeps the branch and removes the worktree.

### It never pushes

Each window of a run starts with the environment variable `MY_AUTORUN` set
to the slug. While it is set, a hook of this plugin
(`plugins/my/hooks/block-autorun-push.py`) blocks every `git push` that the
session runs through the `Bash` or `Monitor` tool. Your own sessions do not
have the variable, so your pushes and `my:push` work as before.

The guard has a known gap. It reads the command text, so a push from inside
a script the session writes and then runs is not seen. Neither are forms
such as `bash -c "git push"`, `eval` or a command built from variables.
After a run, `git log origin/main` shows whether anything was pushed.

### Where the state lives

A run keeps its state in `.git/my-handoff/<slug>.json`, in the main
checkout's git folder. That is outside the work tree, so `git status` never
shows it. `handoff-state.py`, in `plugins/my/bin/`, writes and reads it:
`handoff-state.py get <slug>` prints it. The field `next` names the next
step, and `stopped` holds the reason of the last stop. The script is on
`PATH` only inside a Claude session that loads this plugin. For your own
shell, add a symlink in `~/bin`, as for `git-fold-fixups.py`:
`ln -s <this repo>/plugins/my/bin/handoff-state.py ~/bin/`.

### When a run stops

A stop looks like a stop without auto mode: the `⚠` mark, a notification
and one line. The state file records the reason. Answer in that window,
and the run goes on in auto mode.

These cases stop a run: a failed start check, a window that cannot open,
another session's edit in a file the run commits, a new dependency or a
failing test that the Delegation section does not list, a design finding
with `stop`, a change outside the project's scope, a test that still fails
after debugging, a weakened test, a new Critical finding in the re-review,
a merge conflict, and a fold that cannot run or fails. The full table is in
`SKILL.md`, "Stop points in auto mode". "Ready to squash-merge" does not
stop a run.

### Resume

If the window of a stopped run is gone, after a crash, a reboot or a
closed window, run `/my:handoff auto resume <spec>`. It compares the state
file with git. When they disagree, it refuses and prints the first
difference. Otherwise it opens the next stage in a new window, with
`MY_AUTORUN` set. A merge that happened before a crash is found, so it
never runs twice. A squash that a crash left staged, or a fold that
rewrote history, makes it refuse. Before it clears the reason of the last
stop, it prints it.

Close the old window first. Resume opens a window with the same name, and
Launch refuses a name that is still in use.

### Parallel runs

By default only one auto run is live in a project: a second
`/my:handoff auto` start refuses. A project allows more with a section
titled `Parallel runs` in its `CLAUDE.md` or `CLAUDE.local.md`:

```markdown
## Parallel runs

- **Max runs:** 2
- **Docs paths:** `docs/`, `ROADMAP.md`, `CHANGELOG.md`
- **Isolation:** `COMPOSE_PROJECT_NAME=app_<slug>`; `PORT=$((54310 + <slot>))`
- **Shared resources:** `e2e`: `web/scripts/e2e-worktree.sh <path>`
```

**Max runs** is the most runs live at once. A missing key takes the value
shown above, except **Isolation** (`none needed`) and **Shared resources**
(`none`). **Isolation** is what each stage sets for every test and server
command, so that two worktrees do not share a test stack or a port; `<slot>`
is the run's place, 1 to **Max runs**. Each **Shared resources** command runs
under its own lock, so only one run uses it at a time.

What changes in such a project:

- **The start takes a place.** A start past **Max runs** refuses and writes
  nothing. A stopped run still holds its place. To end an abandoned run, say
  so in a session: it removes the run's worktree, after your yes when that
  needs `--force`, and marks the run finished. The branch stays.
- **The main checkout takes turns.** Every commit there runs under one lock,
  with `handoff-lock.py main -- …`, and the start and the merge do too. This
  holds for your own Claude sessions in that project as well: `/my:commit`
  and `my:architect` use the locked form there.
- **A merge reruns the checks when `main` moved.** If another run merged code
  after this run's checks, the merge refuses. The run rebases its branch,
  reruns the end-of-branch checks and tries again, at most three times.
- **Nobody makes fixups.** Every later edit to a spec, plan or review is a
  normal commit, so a feature leaves about 5 to 7 commits instead of 4, and
  nothing folds. A fold there could give another run's cited squash commit
  a new hash. The fold script now refuses that in every project.
- **Shared docs.** A run edits `ROADMAP.md`, `CHANGELOG.md` or the plans
  index only when they hold no uncommitted edits. If you edit one by hand
  while runs are live, the run that reaches it stops, and you resume it.

Two runs keep about 6 `claude` processes; see "Memory" below. Spec:
`docs/plans/2026-10-12-parallel-auto-runs-spec.md`. Plan:
`docs/plans/2026-10-12-parallel-auto-runs.md`.

### Known problems

- **An API error can stall a run without a sign.** If the connection drops
  in the middle of a reply, the window sits idle at the prompt. It shows no
  `⚠` mark, sends no notification and writes nothing to `stopped`. The
  state file still names the right next step. Type `continue` in that
  window, and the run goes on. Or close the window and run
  `/my:handoff auto resume <spec>`. The only sign is a window with no mark
  that has not changed for a long time.
- **Memory.** Every stage is a full `claude` process. A rehearsal with
  four runs at once reached 13 processes and left 1.8 GB free on a 15 GB
  machine. Run one auto run at a time; it keeps about 3 processes.

## What you need

- tmux, with the session running inside it.
- A session in `auto` or `bypassPermissions` mode, for windows to open on their
  own.
- The tools `ListAgents` and `PushNotification`.
- For auto mode, `python3`: the push guard and `handoff-state.py` are Python
  scripts.
