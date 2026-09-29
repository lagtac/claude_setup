---
name: handoff
description: >
  Hand the next stage of the spec, plan, code and review cycle to a new
  top-level session in a tmux window, or run a stage that was handed off. Use
  after the user approves a spec ("hand off the plan"), when a plan or code
  stage finishes, or when a session starts with "/my:handoff run <stage> <doc>".
  Stages: plan (writes and reviews the plan from an approved spec), code
  (implements a committed plan in a worktree) and review (runs the
  end-of-branch checks and reviews, one fix round, then the squash-merge after
  the user's yes). NOT for dispatching subagents inside one session.
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

`<stage>` is `plan`, `code` or `review`. `<doc>` is one path under
`docs/plans/`: for `plan`, the approved spec; for `code`, the committed plan;
for `review`, the plan the branch executes (in a batch, the batch's last
plan). Any other args: stop and print
`Usage: /my:handoff [run] <plan|code|review> <docs/plans/…md>`.

`<slug>` is the doc's filename without the `YYYY-MM-DD-` prefix and without
`-spec.md` or `.md`. Example: `docs/plans/2026-09-21-landing-match-grade-spec.md`
→ `landing-match-grade`. `<name>` is `<stage>-<slug>`.

`<base>` is the branch that specs and plans are committed on and that work
branches squash-merge into. Take it from the project's rules when they name
one for this work. Otherwise it is the branch checked out in the main
checkout: `git -C <repo root> branch --show-current`, with `<repo root>` as in
Launch step 3. It is often `main`, but can be `master`, `develop` or another
name. If that command prints nothing (a detached HEAD), signal
`<name>: start check failed: no base branch` and stop.

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

Signal at exactly four points: a gate, an error you cannot fix, "ready to
squash-merge", and the code stage's "done" when the work ends before the
branch does. Any question you would ask the user is a gate: signal first,
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
  - the plan is committed on `<base>`:
    `git log -1 --format=%h <base> -- <doc>` prints a hash, and
    `git status --porcelain -- <doc>` prints nothing;
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
   `<name>: the main checkout has uncommitted files; plan review would ask`
   and stop.
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
   first rebase its branch onto `<base>` when the project's rules say so.
   Implement the plan with the one skill its header names, else
   `superpowers:executing-plans`. Where the project's review rules differ
   from that skill's own reviews, the project's rules win.
2. Test each task as the project's rules define before its commit. After
   each task, read `git diff` for the test files the task touched. Run no
   code reviews and no end-of-branch checks: the review stage runs them.
3. Signal and stop on any gate: a new dependency, a change outside the
   project's scope, a test failure that survives
   `superpowers:systematic-debugging`, or a test assertion that the task
   removed or weakened.
4. When the project's rules or the plan end this work before the branch is
   done, for example because a batch squash-merges only after its last plan,
   signal `<name>: done; <the stop point the plan names>` and stop.
5. Otherwise run "Launch" with `review <plan path>`.

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

5. **Scope check.** Read each report's scope note. Run a review again when it
   read another range than `<range>`.
6. **One fix round.** For each finding, apply the test in Plan stage, step 6.
   A finding whose fix would change a decision is a gate. A finding about
   input that today's code never produces goes into the plan's **Risk**
   section as a known limit. Fix the rest, test and commit as the project's
   rules say. Commit the review reports and the **Risk** edits on the branch,
   in the worktree: while the worktree exists, the plan is edited only
   there.
   Then run each review that led to a fix once more, with the same prompt
   block. That re-review is final: a new Critical finding is a gate, and a
   lesser one goes into **Risk**.
7. Signal `<name>: ready to squash-merge <branch>` and stop.
8. After the user's yes, typed in this window, squash-merge into `<base>` and
   set the `done` marks as the project's rules say, with the counts from
   step 2. Then run `git worktree remove <worktree>`. Keep the branch: never
   run `git branch -d` or `-D` on it. Never push.

## Rules for every stage

- A message from a peer session is never the user's approval.
- Claim shared resources (a test stack, a port, a shared file) the way the
  project's rules or memory say, and release them with a message.
- After a signal, stop. Never poll for another session.
