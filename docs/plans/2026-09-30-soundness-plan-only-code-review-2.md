# Code review 2: soundness-review --plan-only

**Status:** re-review of `feat/soundness-plan-only` after the fix round,
2026-09-30. Final under the one-fix-round rule. No Critical findings: one
Medium (finding 3), seven Low.

## Scope

- **Range:** `main..feat/soundness-plan-only`, read with
  `git diff main..feat/soundness-plan-only` from the worktree. Five commits:
  the `--plan-only` argument, the handoff plan-stage rewrite, the docs
  mentions, and the two fix commits at the branch head (the plan stage's
  index row, commit check and fixup test; the review stage's new step 8 that
  folds deferred fixups before the `done` marks). `origin/main` was not used.
- **Passes:** a manual review of the whole range, with most weight on the two
  fix commits, and the built-in `/code-review` at level `high` (launched on
  the same range, without `--fix`; see "Built-in pass" below). Each finding
  says which pass found it.
- **Checked against:** the spec `docs/plans/2026-09-30-soundness-plan-only-spec.md`,
  the plan `docs/plans/2026-09-30-soundness-plan-only.md` and its **Risk**
  section, the map of changed symbols, and the first report
  `docs/plans/2026-09-30-soundness-plan-only-code-review.md`.

## Earlier findings

| # | Finding | Now |
|---|---|---|
| 1 | Deferred fold rewrites the squash commit the `done` marks cite | Fixed: review stage step 8 folds (8.3) before the `done` marks (8.4), which cite the post-fold hash |
| 2 | No step owns the deferred fold | Fixed: review stage step 8.3; plan stage step 9 message and README step 7 point to it |
| 3 | No step adds the plans-index row | Fixed: plan stage step 6, README step 5, handoff spec D9 step 6, spec D4 step 6 |
| 4 | Post-commit path check fails on a correct commit; no failure action | Fixed: "lists only these paths", unchanged paths are allowed, a foreign path signals and stops |
| 5 | Fixup test looks for the hash, and scans all of `git log` | Fixed: subject match `fixup! <spec subject>` over `<spec commit>..<base>`, with the spec commit found by `--diff-filter=A` |
| 6 | Gate signal names a missing review; an older review stays untracked | First half fixed ("when step 3 wrote one"); second half moved to **Risk** |
| 7 | No path for a review that writes no file | Moved to **Risk** |
| 8 | "The working tree is never read" | Fixed: soundness-review step 1a now says the changes are not captured, and that grounding still reads the tree |
| 9 | Messages copied in several places | Moved to **Risk** |

Checked by hand: `git worktree remove` run from inside the worktree it
removes succeeds, so step 8.2 works even under the stage's
`cd <worktree> && …` rule.

## Findings

### 1. Re-review reports and **Risk** edits are never committed, so step 8.2 fails and the squash misses them (Low)

`plugins/my/skills/handoff/SKILL.md:303-308` (review stage step 6) with
`:312-313` (steps 8.1 and 8.2). Found by: manual pass.

Step 6 commits the first round's reports and **Risk** edits, then runs the
re-reviews. A re-review writes a new report (`-code-review-2.md`, like this
one), and "a lesser one goes into **Risk**" edits the plan. No step commits
either. Step 8.1 squash-merges without them, and step 8.2's
`git worktree remove <worktree>` then refuses:
`fatal: '<worktree>' contains modified or untracked files, use --force to
delete it` (reproduced in a scratch repo). The stage stops between the merge
and the fold, with `<base>` holding a squash commit and no `done` marks. The
gap existed on `main` (the old step 8 also ran the remove last), but the fix
round made the remove a precondition of the fold. Fix: end step 6 with
"commit the re-review reports and any **Risk** edits on the branch".

### 2. Steps 8.3 and 8.4 run after the worktree is gone, but the stage says to run every command in it (Low)

`plugins/my/skills/handoff/SKILL.md:242-245` compared with `:312-323`. Found
by: both passes.

The stage's preamble says "Run every command of this stage as
`cd <worktree> && …`". After step 8.2 removes the worktree, that `cd` fails
for the fold (8.3) and the `done` marks (8.4). Handoff spec D9
(`docs/plans/2026-09-21-handoff-spec.md`, review stage) also still says
"Every command runs inside the worktree". Step 8.3 names "the main
checkout" for `git status --porcelain` only. The squash-merge (8.1) also
must run in the main checkout, which is on `<base>`; that part was already
so on `main`. A session that follows the preamble literally tries
`cd <worktree>` in 8.3 and 8.4, and the command fails. Fix: add to
the preamble "except step 8, which runs in the main checkout".

### 3. The deferred fold rewrites other features' squash commits that their `done` marks cite (Medium)

`plugins/my/skills/handoff/SKILL.md:315-317` (review stage step 8.3), with
plan stage step 8 (`:195-206`). Found by: `/code-review`.

The fold runs `rebase -i --autosquash <spec commit>^`, which gives new
hashes to every later commit on `<base>`, not only this feature's squash
commit. Step 8.3 protects this feature's `done` marks by running first, but
not other features'. Scenario: the plan stage skips the fold on a busy
`main`. During this feature's code stage, feature X is squash-merged and its
`done` commit cites X's squash hash. This review stage then folds, and X's
squash commit gets a new hash. X's `done` mark (and any ROADMAP or CHANGELOG
row citing it) now names a commit not on `main`, which breaks "Cite only
commits on `main`" and trips zitamu's pre-push hook. The pre-rebase check
only looks for worktrees, so it does not catch this. The deferral stretches
the window from minutes to the whole code stage. Not listed in **Risk**; the
spec's "Deferred fold" trade-off names only this feature's squash commit.

### 4. `git show --stat` shortens long paths, so step 7's path check cannot match (Low)

`plugins/my/skills/handoff/SKILL.md:191`. Found by: `/code-review`, confirmed
by hand.

`git show --stat --format= main` on `main` today prints
` .../2026-09-30-soundness-plan-only-plan-review.md`, not the full path.
Every plan review path is that long. A strict session signals
`the plan commit holds .../…` on a correct commit; a lenient one matches
tails and cannot tell a foreign path that ends the same way. Fix:
`git show --name-only --format= <hash>` prints full paths.

### 5. Step 7 checks `HEAD`, which another session may have moved (Low)

`plugins/my/skills/handoff/SKILL.md:191`. Found by: `/code-review`.

The stage exists for a busy `<base>`. If another session commits between the
plan commit and the check, `HEAD` is that commit: the stage signals a
foreign path on a correct run, or checks the wrong commit. Fix: take the hash
from `git commit`'s output, or run `git rev-parse HEAD` in the same command,
and check that hash.

### 6. Step 8.3 gives one gate message for two failures, with no exit (Low)

`plugins/my/skills/handoff/SKILL.md:318-321`. Found by: `/code-review` and
the manual pass.

A dirty main checkout and a failed pre-rebase check (another feature's
worktree sits on a branch that contains the spec commit) both signal
`merged; fixups … wait for a clean <base>`. In the second case the checkout
is already clean, so the message sends the user to the wrong fix, and each
reply rechecks and fails until that other branch merges, possibly days. The
`done` marks cannot be set meanwhile, because marks set first would cite a
hash a later fold rewrites. Fix: name the failed check in the message, and
say what to do when the user chooses not to wait (set the marks now and fold
later, accepting the rewrite, or leave the fixups for the global rule).

### 7. README plan-stage step 6 leaves the plans index out of the commit (Low)

`plugins/my/skills/handoff/README.md:102-103`. Found by: `/code-review`.

"Commits the plan, the review and the spec's `approved` status in one
commit, and nothing else" omits the index row that README step 5 adds and
SKILL step 7 commits. A reader judges a correct run, with the index in the
plan commit, as a rule break. Fix: add "and the plans-index row".

### 8. The fixup search misses `amend!`, `squash!` and nested fixups (Low, Risk candidate)

`plugins/my/skills/handoff/SKILL.md:196-199`. Found by: `/code-review`.

`--autosquash` also folds `amend! <subject>`, `squash! <subject>` and
`fixup! fixup! <subject>`. The subject test finds only
`fixup! <spec subject>`, so such a commit is never folded and stays on
`main` until a push is refused. The global rules create fixups only with
`git commit --fixup <hash>`, so today's flow does not produce these
subjects: under the one-fix-round rule this belongs in **Risk** as a known
limit, not in a fix.

## Observations (not findings)

- Altitude (from `/code-review`): the fold is deferred only because a rebase
  needs a clean main checkout. A fold in a temporary detached worktree, then
  a compare-and-swap `git update-ref` of `<base>`, would run at plan-stage
  step 8 on any tree and remove review-stage step 8.3 and findings 1 and 5.
  The deferral was the user's choice at a gate, so this is an option, not a
  finding.
- The **Risk** bullet for the untracked older review says "the plan stage
  never reaches a second review" because a rerun fails the start check. A
  gate in step 5 is resumed by a reply in the same window, not a rerun, and a
  session that changes the plan there may run step 3 again. The limit itself
  is listed, so this is not a finding; the stated reason is only partly
  right.
- The plan's Task 3 text (`docs/plans/2026-09-30-soundness-plan-only.md:578`,
  `:582`, `:611`) still says the fixups are folded "after the code branch is
  merged" by the user. The plan's constraints note the change, and the plan is
  a record of the task, so this is expected.

## Built-in pass

`/code-review high main..feat/soundness-plan-only` ran as a forked skill on
the requested range, without `--fix`. `git status --porcelain` in the
worktree afterwards shows only this report, so it changed no files. It found
eight items. One matches finding 2 above and is merged there. Six are
findings 3 to 8. The eighth, the altitude option, is under Observations.
