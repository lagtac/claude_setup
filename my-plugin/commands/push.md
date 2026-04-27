---
description: Push with pre-push checks
---

# Push instructions

Follow these steps in order. Stop and report on any abort condition — do not auto-resolve.

1. **Verify clean tree.** Run `git status`. If there are uncommitted changes, **stop and report** — do not auto-stash, do not commit on the user's behalf. Tell the user what's uncommitted and ask how they want to proceed.

2. **Detect upstream state.** Run `git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null`.
   - **No upstream**: stop and report. Tell the user the current branch has no upstream and ask whether to push with `-u origin <branch>`. Do not set upstream automatically.
   - **Diverged from upstream** (run `git status -sb` and look for "ahead N, behind M" with both non-zero): stop and report. Never force-push without an explicit instruction from the user.

3. **Show what will be pushed.** Run `git log --oneline @{u}..HEAD`. If empty (nothing to push), tell the user and stop.

4. **Push to the remote.** Use plain `git push` — no `--force`, no `--force-with-lease`, no `--no-verify` unless the user has explicitly asked for them in this turn. If the push is rejected, report the rejection reason verbatim and stop; do not retry with force.
