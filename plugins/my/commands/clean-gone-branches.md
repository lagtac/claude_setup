---
description: Cleans up all git branches marked as [gone] (branches that have been deleted on the remote but still exist locally), including removing associated worktrees.
---

## Your Task

Delete local branches whose upstream branch was deleted on the remote (`[gone]`), and remove their worktrees. Run this only because the user asked for it: merged branches are otherwise kept as a record, so never run it as a side step of other work.

Deleting a branch and removing a worktree cannot be undone from this command. So it lists first, asks, and removes nothing that has uncommitted work.

## Steps

1. **Refresh the remote state.** Without this, `[gone]` reflects the last fetch, which may be stale.

   ```bash
   git fetch --prune
   ```

2. **List the candidates.**

   ```bash
   git branch -v | grep '\[gone\]'
   git worktree list
   ```

   A `+` before a branch name means a worktree has it checked out. A `*` means it is the current branch.

   If there are no `[gone]` branches, report `No [gone] branches; nothing to clean.` and stop.

3. **Check each worktree for uncommitted work.** For each `[gone]` branch with a worktree at `<path>`:

   ```bash
   git -C "<path>" status --porcelain
   ```

   A worktree with any output is **dirty**. It and its branch are skipped in step 5.

4. **Show the plan and ask.** Print one table: branch, last commit (from `git branch -v`), worktree path or `none`, and the action (`delete`, or `skip: dirty worktree`, or `skip: current branch`). Then ask with `AskUserQuestion`: `Delete as listed` or `Cancel`. If `AskUserQuestion` is not available, print the table, say `Reply "delete" to run it`, and end the turn. Delete nothing without an explicit approval.

5. **Delete, one branch at a time.** For each branch marked `delete`:

   ```bash
   git worktree remove "<path>"     # only when it has a worktree; never --force
   git branch -D "<branch>"
   ```

   `git branch -D` is needed because a squash-merged branch never looks merged to git. If `git worktree remove` fails, report the error, skip that branch's deletion, and continue with the next branch.

6. **Report.** List the worktrees removed, the branches deleted and the branches skipped, each with its reason.
