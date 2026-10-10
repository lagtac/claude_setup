# Critique: the development workflow, efficiency

**Status:** current, 2026-10-09. Findings on whether the global rules, Superpowers and the `my:` skills make coding faster; C1, C2 and S1 are fixed; G1 and G2 have a roadmap row; S2 and S3 need no action.

## How to read this

- **Subject:** `global/CLAUDE.md` (4,750 words), `global/rules/docs-layout.md` (1,183 words),
  `global/rules/plan-format.md`, and the `my:` skills that the flow calls: `my:handoff`,
  `my:spec-review`, `my:soundness-review`, `my:architect`, `my:roadmap-management`.
- **Evidence:** the `main` history of this repo and of `zitamu/real-estate-webapp`. Only commits
  after each rule existed count against that rule. The four-commit rule arrived on 2026-09-24.
  The size table arrived on 2026-10-03.
- **Method:** the files were read. Nothing was timed. Claims about model attention are marked as
  hypotheses.

## Short answer

**Mostly efficient, with three kinds of waste.**

What works, and should stay:

- **Sizing (Small, Medium, Large).** It is the main limit on process cost.
- **One review round per branch, run in parallel.** The `my:tutor` and `--plan-only` features
  each had one review and one re-review, as the rule says.
- **The Risk section as the place for edge cases.** It stops the review loop from growing.
- **"The red step is the mutation proof".** It removes a second test step.
- **Specs and plans written on `main`, code in a worktree.** Parallel sessions do not collide.

Post-rule history shows the code flow is fast. `my:tutor` took three commits over two days.
Zitamu's "matching requests" went from architecture brief to `done` on 2026-10-08, in one day.

The waste:

1. Contradictions in `CLAUDE.md` that give a literal model two opposite orders (C1, C2).
2. Git mechanics written as prose that the model must execute step by step (G1, G2).
3. Process steps that ignore size: the UI rule and the volume of documents around the code (S1
   to S3).

## Contradictions

### C1. The trigger table orders a skill that another section forbids

`CLAUDE.md:79` maps "Major work needs review before merge" to `superpowers:requesting-code-review`.
`CLAUDE.md:116` says "Never invoke … `superpowers:requesting-code-review`". The table is introduced
as "explicit triggers, not suggestions". So both lines are orders.

**Fix:** replace the row with `my:soundness-review` plus `/code-review high`, or delete it. The
end-of-branch section already says what runs.

### C2. The trigger table orders a skill that the Git section overrides

`CLAUDE.md:78` maps "ready to integrate" to `superpowers:finishing-a-development-branch`.
`CLAUDE.md:156` and `:214` override that skill. The model must load it, then ignore most of it.

**Fix:** point the row at "Git Workflow, steps 12 and 13", or at `my:handoff review`, which
already does the squash-merge.

### C3. The Superpowers framing is half right

Of the nine Superpowers skills in the table, two are fully replaced (C1, C2). Two more run with
their own reviews switched off (`executing-plans`, `subagent-driven-development`). Brainstorming,
TDD, systematic debugging, writing-plans and worktrees are still the core. So Superpowers is a
sound base. The problem is only that the table still names the replaced skills.

## Git mechanics as prose

### G1. The fixup and rebase steps are a script written in English

Steps 4, 8 and 9, plus the two `git branch --contains` checks, are about 400 words. They are exact
commands with exact checks: name the target by hash, refuse when a worktree holds a branch,
rebase with `-i` and `GIT_SEQUENCE_EDITOR=true`, then confirm no `fixup!` remains and the diff is
empty. Every step is fixed. None needs judgment.

- **Option A: a script**, for example `git-fold-docs`, that runs the checks and the rebase and
  exits non-zero with a reason. Pros: the same result every time, and fewer words in every
  session. Cons: one more file to maintain and test.
- **Option B: keep the prose.** Pros: nothing new. Cons: the model re-derives a fixed procedure
  each time, and one missed check rewrites hashes under an open worktree.
- **Recommendation:** A. The rule already exists because the prose failed once (the `-i` note).

### G2. Every session loads rules that only one stage needs

`CLAUDE.md` is loaded into every session, including a one-line fix. About half of it serves one
stage only: Git Workflow steps 1 to 14, the review routing paragraphs, the spec-to-plan flow.
`docs-layout.md` already shows the other way: it loads only when a file under `docs/plans/` or
`docs/reports/` is touched.

- **Option A: move stage rules out.** Git steps into a rule scoped to `docs/plans/**`, or into
  `my:handoff`, which already runs those stages. Review routing into the review stage of
  `my:handoff`. Pros: less text in every session. Cons: a rule scoped by path may not load in a
  session that needs it, for example a review started by hand without touching a plan file.
- **Option B: keep one file.** Pros: every rule is always present. Cons: the cost is paid in every
  session.
- **Recommendation:** A, for the Git steps only. Keep a two-line pointer in `CLAUDE.md`. The
  review rules are short enough to stay.

Hypothesis, not measured: a long file with many exact rules makes it more likely that a rule is
missed. The rule changes of 2026-09-18 to 2026-10-03 are consistent with this, since several
patch a single observed miss. A test would be to count rule misses in handed-off sessions before
and after the move.

## Steps that ignore size

### S1. The UI rule has no Small case

"UI Design" says to draw a Claude Design canvas "Always, for any screen, state or flow". A Small
change to a label or a spacing value then needs a canvas. The size table does not mention UI.

**Fix:** add one line: a Small change that does not add a screen or a state needs no canvas.

### S2. Documents around the code grow faster than the code

Zitamu `main` since 2026-10-03: 48 `docs` commits, 13 `feat`, `fix` and `test` commits. 31 files in
`docs/plans/` are dated October, and 21 of them are reviews. Of the 48 `docs` commits, 14 edit
the roadmap.

The four-commit rule controls specs and plans. It does not cover roadmap edits, decision
records, briefings or deploy notes. Those are now the main volume. Part of this is the client's
own process: the match grade went from ring with percentage, to ring or bar, to bar, in one
day. That churn is real work, not waste.

**Fix:** decide whether roadmap and decision edits count as docs that fold into the next feature
commit, as specs do. If the answer is no, the ratio is a cost of client work and not of the
workflow.

### S3. Many review files for one feature

The `--plan-only` flag produced eight files in `docs/plans/`: spec, spec review, plan, plan review,
two code reviews, two branch reviews. Each is useful while the branch is open. Few are read
after the merge.

- **Option A: keep every review file.** Pros: a full record. Cons: the directory grows by about
  six files per feature, and the index and the orphan hook must track each one.
- **Option B: fold the end-of-branch reviews into one file per branch,** with a section per
  reviewer. Pros: one file per stage. Cons: a change to `my:handoff review` and to both review
  skills' output paths.
- **Recommendation:** B, but only if the index or the orphan hook costs time today. If nobody
  reads the directory listing, the cost is small and A is fine.

## Evidence limits

- No session was timed. "Fast" above means few commits and short calendar time on `main`.
- Zitamu is shared with another developer. Some of its commits are theirs and follow other rules.
- Most commits in this repo are work on the workflow itself. They are not evidence for or
  against coding speed.

## Where these went

All rows are in `ROADMAP.md`, section "Workflow efficiency".

| Finding | Where it went |
| --- | --- |
| C1, C2 | Row "Trigger table contradictions". |
| C3 | No action. It explains C1 and C2, and their row fixes it. |
| G1 | Row "Fold script for docs fixups". |
| G2 | Row "Git steps leave the always-loaded file", after the G1 row. |
| S1 | Row "UI rule has a Small case". |
| S2 | No action, the user's choice of 2026-10-10. Each docs commit costs seconds, most record the client's changes, and more fixups would add Git steps. |
| S3 | No action, the user's choice of 2026-10-10. No evidence the files cost time; the change would touch three skills. |
