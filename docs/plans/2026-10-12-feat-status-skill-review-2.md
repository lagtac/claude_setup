# Review: main..feat/status-skill

**Status:** review of main..feat/status-skill, 2026-10-12. Mixed: the fix round resolves both Warnings from the first review. One new Warning remains: for a branch with no shared history, the fix sends the model to a two-dot diff whose `-` side is mostly `main`'s own later work, and step 2 does not say to take names from the added lines only.

**Scope:** main..feat/status-skill, diffed from the merge base of local `main` and `feat/status-skill` (local `main`, not `origin/main`). The merge base is `5c45b41`, which is also the tip of local `main`, so the range holds exactly the branch's commits. This is the final re-review after one fix round.

## Change Summary

The branch adds `plugins/my/bin/status-scan.py`, a read-only script that prints seven tab-separated blocks of facts: roadmap rows, order of work, open documents, the main checkout, worktrees, auto runs, and branches that may hold unmerged work. It adds `plugins/my/skills/status/SKILL.md`, which runs the script once and judges "where we are", "what is next" and "what can run in parallel". It also adds 19 subprocess tests, README lines, one edited "Out of scope" line in the parallel auto runs spec, the first review, and Risk item 7 in the spec. The fix round adds a no-shared-history path in `branch_facts`, an exit-code reason in `git()`, a definition of `main` in SKILL.md step 1, and one test.

Caller sweep: done by text search only (`grep -rn`), because this reviewer has no symbol-reference tool. The payload removes or renames no symbol. The only callers of the new script are the skill and the tests (see the caller map).

## Plan Alignment

The implementation still matches the spec (`docs/plans/2026-10-12-status-skill-spec.md`) closely. The first review recorded the deviations it found (wider signatures for Task 2, exit 2 for a usage error) as harmless, and they still are. The suite passes: 85 tests, all OK, including the new `test_orphan_branch_compared_with_all_of_main`.

- `plugins/my/bin/status-scan.py:242-248`: a NEW deviation from D4. D4 (spec lines 110-116) defines the comparison only through `main...<branch>` and `<merge-base>..main`. The fix round adds a third rule: a branch with no merge base is diffed from the empty tree and compared with every line `main` ever added or deleted. The rule is sound, but neither D4 nor Risk 7 records it. The script's own docstring (`status-scan.py:27-29`) still says "since the branch split off". See the Suggestion row.
- (missing) Task 4, the rehearsal. The caller says its result is in the body of the Task 5 docs commit and will go into the squash message. Per the caller's note, this is not a finding.

**Status of the first review's Warnings:**

1. **No shared history wiped the whole `branches` block: resolved.** `status-scan.py:242-248` catches the `merge-base` failure for each branch and compares that branch from the empty tree with all of `main`'s history. `status-scan.py:68` now gives `exit N` when stderr is empty. On `~/projects/grispy2-web-ext`, where all three local branches share no history with `main`, the block now prints `maybe-unfinished feat/plane-a-events 3 …` in 0.19 s. Before the fix it printed one error line. That repo's `main` has the "add the field classifier" commit, and `feat/field-classifier` is now hidden, which fits. The squasher backup is also hidden. On this repo the block is unchanged: one branch, `feat/spec-review-off-path`, 1 line, in 1.3 s. The per-worktree form of the same weakness is now a known limit in Risk 7, so it is not a finding.
2. **SKILL.md assumed the base is named `main`: resolved.** `SKILL.md:47-51` defines `main` as the branch checked out in the main checkout, and says to use its real name in every command.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / Medium (NEW, from the fix round) | For a branch with no shared history, `SKILL.md:50-51` replaces `main...<branch>` with the two-dot `git diff main <branch>`. That diff's `-` side is mostly `main`'s later work, not the branch's own deletions. Step 2 (`SKILL.md:54-56`) says "pick two or three concrete names from" the diff and `git grep` them on `main`, and "when every name is found, the branch is merged". It never says to take the names from the added lines only. Names from the `-` side are on `main` by definition, so step 2 can clear an unfinished branch. That undoes the Goal 4 gain that the script fix won. The same gap exists, in a smaller form, for an ordinary branch whose finding is a deletion (`test_delete_only_branch_listed`): its deleted names are still on `main`. | `plugins/my/skills/status/SKILL.md:50-51`, `:54-58`. In `~/projects/grispy2-web-ext`, the one flagged branch, `feat/plane-a-events`, gives 9 insertions and 462 deletions in `git diff main feat/plane-a-events`. The deletions are `main`'s later text in `docs/decisions.md`, `docs/core-model.md`, `CLAUDE.md` and a briefing, all of which `git grep` finds on `main`. | One phrase in step 2: take the names "from the added (`+`) lines". For a branch that only deletes, add: "check that the deleted lines are gone from `main`". Under the one-fix-round rule this can go into Risk 7 instead, as a known limit of the skill's judgment. |
| Suggestion / High (NEW) | The no-shared-history rule is in the code only. D4 still defines the check through the merge base, Risk 7 does not mention the new path, and the script docstring says "since the branch split off". A cold reader of the approved spec, which becomes the `done` record, cannot learn that such a branch is compared with all of `main`'s history. | `plugins/my/bin/status-scan.py:27-29`, `:242-248`; `docs/plans/2026-10-12-status-skill-spec.md:106-116` | Add one sentence to D4 and to the docstring: "A branch with no merge base is diffed from the empty tree and compared with every change on `main`." |

The first review's two Warnings are resolved (see Plan Alignment). Neither is carried over.

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| The orphan fix treats the root cause per branch. It does not skip the branch or mask the failure: the branch is still compared, against the widest true baseline. On a real repo this hides the merged `feat/field-classifier` and the squasher backup, and still flags `feat/plane-a-events`. | `plugins/my/bin/status-scan.py:242-260`; scan of `~/projects/grispy2-web-ext` | Strong |
| The error reason no longer goes empty when git writes nothing to stderr. | `plugins/my/bin/status-scan.py:68` | Moderate |
| The `seen` cache, keyed by the fork, works for the new path: all orphan branches share one empty-tree key and one full `git log -p`. The cost stayed low on real data (0.19 s and 1.3 s). | `plugins/my/bin/status-scan.py:249-254`; timed runs | Moderate |
| The new test puts an orphan branch whose lines are on `main` next to an unfinished branch, and expects only the unfinished one. Before the fix it would have failed on the error line. | `plugins/my/tests/test_status_scan.py:223-230` | Moderate |
| The base-branch definition in SKILL.md matches the script's rule and the spec's D3 wording. It also covers the `...` failure for unrelated histories. | `plugins/my/skills/status/SKILL.md:47-51`; `plugins/my/bin/status-scan.py:78-79` | Strong |
| The facts/judgment split, the block format and the runs fallback are unchanged from the first review, which judged them sound. The full suite passes (85 tests). | `plugins/my/bin/status-scan.py:1-35`; test run | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| The skill's `git grep` check can clear an unfinished branch that has no shared history, when the names come from the two-dot diff's `-` side. | `plugins/my/skills/status/SKILL.md:50-56` | Medium |
| The no-shared-history rule is not written in the spec or the docstring. | `docs/plans/2026-10-12-status-skill-spec.md:106-116`; `plugins/my/bin/status-scan.py:27-29` | Low |

## Not Applicable

None.

## Reasoning

Both fixes hold. The script fix was checked on the repo that caused the first Warning, and there it now reports the right branch and hides the merged ones. The SKILL.md definition closes the base-name gap. The remaining Warning is in the skill's prose. The fix round's own fallback sends the model to a diff where most `-` lines are `main`'s work, and step 2 does not say which side to take names from. The approach is still right, and the gap is a one-phrase edit or a Risk entry, so the verdict is Mixed, not Problematic.

## Verdict

**Assessment:** Mixed
**Confidence:** Medium. Both prior Warnings were verified by code reading, the test suite and a real-repo run. The new Warning depends on how the model picks names, which was reasoned through and checked against the real diff, but not rehearsed.
**Recommendation:** Add "from the added (`+`) lines" to SKILL.md step 2, or record that gap in Risk 7. Optionally add the no-merge-base sentence to D4 and to the docstring. Then squash-merge. Neither item blocks the merge under the one-fix-round rule.
