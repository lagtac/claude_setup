# Critique: the development workflow, efficiency

**Status:** current, 2026-10-12. Findings on whether the global rules, Superpowers and the `my:` skills make coding faster; C1, C2, S1, G1 and G2 are fixed; S2 and S3 need no action; the measurements of 2026-10-12 (M1 to M3) need none either, and a roadmap row measures again later; M4 gives three rows.

## How to read this

- **Subject:** `global/CLAUDE.md` (4,750 words), `global/rules/docs-layout.md` (1,183 words),
  `global/rules/plan-format.md`, and the `my:` skills that the flow calls: `my:handoff`,
  `my:spec-review`, `my:soundness-review`, `my:architect`, `my:roadmap-management`.
- **Evidence:** the `main` history of this repo and of `zitamu/real-estate-webapp`. Only commits
  after each rule existed count against that rule. The four-commit rule arrived on 2026-09-24.
  The size table arrived on 2026-10-03.
- **Method:** the files were read. Nothing was timed. Claims about model attention are marked as
  hypotheses.
- **Measurements of 2026-10-12:** the section of that name adds timings from zitamu's git history.
  They come from the zitamu report
  `real-estate-webapp/docs/reports/2026-10-12-commit-size-audit.md`, sections "Pace" and "Where
  the branch `fix` commits came from", committed on zitamu's `main` in `f865401` and `d441494`.
- **Charts:** M1 to M4 each have a chart in `assets/2026-10-09-workflow-efficiency/`.
  `extract.py` reads zitamu's git history into `data.json`, and `plot.py` draws the SVG files
  from it. `review_fixes.py` lists M4's candidate commits; `review_fix_classes.json` holds the
  class given to each by hand. The usage line is at the top of each script.

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

**New count, 2026-10-12.** Over the four full weeks from 2026-09-14, zitamu made 249 docs-only
commits for 52 merged branches: 3.3, 4.4, 8.2 and 6.3 per branch by week, 4.8 on average. A Large
change plans for three. The count is higher than the plan and rising, but nothing shows that the
extra commits cost time. The user kept "no action" on 2026-10-12.

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

## Measurements of 2026-10-12

These come from the zitamu report named in "How to read this". Times are from author dates, because
the fixup fold rewrites commit dates. Spec times cover the 28 zitamu specs marked `done`.

### M1. The code stage is not what limits throughput

A branch lives 1.1 hours at the median, from its first commit to its squash-merge. A spec reaches
`done` 4.6 hours after its first commit at the median. About 13 branches merge per week, so
building fills about 14 hours of the week. The week with the fewest branches, 6, did not have
short branches: its median branch lived 3.6 hours. This suggests that throughput depends on how many
specs are ready, not on how fast agents write code. Git cannot prove it, because it does not
record waiting.

![Branch lead time per week, one dot per branch](<assets/2026-10-09-workflow-efficiency/m1-branch-lead-time.svg>)

The chart also shows that the weekly median grew: 0.5, 1.4, 3.6 and 2.8 hours. Branches grew too,
with the client batches. The chart finds each branch's squash commit in a simpler way than the
zitamu report, so its median is 1.0 hours, not 1.1.

**Fix:** none. Making the agents write code faster would change little.

### M2. Waits between stages make the long cycles

The average spec takes 12.7 hours, almost three times the median. The five specs that took over
12 hours each had one gap of 17 hours or more between two stages: spec to plan, or plan to `done`.
Such a gap looks like a night with no session, not like slow work.

![Hours per spec, split by stage, longest first](<assets/2026-10-09-workflow-efficiency/m2-spec-stages.svg>)

**Fix:** none new. `my:handoff auto` (shipped in `39737e1`, on 2026-10-12) runs the stages without
waiting for the user. The measured weeks are all before it, so its effect is not known yet.

### M3. The end-of-branch reviews find real defects, in one small round

Of the 105 `fix` commits on zitamu's branches, 40 fix what the end-of-branch reviews found. 38 of
those 40 change what a user, a screen reader or a crawler meets. One example: a video that could
never play, while every test passed. 29 of 55 branches have a review fix, and 21 of them have
exactly one. The other `fix` commits are the branch's planned work (49), defects found while
building (11), and 5 whose message does not say.

7 of the 40 messages say that the user chose the answer, on 6 of the 55 branches. So with
"Design-changing findings: `stop`" in a Delegation section, about 1 auto run in 9 would stop for a
review finding.

![Causes of the 105 branch fix commits](<assets/2026-10-09-workflow-efficiency/m3-fix-causes.svg>)

The chart copies the zitamu report's counts. The commits were sorted by reading each message,
so no script repeats the count.

**Fix:** none. This supports one review round per branch, and S3's "no action".

### M4. A spec or plan could have prevented about half of the review fixes

M4 sorts the review fixes by where each defect started. It counts 42, not 40, because it takes
every branch `fix` commit that changes application code and names a review in its message. Four
more such commits were left out: planned work, a design critique, and a branch made after the
audit. Each message was read and given one class.

| Where the defect started | Fixes | Could a spec or plan prevent it? |
| --- | --- | --- |
| The code broke a rule the spec already stated | 17 | No. Review exists for this. |
| Layout broke at a width, a language or a text length nobody checked | 10 | Yes, the plan |
| The spec missed or got wrong a decision | 7 | Yes, the spec |
| Browser or framework behaviour | 4 | No |
| The test checked the wrong thing | 3 | Yes, the plan |
| Comments only | 1 | — |

![Where the 42 review fixes started](<assets/2026-10-09-workflow-efficiency/m4-review-fix-sources.svg>)

- **Layout is the largest group a plan could prevent.** The same widths recur: 320 to 380 px,
  820 px, 960 px, 1440 px and up. So do a language switch and text that grew.
- **All six fixes the user decided are spec gaps.** They are off-path events the spec did not
  cover: Back and Forward, deleting a listing, a header that hides, copy for an edge case. These
  are the findings that stop an auto run.
- **9 of the 42 messages also say a test was weak or missing.** One example: the video with no
  source passed tests of its poster and tracks, but no test checked that it plays.

The class is a judgment from the message. Some fixes fit two classes, and the line between layout
and code is the softest.

**Fix:** three rows. A plan that changes UI names the layouts to check. `my:spec-review` checks
that the spec decides off-path events, such as Back or a deleted record. The existing "End-to-end
coverage" rule asks the test to check the result a user gets, not only the markup.

## Evidence limits

- No session was timed. "Fast" above means few commits and short calendar time on `main`. M1 to
  M3 measure calendar time from git, which cannot tell work from waiting.
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
| S2 | No action, the user's choice of 2026-10-10, kept on 2026-10-12 with the new count. Each docs commit costs seconds, most record the client's changes, and more fixups would add Git steps. |
| S3 | No action, the user's choice of 2026-10-10. No evidence the files cost time; the change would touch three skills. |
| M1, M3 | No action. They support the current flow. |
| M2 | No action now; `my:handoff auto` answers it. Row "Measure the auto runs" checks its effect. |
| M4 | Rows "Plan names the layouts to check", "Spec review checks off-path events" and "E2E tests check the result". |
