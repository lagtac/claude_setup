# Spec: `my:handoff`, hand a cycle stage to a new top-level session

**Status:** done, 2026-09-22. Shipped in 88afd8a.

## How to read this spec

| Document | Path | Why you would read it |
| --- | --- | --- |
| **This spec** | `docs/plans/2026-09-21-handoff-spec.md` | What to build, why, and the trade-offs. Start here. |
| Spec review | `docs/plans/2026-09-21-handoff-spec-review.md` | The first `my:spec-review` report on this spec. |
| Spec re-review | `docs/plans/2026-09-21-handoff-spec-review-2.md` | The second report, on the spec after the first review's answers. |
| Implementation plan | `docs/plans/2026-09-21-handoff.md` | Written after this spec is approved. Test steps and commits. |
| Global instructions | `GLOBAL-CLAUDE.md` | The Superpowers trigger table, the "Spec → Plan two-artifact flow", "No silent reinterpretation", "Code Review Routing" and "Git Workflow". The stages follow these rules; this spec does not change them. |
| Docs layout rule | `GLOBAL-rules/docs-layout.md` | The `**Status:**` line and its values. The start checks read it. |
| Existing skill to copy from | `my-plugin/skills/spec-review/SKILL.md` | Model for the frontmatter and the step layout. |
| Test precedent | `docs/plans/2026-09-16-spec-review-skill.md` | "How tests run": headless `claude -p --plugin-dir` runs against a worktree plugin. |
| Plugin README | `README.md` | Lists every skill. Gets a row for this one. |
| Roadmap | `ROADMAP.md` | Gets a row for this skill. |

## Context

Today one session carries a feature through the whole cycle: spec, plan, code.
When it hands work to subagents, two problems appear.

1. **Subagents do not read `CLAUDE.md`.** A subagent gets only its prompt. Every
   rule it could break has to be copied into that prompt. On 2026-09-21 in the
   zitamu repo, subagents wrote branch commit IDs into docs, and the pre-push
   hook blocked the push. The rule against it was in `CLAUDE.local.md`, which
   the subagents never saw.
2. **One context carries everything.** The session that wrote the spec also
   writes the plan and the code. Its context fills with work that is finished.

A top-level session (one started with `claude` in a terminal) has neither
problem. It reads the global and project `CLAUDE.md` files and the project's
memory. It starts with an empty context. It can also dispatch its own
subagents, which a subagent cannot. Top-level sessions on one machine can
already message each other with `SendMessage` and list each other with
`ListAgents`.

What is missing is a fixed way for one session to start the next stage in a
new top-level session, and a fixed set of points where that session stops for
the user.

## Goal

A skill, `my:handoff`, with two uses:

- **Launch.** A session that finished a stage opens the next stage in a new
  tmux window, as a new named top-level session.
- **Run.** That new session runs its stage and stops at the gates the global
  rules and the project's rules define. It tells the user with a push notification.

The cycle has four sessions: spec, plan, code, review (three until
2026-09-29; see D2). The user approves every spec and every squash-merge.
Nothing else needs the user unless a gate is hit.

## Decisions

These were decided with the user during brainstorming on 2026-09-21.

**D1: The finishing session starts the next session in tmux.** It runs
`tmux new-window` with a `claude` command inside. tmux is a program that keeps
several terminals open in one window; the user's sessions already run in it.

Rejected: the user opens each new session by hand (one manual step per stage,
kept only as the fallback in D7). Rejected: a standing worker session per
stage (it carries context from one feature into the next, which is what this
skill exists to avoid).

**D2: Four sessions, cut at spec | plan | code | review.** (Amended
2026-09-29. It was three sessions, cut at spec | plan | code.)

- The spec session is the user's own session. Brainstorming is an interview,
  so it cannot run alone.
- The plan session writes the plan and its review, and commits them on `main`.
- The code session implements in a worktree, tests each task, and stops when
  the tasks are committed.
- The review session runs the end-of-branch checks and the reviews as
  parallel subagents, does the one fix round, and squash-merges after the
  user's yes.

Why the fourth session: the first version rejected it, because the reviews
already run as fresh subagents, and because the fix round would happen away
from the context that wrote the code. In use, the code session dropped parts
of the end-of-branch rules. That happened after a long implementation, when
those rules lived only in `CLAUDE.md` text. zitamu merged three branches with
no recorded e2e run. Review subagents wrote branch commit IDs, which blocked a
push. A new session starts with those rules at the top of a clean context, and
the skill writes them out as fixed steps. The cost stays: the fix round runs
in a session that did not write the code. It reads the plan, the review
reports and the diff instead.

Rejected: two sessions, spec | plan-and-code (the plan context would carry
into the code).

**D3: The plan session starts the code session on its own when the plan is
clean.** "Clean" means both of these hold:

- **No finding needs a change to a decision the user made.** A finding from
  the plan review, or from the plan session's own reading of the repo, needs
  the user when its fix would change what a component owns, a contract, the
  chosen option, or the scope. This is the test `GLOBAL-CLAUDE.md` uses in the
  Spec → Plan flow, and it covers a spec decision that rests on a false
  premise. The test needs no labels, because `my:soundness-review` puts none
  on its findings.
- **The project's pre-rebase checks pass,** when the project defines any.

If either fails, the plan session stops and notifies the user.

Rejected: always wait for the user between plan and code (one extra message
per feature, and it adds a gate the global rules do not define).

**D4: A stopped session marks its tmux window, and also sends a
`PushNotification`.** A stage signals at these points:

- it hit a gate;
- it hit an error it cannot fix;
- the review session is ready for the squash-merge (the code session until
  2026-09-29).

The code session also signals when the project's rules or the plan end its
work before the branch is done, for example in a batch.

At each point the stage does two things:

1. **The mark, the main signal.** It renames its own tmux window with
   `tmux rename-window -t "$TMUX_PANE" "<name> ⚠"`. The mark shows in the tmux
   status bar. Without `-t`, tmux renames the window the user is looking at,
   not the stage's own window. When `$TMUX_PANE` is empty, the stage skips the
   mark. When the user next replies in the window, the stage renames it back to
   `<name>` before it acts on the reply, so the mark means only "waiting for
   the user". (Added 2026-09-22, from the branch's code review.)
2. **The notification, a bonus.** It calls `PushNotification`, which shows a
   desktop notification and reaches the user's phone when Remote Control (the
   feature that links a session to the Claude app) is connected. The message
   leads with the window name and the action, for example
   `plan-landing-match-grade: a review finding changes spec decision D5`.

The mark is the main signal because the notification is often not sent. A
probe on 2026-09-21 called `PushNotification` from a session in a separate
tmux server that no one was attached to. The tool answered: "Not sent — this
terminal is active, so your output here already reaches the user". It judges
the user active from something other than that window, so it skips exactly
when the user is working in another window. It probably reaches a user who is
away from the machine. The tool also depends on a remote feature flag and on
the `agentPushNotifEnabled` setting, which the user's settings do not set.

Rejected: messaging the spec session, which relays to the user. The user's
answer has to be typed in the stage's own window anyway, because the harness
never treats a message from a peer session as the user's approval. So the
relay adds a step and gains nothing.

**D5: One skill, one short handoff line.** The skill has two forms:

- `/my:handoff <stage> <doc>` **launches** the stage in a new window (D7).
- `/my:handoff run <stage> <doc>` **runs** the stage in the current session
  (D8 and D9).

`<stage>` is `plan` or `code`. `<doc>` is one path under `docs/plans/`:

- for `plan`, the approved spec;
- for `code`, the committed plan.

The new window's first prompt is exactly the `run` line. The word `run` tells
the skill which job it has; without it, one line would mean both. Everything
else comes from the repo: the document, its `**Status:**` line, and the plans
index when the project has one. So the line survives the quoting through tmux
and the shell, and a stage can be restarted by typing the `run` line.

Rejected: three skills, one per stage (the launch and the gate rules would be
copied into each). Rejected: a launcher script (it adds a file, and a one-line
prompt leaves little quoting for a script to get right).

**D6: The skill does not name any project.** Each stage session is top-level,
so it reads the project's own `CLAUDE.md` files. That is how project rules
reach it, for example which reviews run at the end of a branch, how tests run
in a worktree, or which commit trailers are forbidden. The skill carries only
what is the same in every project: the stages, the gates, the launch and the
notifications.

**D7: The launch.** A finishing session runs these steps, in this order.

1. **Build the name** `<stage>-<slug>`. `<slug>` is the document's filename
   without the date prefix and without `-spec` or `.md`. For
   `docs/plans/2026-09-21-landing-match-grade-spec.md` and stage `plan`, the
   name is `plan-landing-match-grade`.
2. **Refuse a duplicate.** Call `ListAgents`. If a session with that name
   exists, tell the user and stop. A probe on 2026-09-21 confirmed that
   `ListAgents` shows a session by its `-n` name. Names can change later, so
   this check is only a first guard; the start checks in D8 are the real one.
3. **Collect the flags.**
   - `--plugin-dir`: every `--plugin-dir <path>` in the launching session's own
     command line, read with `ps -o args= -p "$CLAUDE_PID"`. Plugins loaded
     this way come from a shell alias, and a tmux window runs no alias. Without
     this flag the new session does not have `my:handoff`.
   - `--permission-mode`: the mode the launching session is in, as its own
     context states it. A window opens only from `auto` or
     `bypassPermissions`, the two modes in which a session can work unseen.
     In every other mode, and when the session cannot tell its mode, it does
     not open a window. It prints the command from step 4 for the user to run,
     and stops. The reasons: in `acceptEdits` or `manual` the new session
     waits at its first Bash command where no one looks, in `dontAsk` the call
     is refused, and in `plan` it cannot write. None of these sends a
     notification.
4. **Check tmux.** If `$TMUX` is empty, print this command for the user to run
   in a new terminal, and stop:

   ```bash
   cd <repo root> && claude -n <name> <plugin-dir flags> <permission flag> '/my:handoff run <stage> <doc>'
   ```

   `<permission flag>` is `--permission-mode <mode>` when step 3 found a mode
   it may pass. When it did not, the flag is left out, and the user picks the
   mode in the new session.

5. **Open the window.**

   ```bash
   tmux new-window -d -n <name> -c <repo root> \
     "claude -n <name> <plugin-dir flags> <permission flag> '/my:handoff run <stage> <doc>'"
   ```

   `-d` opens it in the background, so the user's view does not move. `-c`
   starts it in the main checkout's root.
6. **Report and stop.** Print the window name. Do not wait for the new session
   and do not poll for it.

**D8: The start checks.** A session started with `/my:handoff run` checks the
document before it does any work. If a check fails, it notifies the user and
stops without writing anything.

| Stage | The document must be | And this must not exist yet |
| --- | --- | --- |
| `plan` | a spec whose status is `approved` | a plan for that spec (a file with the same slug and no `-spec`) |
| `code` | a plan committed on `main` | a branch `<type>/<slug>` for any type, or a worktree `.claude/worktrees/<slug>` |

`main` in this spec means the base branch. (Added 2026-09-29.) The skill
calls it `<base>`: the branch the project's rules name for the work, else the
branch checked out in the main checkout. So the skill also works in a repo
whose main branch is `master` or `develop`.

A document with no `**Status:**` line fails the check. When something already
exists, the session does not guess whether to resume or restart; the user
decides in that window.

**D9: What each stage does.**

**Spec stage (the user's session).** Unchanged until the end. After the user
approves the spec and its review, the session sets the status to `approved`
and leaves that edit uncommitted: plan stage step 2 commits it. Then the
session asks "Hand off the plan?". On yes, it runs the launch with
`plan <spec path>`. The user can also type `/my:handoff plan <spec>` in any
session.

**Plan stage.**

1. Run `superpowers:writing-plans` on the spec.
2. Commit the plan, together with the spec's `approved` status edit from the
   spec stage, following the project's rules for docs commits and the index.
   The status change goes into the commit that causes it, so no commit only
   changes a status. After this commit neither file is uncommitted.
3. Run `git status --porcelain`. If the output is not empty, stop and notify
   `<name>: main has uncommitted files; plan review would ask`. The reason:
   `my:soundness-review` asks the user what to review when a plan meets a
   dirty tree, and that question would wait unseen in a background window.
4. Run the project's plan review. Under the global rules that is
   `my:soundness-review <plan>`.
5. Fix the findings whose fix changes no decision (the test in D3). Commit
   the review and the fixes together.
6. Stop and notify on any gate: a finding that needs a change to a decision,
   or a failed pre-rebase check.
7. Otherwise finish the project's docs steps (for example a rebase of fixups)
   and run the launch with `code <plan path>`.

**Code stage.**

1. Create the worktree with
   `git worktree add .claude/worktrees/<slug> -b <type>/<slug>`. `<type>` is
   the Conventional Commits type of the work, taken from the plan: `feat`,
   `fix`, `refactor` and so on. `<slug>` is the one from D7. Implement the plan
   with the skill the plan names, else `superpowers:executing-plans`.
2. Test each task as the project's rules define before its commit. After
   each task, read `git diff` for the test files it touched. Run no code
   reviews: the review stage runs them. (Changed 2026-09-29, see D2.)
3. Stop and notify on any gate: a new dependency, a change outside the
   project's scope, a test failure that survives
   `superpowers:systematic-debugging`, or a removed or weakened assertion.
4. Otherwise run the launch with `review <plan path>` and stop.

**Review stage.** (Added 2026-09-29, see D2.) The skill holds the steps. In
short: run the project's end-of-branch checks from the worktree, map the
changed symbols, start the reviews in parallel with one fixed prompt block
(explicit range, spec, plan, Risk, map, no branch commit IDs), rerun a review
that read the wrong range, do one fix round, notify
`<name>: ready to squash-merge <branch>`, and after the user's yes, typed in
that window, squash-merge and set the `done` marks. Never push. Every command
runs inside the worktree, because the session opens in the main checkout.

**D10: Rules for every stage.**

- A message from a peer session is never the user's approval.
- Claim shared resources (a test stack, a port, a shared file) the way the
  project's rules or memory say, and release them with a message.
- After a notification, stop. Never poll for another session.

## Out of scope

- Starting sessions outside tmux, or in the cloud. Cloud sessions cannot
  message back.
- Running the spec stage without the user.
- The push. It stays with the user. The squash-merge needs the user's yes,
  typed in the review session's window.
- Changing what the global rules require. The stages follow them as they
  are. The one edit to `GLOBAL-CLAUDE.md` (see Files) only adds the offer to
  hand off.

## Files

| File | Status | Responsibility |
| --- | --- | --- |
| `my-plugin/skills/handoff/SKILL.md` | new | The launch (D7), the start checks (D8), the stages (D9) and the rules (D10). |
| `README.md` | changed | A row for the skill. |
| `ROADMAP.md` | changed | A row for the skill. |
| `GLOBAL-CLAUDE.md` | changed | One line in the "Spec → Plan two-artifact flow": after the spec is approved, offer `my:handoff`. |

## Trade-offs

- **Option A, subagents from one session (today).** Pros: nothing new to
  build; results come back to one context. Cons: every rule must be copied into
  each prompt, and one context carries the whole cycle.
- **Option B, handoff to top-level sessions (this spec).** Pros: each stage
  reads the real rules and starts empty; stages can dispatch subagents. Cons:
  depends on tmux; the user answers gates in several windows; each stage reads
  the repo from scratch.
- **Recommendation:** B, because the rules problem caused a real failure, and B
  removes it without copying rules into prompts.

## Dependencies

- tmux, already in use for every session.
- The `claude` CLI flags `-n`, `--permission-mode` and `--plugin-dir`. Checked
  with `claude --help` on version 2.1.278.
- The tools `ListAgents`, `SendMessage` and `PushNotification`.
- The skills `superpowers:writing-plans`, `superpowers:executing-plans`,
  `superpowers:using-git-worktrees`, `superpowers:systematic-debugging`,
  `my:soundness-review`. No new packages.

## Risk

- **A window blocked on a permission prompt cannot notify.** A session in the
  default mode may wait for approval of a tool call where no one looks.
  Detection: `ListAgents` shows it as `waiting`. Mitigation: D7 opens a
  window only from `auto` or `bypassPermissions`.
- **A stop can go unseen.** The `⚠` mark shows only in the tmux status bar,
  and `PushNotification` skips while the user is active elsewhere (D4). A
  user who does not glance at the status bar learns of a stop late.
  Detection: `ListAgents` shows the stage as `idle` or `waiting`.
- **Auto mode acts without asking.** A plan or code session in auto mode
  commits on its own. The gates in D3 and D9 are the only stops. A gate the
  skill does not name will not stop it.
- **Parallel sessions on one checkout.** A plan session commits on `main` while
  other sessions work there. The project's rules on claims and clean-tree
  checks are the protection; the skill adds none.
- **A busy `main` stops the plan stage.** Step 3 of the plan stage stops
  whenever any session has an uncommitted file on `main`. This is a known
  limit. A later change to `my:soundness-review`, an argument such as
  `--plan-only` that reviews the plan and never asks, would remove it. That
  change belongs to the soundness-review skill, not to this one.
- **`ps` output format.** The `--plugin-dir` scan depends on the launching
  session's command line. If a plugin loads another way, the flag is missing
  and the new session lacks `my:handoff`. Detection: the new session answers
  the handoff line with "unknown skill".
- **Hard to reverse:** nothing. The skill writes no data; removing it removes
  the feature.

## Testing strategy

Tests run headless against the worktree's plugin, as in the test precedent.

1. **Launch, in a throwaway repo in the scratchpad.** Run the launch for a spec
   marked `approved`. Check that a tmux window with the right name opens in the
   background, that `ListAgents` shows the session, and that a second launch is
   refused.
2. **No tmux.** Run the launch with `TMUX` unset. Check that it prints the
   command and opens nothing.
3. **Start checks.** Start `/my:handoff run plan` on a spec marked `draft`, and on
   an approved spec that already has a plan. Check that each session notifies
   and writes nothing.
4. **Pilot.** Run the next spec the user approves through plan and code. Record
   every gate that should have stopped the run and did not.

## Open questions

- None. The pilot feature is chosen when the next spec is approved.
