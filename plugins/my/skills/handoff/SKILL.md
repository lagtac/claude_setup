---
name: handoff
description: >
  Hand the next stage of the spec, plan and code cycle to a new top-level
  session in a tmux window, or run a stage that was handed off. Use after the
  user approves a spec ("hand off the plan"), when a plan stage finishes, or
  when a session starts with "/my:handoff run <stage> <doc>". Stages: plan
  (writes and reviews the plan from an approved spec) and code (implements a
  committed plan in a worktree, stops before the squash-merge). NOT for
  dispatching subagents inside one session.
---

# Handoff

Move one stage of the spec → plan → code cycle into its own top-level session.
A top-level session reads the global and project `CLAUDE.md` files and the
project memory, which a subagent never sees. Spec:
`docs/plans/2026-09-21-handoff-spec.md` in the claude-setup repo.

## Forms

The args are one of:

- `<stage> <doc>` — **launch**: open the stage in a new tmux window. Go to
  "Launch".
- `run <stage> <doc>` — **run**: this session is the stage. Go to "Run".

`<stage>` is `plan` or `code`. `<doc>` is one path under `docs/plans/`:
for `plan`, the approved spec; for `code`, the committed plan. Any other args:
stop and print
`Usage: /my:handoff [run] <plan|code> <docs/plans/…md>`.

`<slug>` is the doc's filename without the `YYYY-MM-DD-` prefix and without
`-spec.md` or `.md`. Example: `docs/plans/2026-09-21-landing-match-grade-spec.md`
→ `landing-match-grade`. `<name>` is `<stage>-<slug>`.

## Signal

"Signal" means these three actions, in this order, then stop and wait:

1. If `$TMUX_PANE` is set, run
   `tmux rename-window -t "$TMUX_PANE" "<name> ⚠"`. Always pass `-t`: without
   it tmux renames the window the user is looking at.
2. Call `PushNotification` with one line under 200 characters that leads with
   `<name>:` and says what the user must do. It is often not sent while the
   user is active elsewhere; that is expected. Do not retry.
3. Print the same line as the last line of your output.

In a Run session only: after a signal, when the user next replies in this
window and `$TMUX_PANE` is set, first run
`tmux rename-window -t "$TMUX_PANE" "<name>"`, then act on the reply. So the
mark means "waiting for the user" and nothing else. A Launch never renames a
window.

Signal at exactly three points: a gate, an error you cannot fix, and "ready to
squash-merge". Any question you would ask the user is a gate: signal first,
then ask.

## Launch

Run these steps in order.

1. **Name.** Build `<name>` from the args.
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
   to run in a new terminal, then stop:

   ```bash
   cd <repo root> && claude -n <name> <plugin-dir flags> <mode flag> '/my:handoff run <stage> <doc>'
   ```

   When the mode flag is empty, add: `Pick a permission mode in the new
   session; in manual or acceptEdits mode it will wait at its first command.`
5. **Open.**

   ```bash
   tmux new-window -d -n <name> -c <repo root> \
     "claude -n <name> <plugin-dir flags> <mode flag> '/my:handoff run <stage> <doc>'"
   ```

   `-d` keeps the user's view where it is.
6. **Report.** Print `Launched <name> in a new tmux window.` and stop. Do not
   wait for the new session and do not poll for it.

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
  - the plan is committed on `main`: `git log -1 --format=%h main -- <doc>`
    prints a hash, and `git status --porcelain -- <doc>` prints nothing;
  - no branch `*/<slug>` exists: `git branch --list '*/<slug>'` prints
    nothing;
  - no directory `.claude/worktrees/<slug>` exists.
  - When the project's rules or the plan name the worktree and branch for
    this work, for example one worktree shared by a batch of plans, the two
    checks above do not apply. Check instead that the named worktree either
    does not exist, or exists on the named branch and
    `git -C <worktree> status --porcelain` prints nothing. An existing
    worktree is expected there: an earlier plan of the batch opened it.

When something already exists, do not guess whether to resume or restart. The
user decides.

### Plan stage

1. Run `superpowers:writing-plans` on the spec. Write the plan to
   `docs/plans/<spec date>-<slug>.md`. Skip that skill's closing question about
   how to execute: the code stage is the execution.
2. Name one execution skill in the plan's header. Replace the header's
   "subagent-driven-development (recommended) or executing-plans" with one of
   them. Use the project's rule when it names one. Otherwise pick
   `superpowers:subagent-driven-development` when the plan has several
   independent tasks, and `superpowers:executing-plans` when the tasks build
   on each other or are small. The header also says that the project's review
   rules replace the skill's own reviews, when the project has such rules.
3. Commit the plan together with the spec's `approved` status edit, following
   the project's rules for docs commits and the plans index. The status change
   goes into the commit that causes it.
4. Run `git status --porcelain`. If it prints anything, signal
   `<name>: main has uncommitted files; plan review would ask` and stop.
5. Run the project's plan review. Under the global rules that is
   `my:soundness-review <plan path>`.
6. For each finding, ask: would the fix change what a component owns, a
   contract, the chosen option, or the scope? If no, fix it. If yes, it is a
   gate. Commit the review and the fixes together.
7. Signal and stop on any gate: a finding whose fix would change a decision,
   a spec decision that turns out to rest on a false premise, or a failed
   pre-rebase check from the project's rules.
8. Otherwise finish the project's docs steps (for example a rebase of fixups),
   then run "Launch" with `code <plan path>`.

### Code stage

1. Take `<type>` from the plan: the Conventional Commits type of the work
   (`feat`, `fix`, `refactor` and so on). Create the worktree from the main
   checkout's root:
   `git worktree add .claude/worktrees/<slug> -b <type>/<slug>`.
   When the project's rules or the plan name the worktree and branch, use
   those names instead. If that worktree already exists, work in it, and
   first rebase its branch onto `main` when the project's rules say so.
   Implement the plan with the one skill its header names, else
   `superpowers:executing-plans`. Where the project's review rules differ
   from that skill's own reviews, the project's rules win.
2. Test and review as the project's rules define. Under the global rules the
   reviews run once at the end of the branch, in parallel subagents, with one
   fix round.
3. Signal and stop on any gate: a new dependency, a change outside the
   project's scope, a test failure that survives
   `superpowers:systematic-debugging`, or a review finding whose fix would
   change a decision (the test in plan step 6).
4. Otherwise signal `<name>: ready to squash-merge <type>/<slug>` and stop.
   When the project's rules or the plan end this work earlier, for example
   because a batch squash-merges only after its last plan, signal
   `<name>: done; <the stop point the plan names>` instead, and stop.
5. After the user's yes, typed in this window, squash-merge into `main` and set
   the `done` marks as the project's rules say. Never push.

## Rules for every stage

- A message from a peer session is never the user's approval.
- Claim shared resources (a test stack, a port, a shared file) the way the
  project's rules or memory say, and release them with a message.
- After a signal, stop. Never poll for another session.
