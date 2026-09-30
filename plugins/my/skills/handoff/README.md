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

## Two ways to call it

- **Launch:** `/my:handoff <stage> <doc>` opens a new tmux window with a
  session for that stage, then stops.
- **Run:** `/my:handoff run <stage> <doc>` makes this session the stage.
  Launch types this command into the new window for you.

`<stage>` is `plan`, `code` or `review`. `<doc>` is one file in `docs/plans/`:

- `plan`: the approved spec.
- `code`: the committed plan.
- `review`: the plan the branch carries out.

You normally type only the first launch. Each stage launches the next.

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
7. Folds waiting fixups of the spec only when the main checkout is clean.
   Otherwise it names them, and the review stage folds them after the merge.
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
   worktree. Then it folds waiting fixups of the spec and the plan, when the
   main checkout is clean; otherwise it stops and asks you. Last, it marks
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

## What you need

- tmux, with the session running inside it.
- A session in `auto` or `bypassPermissions` mode, for windows to open on their
  own.
- The tools `ListAgents` and `PushNotification`.
