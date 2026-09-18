---
paths:
  - "**/docs/plans/*.md"
  - "**/docs/reports/*.md"
---

# Where design documents live

These rules apply unless the project documents its own layout. If it does, follow the project
and do not convert it without asking. Some projects generate their index, or keep status in
`ROADMAP.md` instead of in each file.

## Kinds of document

| Kind | What it is | Where | Name |
| --- | --- | --- | --- |
| Spec | What to build and why. | `docs/plans/` | `YYYY-MM-DD-<slug>-spec.md` |
| Plan | How to build it: steps, tests, commits. | `docs/plans/` | `YYYY-MM-DD-<slug>.md` |
| Review | A report on one spec, one plan or one diff. It sits next to what it reviewed. | `docs/plans/` | `…-review.md`, `…-review-2.md` |
| Report | Findings about a whole product or area on one day, such as a design critique, an audit or an architecture critique. Other documents fix what it finds. It is never carried out itself. | `docs/reports/` | `YYYY-MM-DD-<slug>-critique.md`, `-audit.md` |
| Action plan | Breaks a report's findings into phases. | `docs/plans/` | `YYYY-MM-DD-<slug>-action-plan.md` |
| Briefing | A plain-language write-up for readers outside engineering (`my:briefing`). | `docs/briefings/` | `YYYY-MM-DD-<slug>.md` |

The test for "report or review": a review has one subject that someone will change in answer to
it. A report has many findings across many files, and several later documents answer it.

## Action plans

A report's findings become work through one action plan. The chain is:

```text
report → action plan (phases) → spec → plan → branch
```

- **One file.** Every phase is a section of the action plan. Do not write one file per phase: a
  phase only scopes work that later gets its own spec or plan, so a separate file adds a layer
  that looks like a plan and is not one.
- **A later report on the same area joins the existing action plan.** Route its findings into
  the phases that exist, or add a phase. Do not start a second action plan.
- **Sections:** "How to read this"; "Order", a table with the columns Phase, Starts, Gate and
  Leads to; "Decisions", one numbered list for the whole plan; then one section per phase.
- **Each phase section** holds the scope, what is out of scope, the gate, the next document (a
  spec, a bug-fix plan, or none), what it needs, and notes the later plans must cover. It holds
  no implementation steps.
- **Define shared things before pages use them.** A phase that adds tokens or components changes
  no page. Using them in pages is a later phase. This keeps each value from changing twice.
- **Bug fixes and features are separate branches,** even inside one phase.
- **One order only.** The action plan keeps the order of the phases. The roadmap links to it and
  does not copy that order.

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
