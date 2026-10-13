---
paths:
  - "**/docs/plans/*.md"
  - "**/docs/reports/*.md"
---

# Where design documents live

These rules apply unless the project documents its own layout. If it does, follow the project
and do not convert it without asking. Some projects generate their index, or keep status in
`ROADMAP.md` instead of in each file. The section "One feature, four commits on `main`" is the
exception: it is part of the Git Workflow and always applies. A project names only what differs
there.

## Kinds of document

| Kind | What it is | Where | Name |
| --- | --- | --- | --- |
| Spec | What to build and why. | `docs/plans/` | `YYYY-MM-DD-<slug>-spec.md` |
| Plan | How to build it: steps, tests, commits. | `docs/plans/` | `YYYY-MM-DD-<slug>.md` |
| Review | A report on one spec, one plan or one diff. It sits next to what it reviewed. | `docs/plans/` | `…-review.md`, `…-review-2.md` |
| Report | Findings about a whole product or area on one day, such as a design critique, an audit or an architecture critique. Other documents fix what it finds. It is never carried out itself. | `docs/reports/` | `YYYY-MM-DD-<slug>-critique.md`, `-audit.md` |
| Action plan | Optional. Routes a large report's findings into roadmap rows once, then stays as a reference. | `docs/plans/` | `YYYY-MM-DD-<slug>-action-plan.md` |
| Briefing | A plain-language write-up for readers outside engineering (`kit:briefing`). | `docs/briefings/` | `YYYY-MM-DD-<slug>.md` |

The test for "report or review": a review has one subject that someone will change in answer to
it. A report has many findings across many files, and several later documents answer it.

## From report to roadmap

A report's findings become rows in the project's roadmap. The roadmap is the one live list of
work, and it keeps the only order. The chain is:

```text
report → roadmap rows, placed in the order → spec or plan, by size → branch
```

- **The roadmap keeps the order.** It lives in the roadmap's `## Order of work` section
  (`my:roadmap-management` rule 12). No other document holds the order, a gate, or whether work
  has started or shipped. A document that did would be a second copy, and copies drift.
- **Each row cites its finding:** the report's path and the finding's reference (item letter,
  finding code or heading).
- **A row that cannot start says why, in the row:** `Blocked by row N.`, or `Waits for <what>.`
  for a blocker outside the roadmap, such as a client's answer or a missing file.
- **The report records where its findings went.** A short "Where these went" section maps each
  reference to a row, or to "no action" with a reason. The report's status line names the rows.
- **Bug fixes and features are separate rows,** so they become separate branches.
- **Shared things come first.** A row that adds tokens or components sits before the rows that
  use them in pages. This keeps each value from changing twice.
- **Decisions go where the work reads them.** A decision about one row goes into that row's
  spec. A decision for the whole product goes into the project's `CLAUDE.md`. Do not keep a
  separate decision log that work has to search.

### Routing a report

1. **Read the whole report.** Note each finding's reference.
2. **Sort the findings.** Mark each one as a bug, a feature, a shared definition (tokens,
   components), a use of shared things in pages, a product decision, blocked outside the
   project's scope, or no action.
3. **Propose rows and their place in the order** to the user. Group the findings that one branch
   would fix into one row. Wait for the user's answer: the order is a decision, so it is not
   guessed.
4. **Write it down.** Add the rows and their place in `## Order of work`. Add "Where these went"
   to the report and update its status line. If the project has an index, update the report's
   row in the same commit.
5. **Run the checklist** below, then commit. This is documentation only, so it needs no
   worktree.

### When an action plan helps

Route directly when you can. Write an action plan only when a report is too large to route in
one sitting, or when the grouping needs several rounds with the user.

- **It is a working file for the routing,** nothing more: the groups, the user's answers with
  their dates, and the questions still open.
- **It ends when every finding has a row or a reason.** Its status becomes `done`, naming the
  commit that added the rows. After that it is a reference, and nobody edits it.
- **It never holds the order, a gate, or the state of work.** Those are in the roadmap from the
  first row on.
- **A later report gets its own routing.** It does not join an old action plan.

### Checklist

- Every finding in the report has a row, or a reason in "Where these went". None is missing.
- Every row cites its finding's reference.
- No row mixes a bug fix and a feature.
- No row uses a shared definition before the row that defines it, in the order.
- Every row that cannot start says what it waits for.
- The order lives only in the roadmap. An action plan, if there is one, is `done` and holds no
  order.
- After any move or rename, `git grep` finds no link to the old path.

## Status line

Every file in `docs/plans/` and `docs/reports/` opens with one line, just under its title:

```markdown
**Status:** <status>, <YYYY-MM-DD>. <one sentence>.
```

| Status | Meaning |
| --- | --- |
| `draft` | Written, waiting for the user's approval. |
| `approved` | Approved, not started yet. |
| `planned` | An agreed later step, not started. |
| `current` | Work in progress, or a report that is still the live source of findings. |
| `parked` | A draft set aside until a named step decides what happens to it. |
| `done` | Shipped. The sentence names the commit. |
| `superseded` | Will not be carried out. The sentence names what replaces it. |
| `withdrawn` | Dropped. Nothing replaces it. |
| `review of <file>` | A review. The sentence names what it reviewed and what answered it. |

Update the status when it changes: a spec is approved, a plan's branch is merged, or a document
is replaced or dropped.

## Index

An index at `docs/plans/README.md` is optional. It lists every file in `docs/plans/` and
`docs/reports/`, gives the reading order for the current work, and tells how the work got here.
A file gets its row in the same commit that creates it or changes its status.

The line `<!-- plans-index: strict -->` in that README turns on two checks in the
`check-orphan-plans.sh` session hook: a file missing from the index, and a file with no status
line. Without the line, the hook checks only that files are committed and dated.

## Moving a document

When a document moves or is renamed, update every link to it. Search the repo for the old path
with `git grep`. Keep superseded documents in place, marked `superseded`, instead of deleting
them.

## One feature, four commits on `main`

A Large feature leaves four commits on `main` (Small and Medium leave fewer, as the size table in
`~/.claude/CLAUDE.md` says): the spec with its review, the plan with its review, the squash-merged
code, and the `done` mark. Without this rule, most commits are small edits to one spec or plan: on
zitamu, 44 of 52 commits by 2026-09-18 were `docs:`. Docs are written in the main checkout,
because an `@` mention cannot reach `.claude/worktrees/`. Code is written in a worktree, because
sessions often run in parallel. A project's own file names only what differs: its plans index, its
scopes, its test commands.

Two more commits are allowed. `my:architect` commits the architecture brief on its own, before
step 1. An edit to another document that the spec forces, such as a glossary or a data model, is
its own commit, not a fixup of the spec.

1. Write the spec on `main`.
2. Write the spec review on `main`.
3. Commit the spec and the review together.
4. Fixup any later spec and review edits, with `git commit --fixup <hash>`. Run
   `git-fold-fixups.py check <hash>` first. If it exits 1, make a normal commit instead. Always
   name the target by hash, never `--fixup HEAD`: a parallel session may have committed in between.
5. Write the plan on `main`.
6. Write the plan review on `main`.
7. Commit the plan and the plan review together.
8. Fixup any later plan and plan-review edits. Run `git-fold-fixups.py check <hash>` first. If it
   exits 1, make a normal commit instead. Always name the target by hash, never `--fixup HEAD`: a
   parallel session may have committed in between.
9. Fold the fixups with `git-fold-fixups.py`. It refuses, and changes nothing, when the fold is not
   safe; its message says why. Run it when no other session has uncommitted edits in the main
   checkout.
10. Create the worktree, and write the code there.
11. Make doc edits in the worktree as required, but never edit the project's plans index there.
    While the worktree exists, edit this feature's spec and plan only in the worktree.
12. Squash-merge the branch into `main`, and commit.
13. Mark the spec and plan `done` on `main`, citing the squash commit.
14. The user pushes at their own pace.

In a project whose `CLAUDE.md` or `CLAUDE.local.md` has a "Parallel runs" section (the `my:handoff`
skill defines it), several auto runs share `main`. There, every commit in the main checkout runs
under lock `main`, as one command that stages, commits and lists the commit. Write the message
with the Write tool to a new file in the session's scratchpad, then run:

```bash
locked-commit.py -F <message file> <paths>
```

Before it, read `git diff -- <paths>` and each new file whole: `git diff` does not show a file git
does not track yet. After it, read the `git show --stat` list it printed. Steps 4 and 8 make normal
commits, not fixups, and step 9 is skipped: a fold could give another run's cited commit a new hash.
Four commits remain the goal elsewhere.

- **No commit only changes a status.** There is no "in progress" commit. A status change goes into
  the commit that causes it.
- **Cite only commits on `main`.** Never cite a commit that lives only on a local branch. A review
  names the decisions and sections it read, like "D12 to D16", not a hash, because later fixups fold
  the answers into the reviewed commit. zitamu (`real-estate-webapp`) has uncommitted `pre-commit`
  and `pre-push` hooks that enforce this rule and refuse a push with `fixup!` commits.
