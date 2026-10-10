# Review: main..feat/git-fold-fixups

**Status:** review of main..feat/git-fold-fixups, 2026-10-10. Mixed: the fix round closes both Warnings of the first review as the spec now says, but `check` still passes a target that has a merge commit after it, and the fold then refuses that fixup for good. zitamu's `main` has such merges, the latest from 2026-10-09. By the one-fix-round rule this goes into Risk as a known limit, not into a code fix.

## Change Summary

The branch adds `plugins/my/bin/git-fold-fixups.py`. Its `check <sha>` command says whether a fixup of a commit is safe. With no argument, it folds every waiting `fixup!` commit, or it refuses with one line and changes nothing. The fourteen feature steps move from `global/CLAUDE.md` to `global/rules/docs-layout.md`, and `my:handoff` calls the script. The fix round did four things. It made `check` share the fold's per-target refusals through one function, `target_refusal`. It added a shared-subject refusal to `check`. It made a detached-HEAD worktree count as a holder. It recorded the zitamu `pre-push` hook edit in the spec's blast radius and in Task 6.

## Plan Alignment

The implementation matches the spec as amended in the review round (D2, Risk, Task 6). I checked these points:

- D2, "held": `plugins/my/bin/git-fold-fixups.py:63-84` reads branch holders from `for-each-ref --contains … %(worktreepath)`, skips empty paths and the current worktree, then reads `git worktree list --porcelain` and counts a detached worktree whose `HEAD` contains the commit. This matches the spec's new D2 paragraph.
- D2, what `check` refuses: `:248-265` refuses when `target_refusal` (`:103-110`, held or already on the upstream) gives a reason, or when another first-parent commit shares the subject. The fold uses the same `target_refusal` at `:176-180`, so `check` and the fold can no longer disagree on held or pushed targets. This was the first review's top finding.
- A configured but missing upstream raises in `upstream()` (`:98-99`), and `main` turns that into exit `1` (`:278-280`) for `check` and for the fold alike. This matches the spec's "Found in the review round" bullet.
- Tests: `plugins/my/tests/test_git_fold_fixups.py:133-154` add `check` tests for a pushed target, a shared subject and a detached worktree. `:261-274` add fold tests for a detached worktree and a missing upstream ref. I ran the suite: 27 tests pass.
- Task 6 and the Risk blast radius name the zitamu `.git/hooks/pre-push` lines 2 and 11. They are edited after the merge, together with the D6 sentence. This closes the first review's second Warning. The edit happens after the merge, so it is not missing from this range.
- The docstring (`:11-15`) and the README paragraph describe `check` in the new terms.

No deviation from the text of the amended spec. The spec's stated principle goes further than its list, though. D2 says `check` refuses "when the fold would refuse a fixup of `<sha>` for good or for now", but then lists only held, pushed and shared subject. Two range refusals of the fold, D4.6 (merge) and D4.8 (`squash!` or `amend!`), are not in `check`. See the Warning below.

- (missing) `check` does not run D4.6 or D4.8. `plugins/my/bin/git-fold-fixups.py:248-265` against `:181-188`.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / Medium | `check <sha>` passes a target that has a merge commit, or a `squash!`/`amend!` commit, between it and `HEAD`. The fold refuses that range for good (D4.6, D4.8), and nothing removes the commit from the range. This is the same failure as the first review's top Warning: `check` says yes, the fixup is made, and every later fold on the branch is refused. In zitamu the fixup also cannot be pushed, because the `pre-push` hook refuses `fixup!` commits. I reproduced it in a scratch repo: target, then a `--no-ff` merge, then `check <target>` exited 0. After `fixup! docs: spec`, the fold exited 1 with `merge commit … is in the range`. Realistic: zitamu's first-parent `main` has pull merges ("Merge branch 'main' of https://gitlab…"), dated 2026-10-09 and 2026-09-23. A spec committed locally, then a `git pull` that merges, puts the spec target before a merge. claude-setup's `main` has no merges and no `squash!`/`amend!` commits. | `plugins/my/bin/git-fold-fixups.py:248-265` (`check` runs `target_refusal` and the subject test only); `:181-188` (the fold's range refusals); spec D2, "for good or for now"; `git -C ~/projects/zitamu/real-estate-webapp log --merges --first-parent main` | By the one-fix-round rule: add a known limit to the spec's **Risk** section, for example "A target with a merge, `squash!` or `amend!` commit after it on the first-parent history passes `check`, and the fold then refuses it for good. zitamu's `main` has pull merges." If the user prefers to close it, `check` would run the same range test as `refusal`, using `range_args(sha)`. That is a contract change and needs the user's decision. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| One function, `target_refusal`, decides held and pushed for both `check` and the fold. The fix removes the cause (two separate rules), not only the symptom. | `plugins/my/bin/git-fold-fixups.py:103-110`, `:177-180`, `:258` | Strong |
| The shared-subject test in `check` looks at the same first-parent history as the fold's ambiguity rule. A target that `check` passes therefore has exactly one candidate when the fold looks for it. The one exception, a target outside the first-parent history, is a known limit in Risk. | `:254-261` against `:126-133`, `:170-175` | Moderate |
| A detached worktree is checked with an ancestor test on its own `HEAD`, and the current worktree is skipped by its real path. This covers a worktree in the middle of a rebase, which has no branch. | `:77-83`; tests at `test_git_fold_fixups.py:147-154`, `:261-265` | Strong |
| Every new refusal has a test that runs the real command, and the whole suite passes (27 tests). | `plugins/my/tests/test_git_fold_fixups.py:133-154`, `:261-274` | Strong |
| The step text did not need to change: steps 4 and 8 already say "if it exits 1, make a normal commit". The wider `check` now sends a pushed or ambiguous target to a normal commit too, with no new prose. | `global/rules/docs-layout.md:150`, `:155` | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| `check` covers the fold's per-target refusals, but not its range refusals. A target with a merge after it passes `check`, and the fold then refuses it on every run. | `plugins/my/bin/git-fold-fixups.py:248-265`, `:181-188` | Medium |

## Not Applicable

None.

## Needs Investigation

- **Tools that leave detached worktrees.** Since the fix round, any detached worktree whose `HEAD` contains a target makes `check` and the fold refuse (`plugins/my/bin/git-fold-fixups.py:77-83`). The user chose this rule, and the refusal names the path. I checked that a worktree whose folder was deleted without `git worktree prune` still refuses, and names the deleted path. This repo has no detached worktree today. I could not check whether a tool the user runs, such as a review harness, leaves detached worktrees behind. If one does, every fold waits until someone removes or prunes it. The first real fold after the merge will show it.
- **A user-level rule loading for a new file** is still untested. The spec's Risk section lists it, so it is not a finding. The pointer in `global/CLAUDE.md` ("read it if it has not loaded") is the fallback.

## Reasoning

The fix round does what the user decided. `check` and the fold now share one function for held and pushed targets. `check` also refuses a shared subject. A detached worktree counts as holding. Each change has a test through the real command, and the suite passes. The zitamu hook is now in the spec's blast radius and in a post-merge task. One gap of the same kind as the first Warning remains: `check` does not run the fold's range refusals, and zitamu's `main` has the merges that trigger them. The approach is right and the gap is narrow, so the verdict is Mixed. By the one-fix-round rule, the answer is a Risk entry.

## Verdict

**Assessment:** Mixed
**Confidence:** High. I read the script and the tests in full, matched them against the amended D2, Risk and Task 6, ran the 27 tests, and reproduced the Warning in a scratch repo.
**Recommendation:** Add the range-refusal gap to the spec's **Risk** known limits, or ask the user whether `check` should run the range test too. Then squash-merge. After the merge, do the Task 6 manual steps: the `~/bin` symlink, the zitamu `CLAUDE.local.md` sentence and the zitamu `pre-push` hook lines 2 and 11.
