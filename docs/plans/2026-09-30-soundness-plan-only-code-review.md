# Code review: soundness-review --plan-only

**Status:** review of `feat/soundness-plan-only`, 2026-09-30. Bug-finder pass on
the branch; findings below. The fix round fixed or moved each one; see the `-code-review-2.md` re-review. Shipped in 7740bf7.

## Scope

- **Range:** `main..feat/soundness-plan-only`: three commits (the
  `--plan-only` argument, the handoff plan-stage rewrite, the docs mentions),
  eight files.
- **Passes:** the built-in `/code-review` at level `high`, without `--fix`. It
  read `git diff main...HEAD` from the worktree, whose HEAD is the branch
  head. `main` is an ancestor of the branch, so this is the same diff as the
  requested range. A manual review of `git diff main..feat/soundness-plan-only`
  ran alongside it. Each finding says which pass found it.
- **Checked against:** the spec `docs/plans/2026-09-30-soundness-plan-only-spec.md`
  and the plan `docs/plans/2026-09-30-soundness-plan-only.md`. Known limits in
  their **Risk** sections are not findings. Examples: grounding reads other
  sessions' edits, and a rerun after a gate stop fails the start check.
- **Confirmed sound (manual pass):** the `--plan-only` flow matches spec D1 to
  D3. `git add -- <paths>` then `git commit -- <paths>` commits only those
  paths, new files included, and leaves other sessions' staged files staged.
  The review stage's reference now points to Plan stage step 4, which holds
  the finding test. The linter reports no new errors in the handoff files.

No Critical or High findings.

## Findings

### 1. Deferred fold rewrites the squash commit that the `done` marks cite (Medium)

`plugins/my/skills/handoff/SKILL.md:191-198` (step 8). Found by: `/code-review`.

On a busy `main`, step 8 leaves the spec's fixups to be folded after the code
branch is merged. By then the review stage has squash-merged the branch and
written the `done` marks, which cite the squash commit. Folding then runs
`git rebase -i --autosquash <spec commit>^`. That gives new hashes to every
later commit, the squash commit and the `done` commit among them. The `done`
marks now cite a hash that is not on `main`. This breaks "Cite only commits
on `main`", and zitamu's pre-push hook refuses the push. The spec's Trade-offs
("Deferred fold") names the `fixup!` push refusal but not this.

### 2. No step owns the deferred fold (Low)

`plugins/my/skills/handoff/SKILL.md:199-203` (step 9). Found by: `/code-review`.

The only record of unfolded fixups is one line printed in the plan-stage
window, right before Finish tells the user to close that window. The review
stage's merge step does not fold them. After the window is closed, nothing
names the fixups until a push is refused.

### 3. No step tells the plan stage to add the plans-index row (Low)

`plugins/my/skills/handoff/SKILL.md:185-190` (step 7), compared with
`SKILL.md:162-164` on `main` (old step 3). Found by: both passes.

Old step 3 said to commit "following the project's rules for docs commits
**and the plans index**". New step 7 drops "and the plans index". Step 6
(`SKILL.md:176-177`) still counts the index among the stage's paths, but no
step says to write its row. In a project with an index, the row is never
added, or step 9's "other docs steps" adds it as a second commit, which
breaks "commits once". The spec's D4 drops the same words, so this is a gap
in the spec too.

### 4. The post-commit path check fails on a correct commit (Low)

`plugins/my/skills/handoff/SKILL.md:189-190`. Found by: both passes.

"Check that `git show --stat --format= HEAD` lists exactly these paths." When
one path had no change (most often the plans index, see finding 3), the
commit holds three files and the list names four, so the check fails. The
text also does not say what to do on a failure: signal, stop or continue.

### 5. The fixup test does not match what a fixup subject holds (Low)

`plugins/my/skills/handoff/SKILL.md:191-193`. Found by: both passes.

"A commit whose subject starts with `fixup!` and names the spec's commit."
`git commit --fixup <hash>` writes `fixup! <target's subject>`, not the hash.
A session that looks for the hash finds no fixups, skips the fold on a clean
`main`, and leaves `fixup!` commits in place. The test also scans all of
`git log <base>`, not just the commits since the spec commit.

### 6. The gate signal can name a review that does not exist, and can miss an earlier one (Low)

`plugins/my/skills/handoff/SKILL.md:172-175` (step 5). Found by: `/code-review`.

A false-premise gate can fire in step 1, before step 3 writes a review, so
the signal names a missing file. After a gate is resolved and the review
runs again, the second review is `-plan-review-2.md`. Steps 6 and 7 commit
only the last printed path, so the first review stays untracked on `main`.

### 7. No path for a review that writes no file (Low)

`plugins/my/skills/handoff/SKILL.md:163-168` (step 3). Found by: `/code-review`.

Step 3 takes the review path only from the `Review written to …` line. When
the reviewer's file write fails, soundness-review step 4 prints no such line.
The plan stage has no gate for this, so step 7's `git add -- <missing path>`
fails, or the plan is committed without its review.

### 8. "The working tree is never read" contradicts the spec's Risk (Low)

`plugins/my/skills/soundness-review/SKILL.md:117`. Found by: `/code-review`.

"The working tree is never read, so a dirty tree changes nothing." In
plan-review mode the reviewer grounds the plan by reading the live working
tree, including other sessions' uncommitted files. The spec's Risk section
says so ("Grounding reads other sessions' edits"). The behavior is a known
limit. The sentence is wrong, and a reader will trust it. Suggested wording:
"The diff is never captured, so a dirty tree does not trigger the question."

### 9. `--plan-only` messages are copied in several places (Low, cleanup)

`plugins/my/skills/soundness-review/SKILL.md:50-53`, `117`, `122-123`. Found
by: `/code-review`.

The spec-stop message appears in the step 0 table and the step 1a table. The
description-ignored note appears in step 0, the step 1a paragraph and the
step 1a `plan-review` row. An edit to one copy leaves the others behind, and
the headless tests match exact messages, so they would break. This is not a
bug today.
