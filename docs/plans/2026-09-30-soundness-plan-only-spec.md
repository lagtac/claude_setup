# Spec: `--plan-only` for `my:soundness-review`, and a plan stage that works on a busy `main`

**Status:** draft, 2026-09-30. Waiting for the user's approval.

## How to read this spec

| Document | Path | Why you would read it |
| --- | --- | --- |
| **This spec** | `docs/plans/2026-09-30-soundness-plan-only-spec.md` | What to build, why, and the trade-offs. Start here. |
| Spec review | `docs/plans/2026-09-30-soundness-plan-only-spec-review.md` | The `my:spec-review` report on this spec. Written after this spec. |
| Implementation plan | `docs/plans/2026-09-30-soundness-plan-only.md` | Written after this spec is approved. |
| Soundness-review skill | `plugins/my/skills/soundness-review/SKILL.md` | Step 0 (argument classes), step 1 (diff capture) and step 1a (mode table and the question). D1 to D3 change these. |
| Handoff skill | `plugins/my/skills/handoff/SKILL.md` | "Plan stage", steps 1 to 8. D4 rewrites them. |
| Handoff README | `plugins/my/skills/handoff/README.md` | "Plan stage" lists the same steps for the user. |
| Handoff spec | `docs/plans/2026-09-21-handoff-spec.md` | Decision D9 ("Plan stage") and the Risk item "A busy `main` stops the plan stage". D5 amends both. |
| Global instructions | `global/CLAUDE.md` | "Code Review Routing" describes the `my:soundness-review` arguments. "Git Workflow" steps 5 to 9 say the plan and its review go into one commit. |
| Plugin README | `README.md` | Lists every skill, including `my:soundness-review`. |
| Roadmap | `ROADMAP.md` | "Design workflow" holds the 💭 follow-up this spec answers. |
| Test precedent | `docs/plans/2026-09-16-spec-review-skill.md` | "How tests run": headless `claude -p --plugin-dir` runs against a plugin in a worktree. |

## Context

The `my:handoff` plan stage runs in a background tmux window on the main
checkout. Other sessions often work in the same checkout at the same time. So
the checkout often has uncommitted files that belong to other sessions.

Today the plan stage stops whenever the checkout has any uncommitted file
(`plugins/my/skills/handoff/SKILL.md`, plan stage step 4). It stops for this
reason. `my:soundness-review <plan>` on a dirty tree asks the user "review the
plan, or review the changes against the plan?". In a background window, nobody
sees that question, so the session would wait for ever. The handoff spec lists
this as a known limit and names the fix: an argument such as `--plan-only`
(handoff spec, Risk, "A busy `main` stops the plan stage").

The argument alone is not enough. The plan stage commits the plan first
(step 3) and the review later (step 6). The global Git Workflow puts the plan
and its review in one commit, so the second commit becomes a fixup that a
`git rebase` folds in. A rebase refuses to run while other files are
uncommitted. So with the argument alone, a busy `main` still stops the stage,
only at a later step.

## Goal

A plan stage started while other sessions have uncommitted files on `main`
finishes without stopping. It leaves one commit on `main`, and that commit
holds only the plan stage's own files. When the spec has `fixup!` commits
waiting and `main` is busy, the stage still finishes: it leaves the fixups
for later and says so (D4 step 8).

## Out of scope

- Reviewing a plan against the last commit instead of the working tree. See
  Risk, "Grounding reads other sessions' edits".
- Any change in how the code and review stages of `my:handoff` behave. The
  review stage's text changes in one place only: its reference to the finding
  test moves from "Plan stage, step 6" to "Plan stage, step 4" (D5).
- Any change to how `my:soundness-review` behaves without `--plan-only`.

## Decisions

**D1: An explicit `--plan-only` token.** Step 0 of `my:soundness-review` gets
one new token class, matched before all other rows:

| Token shape | Variable |
| --- | --- |
| The exact token `--plan-only` | `PLAN_ONLY` is set |

With `PLAN_ONLY` set, the skill reviews the plan document. It never asks what
to review.

- Rejected: change the default, so a plan path without a range always means a
  plan review, and add `--diff` for the old behavior. This changes what an
  existing call does. A user who types `my:soundness-review <plan>` on a dirty
  tree today is asked. After the change, they would get a plan review without
  a word. `global/CLAUDE.md` documents the question, so the change would break
  a documented habit to fix one caller.

**D2: `--plan-only` skips the diff capture.** When `PLAN_ONLY` is set, step 1
(capture the diff) runs only its first block, which creates `WORK_DIR`. The
plan-review copy (`cp "$PLAN_PATH" "$WORK_DIR/plan.md"`) needs that
directory. The diff commands, the untracked-file list and the payload file do
not run. Step 1a goes straight to the `plan-review` row. The skill never looks at the working
tree's changes, so it cannot see that the tree is dirty.

**D3: Mixed arguments.** These checks run at the end of step 0, in this order.
The first match wins:

| Arguments | Result |
| --- | --- |
| `--plan-only` and a `RANGE` | Stop: `--plan-only reviews a plan; it takes no range. Drop one of them.` |
| `--plan-only` and no `PLAN_PATH` | Stop: `--plan-only needs a plan under docs/plans/.` |
| `--plan-only` and a `PLAN_PATH` that ends in `-spec.md` | Stop: `This is a spec. Run my:spec-review <PLAN_PATH> instead.` This is the existing message. |
| `--plan-only`, a `PLAN_PATH` and a `DESCRIPTION` | Review the plan. Print the existing note `(description ignored: a plan review has no diff to check it against)`. |
| `--plan-only` twice | Same as once. |

A stop dispatches nothing and writes no file.

**D4: The handoff plan stage reviews before it commits, and commits once.**
The plan stage in `plugins/my/skills/handoff/SKILL.md` becomes:

1. Run `superpowers:writing-plans` on the spec. Unchanged. That skill does not
   commit the plan.
2. Name one execution skill in the plan's header. Unchanged.
3. Run the project's plan review. Under the global rules that is
   `my:soundness-review --plan-only <plan path>`. It reads the uncommitted
   plan file.
4. For each finding, fix it or treat it as a gate. Unchanged test: would the
   fix change what a component owns, a contract, the chosen option, or the
   scope? If no, fix it. If yes, it is a gate.
5. Signal and stop on any gate. The gates are: a finding whose fix would
   change a decision, and a spec decision that turns out to rest on a false
   premise. The signal names the files left uncommitted on `main`: the plan,
   the review and the spec.
6. Check that the stage's files hold only its own changes. Run
   `git diff HEAD -- <paths>`. The paths are the plan, the review, the spec
   (with its `approved` status edit) and the project's plans index when the
   project has one. If a hunk is not this stage's own change, for example
   another session's row in the plans index, signal
   `<name>: <file> holds another session's edit` and stop.
7. Commit these paths, and only these, in one commit:
   `git add -- <paths>`, then `git commit -- <paths>`. The `-- <paths>` on
   `git commit` commits only those paths, even when another session has
   staged files of its own.
8. Fold waiting fixups only when `main` is clean. If the spec has `fixup!`
   commits waiting and `git status --porcelain` prints nothing, run the
   project's pre-rebase check, then the fold. A failed pre-rebase check is a
   gate: signal and stop. If `git status --porcelain` prints anything, skip
   the fold. Name the waiting fixups in the "Finish" message. They are folded
   later, after the code branch is merged, as the global rule "Before every
   rebase" already says.
9. Finish the project's other docs steps, then run "Launch" with
   `code <plan path>`, then "Finish".

Removed: the old step 3 ("commit the plan") and the old step 4 ("stop when
`git status --porcelain` prints anything"). The plan and its review are never
in separate commits, so the stage makes no fixup of its own.

- Rejected: fold the fixups with `git rebase --autostash` on a busy `main`.
  It would stash other sessions' uncommitted files during the rebase, while
  those sessions may still be editing them.
- Rejected: add the argument and keep the commit order. The review commit then
  becomes a fixup of the plan commit, and the rebase that folds it needs a
  clean checkout. A busy `main` would still stop the stage, at step 8 instead
  of step 4.

**D5: The handoff spec is amended, not rewritten.** In
`docs/plans/2026-09-21-handoff-spec.md`, decision D9 "Plan stage" gets the
steps from D4, marked `(Changed 2026-09-30, see the soundness plan-only spec.)`.
This is the same style as the 2026-09-29 changes to D2. The spec stage's
"plan stage step 2 commits it" becomes "plan stage step 7 commits it". The
Risk item "A busy `main` stops the plan stage" is removed. Its status line
stays `done`.

In `plugins/my/skills/handoff/SKILL.md`, review stage step 6, "apply the test
in Plan stage, step 6" becomes "apply the test in Plan stage, step 4".

**D6: Documents that name the arguments are updated.**

- `plugins/my/skills/soundness-review/SKILL.md`: the `description`
  frontmatter gets the clause "`--plan-only` reviews the plan and never asks".
- `README.md`: the `my:soundness-review` entry names `--plan-only`.
- `plugins/my/skills/handoff/README.md`: "Plan stage" lists the new steps.
- `global/CLAUDE.md`, "Code Review Routing": the `my:soundness-review` line
  adds "`--plan-only <plan>` reviews the plan on any tree and never asks".
- `ROADMAP.md`: the 💭 follow-up under `my:handoff` becomes a shipped note
  with its commit.

## Trade-offs

- **Explicit token against a changed default (D1).** The token costs one more
  thing to learn. It keeps every existing call unchanged, and the one caller
  that needs it states what it wants.
- **Review before commit (D4).** The plan stays uncommitted while the review
  runs. If the session dies there, the plan exists only in the working tree.
  In return the stage makes one commit and no fixup of its own, which
  matches the global Git Workflow steps 5 to 7 exactly.
- **Deferred fold (D4 step 8).** On a busy `main`, the spec's waiting fixups
  stay unfolded until after the code branch is merged. A push in that time
  carries `fixup!` commits, which zitamu's pre-push hook refuses. In return a
  busy `main` never stops the stage.

## Dependencies

None. No new packages. Both changed skills are prompt files. The change needs
`git commit -- <paths>`, which every git version supports.

## Risk

- **Grounding reads other sessions' edits.** A plan review checks that the
  files and names in the plan exist. It reads the working tree. Another
  session's uncommitted edit can make a check pass that fails on the last
  commit, or the reverse. This is a known limit. A fix would read files with
  `git show HEAD:<path>`, and it is out of scope.
- **Uncommitted plan after a gate stop.** After a gate, the plan, the review
  and the spec edit sit uncommitted on `main`. Another session that runs
  `git add -A` would sweep them into its own commit. The global rule "read
  `git diff --cached` before every commit" is the protection. The gate signal
  names the files, so the user knows they are there.
- **A rerun after a gate stop fails its start check.** The start check says no
  plan may exist yet. After a gate stop, an uncommitted plan does exist. So a
  rerun stops and the user decides. This is the existing rule ("the user
  decides") and is intended.
- **A shared file with another session's edit.** `git commit -- <paths>`
  commits the whole current content of each named file. A plans index can
  hold another session's uncommitted row. D4 step 6 catches this and stops,
  so the user decides. The check reads hunks, so it cannot tell two edits
  apart inside one hunk; the user's reread of the commit is the last
  protection.
- **Blast radius.** `grep -rln "soundness-review" --include=*.md` outside
  `docs/` finds 11 files. Two of them call the skill:
  `global/CLAUDE.md` (the routing lines, and the end-of-branch reviews, which
  pass a range and are unchanged) and `plugins/my/skills/handoff/SKILL.md`
  (plan stage, changed; review stage, passes a range, unchanged). Three
  document it and change under D6: `README.md`, `ROADMAP.md`,
  `plugins/my/skills/handoff/README.md`. The skill's `SKILL.md` changes
  under D1 to D3. Its `code-reviewer-prompt.md` needs no change: a
  `--plan-only` review is an ordinary `plan-review` by the time the prompt
  is built. The other four only name it:
  `plugins/my/agents/code-reviewer.md`,
  `plugins/my/skills/spec-review/SKILL.md`,
  `plugins/my/skills/spec-review/spec-reviewer-prompt.md` and
  `plugins/my/skills/architect/SKILL.md`. They need no change. No caller
  changes behavior unless it adds the token.
- **Hard to reverse:** nothing. Both changes are prompt text.

## Testing

Both skills are prompt files, so there are no unit tests. Tests are headless
runs, as in the test precedent:
`claude -p --plugin-dir <worktree>/plugins/my` in a small scratch git
repository that holds one plan under `docs/plans/`.

1. **Dirty tree, `--plan-only`.** Add an uncommitted file. Run
   `my:soundness-review --plan-only docs/plans/<plan>.md`. Expected: a file
   `docs/plans/<plan>-plan-review.md` exists, and the run made no
   `AskUserQuestion` call. Red first: without the change, the run asks, or
   (headless, no `AskUserQuestion`) prints the "Working tree is dirty" note and
   reviews the diff.
2. **Mixed arguments.** One run per stop row in D3. Expected: the exact stop
   message, and no new file under `docs/plans/`.
3. **No token, dirty tree.** Run without `--plan-only`. Expected: the existing
   behavior (the question, or the headless fallback note). This proves D1
   changed nothing else.

The handoff plan stage is not run end to end. A full run needs tmux and a
second session, which is too heavy for this change. The first real use is the
test, and the risk above says how a failure shows.
