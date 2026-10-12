---
name: status
description: >
  Answer "where are we", "what is next" and "what can be done in parallel" in
  one short, read-only report. Use when the user asks one of those questions,
  says "status", or types /my:status. Runs status-scan.py once for the facts
  (roadmap, open documents, the main checkout, worktrees, auto runs, branches
  that may hold unmerged work), then judges what needs the user, what to do
  next and which items can run together. Writes nothing. NOT for editing the
  roadmap (`my:roadmap-management`).
---

# Status

Answer three questions in one report: where we are, what is next, and what can
run in parallel. Spec: `docs/plans/2026-10-12-status-skill-spec.md` in the
claude-setup repo.

**This skill writes nothing.** No roadmap edit, no status change, no commit, no
session start, no `handoff-state.py set`. The report names commands; the user
runs them. Every command this skill runs itself only reads.

The order of work is the user's decision (`my:roadmap-management` rule 3). The
report reads it; it never proposes a new one.

## Steps

1. **Collect the facts.** Run `status-scan.py` once, from anywhere in the repo.
   It is on `PATH`, as `handoff-state.py` is for `my:handoff`. It prints blocks,
   each starting with `== <name>`, one fact per line, fields split by tabs:

   | Block | Fields |
   | --- | --- |
   | `roadmap` | icon, row number or `-`, title, `docs/plans/` links or `-`, row text |
   | `order` | one line of the roadmap's `## Order of work` |
   | `docs` | status or `no-status`, date or `-`, path |
   | `checkout` | `dirty`, path; or `fixup`, fixup hash, target hash or `?`, target subject |
   | `worktrees` | path, branch, commits ahead of `main`, `clean` or `dirty` |
   | `runs` | slug, slot, `next`, stop line, branch (`-` for empty) |
   | `branches` | `maybe-unfinished`, branch, missing line count, last subject; then `skipped`, count |

   `none` means the block is empty. A line that starts with `error` means the
   block's source could not be read: say so in the report, and do not guess the
   facts it would have given. Exit 2 means the folder is not in a git repo, or
   no branch is checked out in the main checkout: report that and stop.

   `main` in the steps below means the branch checked out in the main
   checkout, which is the branch the script compares with. It is often named
   `main`, but can be `master` or another name. Use its real name in every
   command. When a branch shares no history with it, `main...<branch>` fails;
   use `git diff main <branch>` instead, which needs no merge base.

2. **Check each `maybe-unfinished` branch.** The script's line test can err
   (a squash commit that differs from the branch). For each such branch, pick
   two or three concrete names from `git diff main...<branch>`: a function, a
   file name, a string literal. `git grep` each on `main`. When every name is
   found, the branch is merged: leave it out. Otherwise it is unfinished, and
   needs the user. This is the rule in "Assessing branch redundancy" in
   `global/CLAUDE.md`.

3. **Read the parallel rules.** Read the `## Parallel runs` section of the
   project's `CLAUDE.md` or `CLAUDE.local.md`, if there is one. Take
   **Max runs** (default `2`), **Docs paths** (default `docs/`, `ROADMAP.md`,
   `CHANGELOG.md`) and **Shared resources** (default none).

4. **Find each row's spec.** A row's linked `docs/plans/` path counts as its
   spec only when that spec is about the row: its title or Goal names the same
   change. Otherwise the link is a reference, and the row has no spec. Example:
   a "Deny list has no effect" row that links the spec where the problem was
   found has no spec of its own.

5. **Find the gates.** A row is gated when the `order` block puts it behind
   another open row, or when its own text says it waits: "Waits for …",
   "Blocked by row N", "after …".

6. **Find each item's file list,** for the items step 8 compares. Take the
   first of these that exists:
   1. a started branch: `git diff --name-only main...<branch>`;
   2. the plan's "Files to Modify/Create" section;
   3. the spec's "Files" section.

   An item with none of these has unknown overlap.

7. **Write the report** (below).

## The report

Chat text, three sections, always in this order. Each line names the stage
(spec, plan, code, review, merge or fold) and its evidence.

### 1. Where we are

First the items that need the user:

- a run with a stop line, and the stop line;
- a `draft` spec waiting for review;
- `fixup!` commits on `main`;
- uncommitted paths in the main checkout;
- a branch still unfinished after step 2.

Then one line per item in progress: a run whose `next` is not `finished`, a
worktree (for example "worktree `feat/x`, 4 commits ahead, clean"), an
`approved` or `current` document, a 🚧 row.

Last, when the `docs` block has `no-status` files, one line with their count,
such as "20 files in `docs/plans/` have no status line". Do not list them, and
do not count them as needing the user.

### 2. What is next

At most three items, each with the exact command to run:

1. What is started and stopped first: a stopped run
   (`/my:handoff auto resume <spec>`), a pending fold (`git-fold-fixups.py`).
2. Then the first rows of `## Order of work` that nothing gates.
3. Without an order section: 🚧 rows, then 📋 rows, in roadmap order. Say that
   roadmap order was used because no order was given.

A row with no spec gets "write its spec" as its command
(`superpowers:brainstorming`).

### 3. What can run in parallel

Two items may run together only when all three hold:

- the order of work, or a row's own text, does not gate one behind the other;
- their file lists share no path outside the docs paths;
- the runs whose `next` is not `finished`, stopped ones included, plus the new
  runs, stay within **Max runs**.

A resource under **Shared resources** does not stop two items from running
together: each run uses it under its lock, so the runs take turns on it. When
both items are code work, list them as safe, and add that they wait for each
other on the project's locks, by name. One exception: when one item's file
list holds a file that a **Shared resources** command names or runs, such as
its script, the other item would use a changed resource. Do not list that
pair as safe, and say why.

An item with unknown overlap is never listed as safe; say that its overlap is
unknown. Without a "Parallel runs" section, allow one auto run, and offer the
second item as a supervised session (`/my:handoff code <doc>`): the auto start
refuses a second auto run there. When a fold is pending and a run's `next` is
not `finished`, say to fold before starting more runs.

When nothing is open, the whole report is one line: "Nothing in progress.
Next: …".

### Example

```markdown
**Where we are**
- Needs you: run `status-skill` stopped at code: fold refused.
- Needs you: 7 `fixup!` commits on `main`, of two specs.
- Code: worktree `feat/parallel-auto-runs`, 2 commits ahead, clean.
- 20 files in `docs/plans/` have no status line.

**What is next**
1. Resume the stopped run: `/my:handoff auto resume docs/plans/2026-10-12-status-skill-spec.md`.
2. "Deny list has no effect" (📋) has no spec: write it with `superpowers:brainstorming`.
No order of work is given, so this uses roadmap order.

**What can run in parallel**
- Nothing new: two auto runs are live, and **Max runs** is 2.
```
