# Review: main..feat/soundness-plan-only

**Status:** review of main..feat/soundness-plan-only, 2026-09-30. Mixed: the fix round addressed both earlier findings and the code review's fixable ones. But the deferred fold in the review stage rewrites the hashes of every commit after the spec commit, not only this feature's squash commit, so other features' `done` marks can end up citing commits that are no longer on `main`.

## Change Summary

The branch adds a `--plan-only` token to `my:soundness-review`. The token forces a plan review, skips the diff capture and the dirty-tree question, and stops on mixed arguments. It also rewrites the `my:handoff` plan stage: review the uncommitted plan, add the index row, check for foreign hunks, make one path-limited commit, and fold spec fixups only on a clean base. The fix round adds more: the review stage now folds deferred fixups after the squash-merge and before the `done` marks. Fixups are now found by subject. The post-commit check allows a path with no change. The Risk section gets three known limits. The docs (handoff README, handoff spec D9, plan-only spec D4 and Trade-offs, `global/CLAUDE.md`, `README.md`, `ROADMAP.md`) are updated to match.

## Plan Alignment

The first three tasks match the plan. At the branch head, the text in Tasks 3 and 4 differs from the plan's word-for-word blocks: plan stage steps 5 to 9, the README steps 5 and 7, handoff spec D9 steps 6 and 8, and the review-stage paragraph. These are fix-round changes. They answer the earlier review and the code review. The review-stage fold is documented in the plan's Global Constraints (`docs/plans/2026-09-30-soundness-plan-only.md:41-43`), and the leftover limits are in Risk (`:828-840`). So they are not findings.

Deviations:

- `docs/plans/2026-09-30-soundness-plan-only-spec.md:54-56` and `:157-158`: the spec still says the review stage's text changes in one place only. The plan's Global Constraints was amended for the review-stage fold, but the spec's Out of scope and D5 were not. The spec's D4 step 8 (`:130-133`) and Trade-offs (`:183-186`) do describe the new fold. So the spec contradicts itself. This is Suggestion row 1 below.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / Medium | The review-stage fold runs `rebase -i --autosquash <spec commit>^` on `<base>`. It gives new hashes to every commit after the spec commit, not only this feature's squash commit. The text's reason ("so it runs before the `done` marks cite that commit") covers only this feature's own hash. Fixups are deferred only when `main` is busy, which means other sessions are active. So other features are likely to squash-merge during this feature's code stage. Their `done` marks cite their squash hashes, and so can `ROADMAP.md` rows. After the fold, those citations name commits that are no longer on `main`. That breaks "Cite only commits on `main`", which zitamu's pre-push hook enforces. The pre-rebase check (`global/CLAUDE.md:136`) looks only at worktree branches, not at hash citations. The hazard is partly inherited, because the global rule already allows a fold after other branches merge. What this branch adds is that the deferred fold is now the normal path on a busy `main`, and the text claims the citations are safe. | `plugins/my/skills/handoff/SKILL.md:315-321`; `docs/plans/2026-09-30-soundness-plan-only-spec.md:183-186`; a `done` mark that cites a hash: `docs/plans/2026-09-21-handoff-spec.md:3`; `global/CLAUDE.md:128`, `:136`, `:139` | This re-review is final and the finding is not Critical, so record it in the plan's **Risk** as a known limit. Suggested wording: "a deferred fold also rewrites the hashes of other features merged after the spec commit, so their `done` marks go stale". A later change could have review stage step 8.3 check whether any commit in `<spec commit>..<base>` is cited in `docs/` or `ROADMAP.md`, and treat that as a gate. |
| Suggestion / High | The fold change is recorded in some places and not others. The spec's Out of scope and D5 still say the review stage's text changes in one place only, while its D4 step 8 and Trade-offs describe the review-stage fold. In the handoff spec, the D9 review-stage paragraph changed without a dated marker, while the plan-stage paragraph has one. | `docs/plans/2026-09-30-soundness-plan-only-spec.md:54-56`, `:157-158` vs `:130-133`; `docs/plans/2026-09-21-handoff-spec.md:267` vs `:307-316` | Amend Out of scope to name the review-stage fold (same wording as the plan's Global Constraints `:41-43`). Add "(Changed 2026-09-30, see the soundness plan-only spec.)" to the handoff spec's review-stage paragraph. |
| Suggestion / High | Two unclear sentences in the fold text. In plan stage step 8, the fix round put two sentences between "a commit whose subject is…" and "If one does", so "If one does" no longer points at anything. Line 198 also breaks after "subject." for no reason. In the review stage, the gate message says "wait for a clean `<base>`" even when the pre-rebase check failed (another worktree sits on top of the target) and `<base>` is already clean. That points the user at the wrong cause. | `plugins/my/skills/handoff/SKILL.md:195-202`, `:318-320` | Start with "If such a commit exists and `git status --porcelain` prints nothing…". Make the gate message name the check that failed, for example `<name>: merged; fixups <hashes> wait (<base> not clean \| worktree <path> on top)`. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Earlier finding 1 (plans-index row) is fixed in all four places. The stage adds its row before the hunk check, so step 6 checks the row and step 7 commits it | `plugins/my/skills/handoff/SKILL.md:178-179`; `plugins/my/skills/handoff/README.md:100`; `docs/plans/2026-09-21-handoff-spec.md:278`; `docs/plans/2026-09-30-soundness-plan-only-spec.md:115-116` | Strong |
| Earlier finding 2 ("never read") is fixed. The sentence now says that no diff is captured and that grounding still reads the tree, which matches the Risk bullet | `plugins/my/skills/soundness-review/SKILL.md:117`; `docs/plans/2026-09-30-soundness-plan-only.md:795-797` | Strong |
| Fixups are now found correctly. The search matches `fixup! <spec subject>`, which is what `git commit --fixup` writes, and it is limited to commits after the spec commit | `plugins/my/skills/handoff/SKILL.md:195-201` | Strong |
| This feature's own `done` marks stay valid. The steps run merge, then worktree removal, then fold, then `done` marks citing the hash after the fold. Removing the worktree first keeps the feature's own branch from failing the pre-rebase check | `plugins/my/skills/handoff/SKILL.md:310-324` | Strong |
| The post-commit check no longer fails a correct commit (a path with no change), and it says what to do when it does fail | `plugins/my/skills/handoff/SKILL.md:191-194` | Strong |
| The `--plan-only` design is unchanged: fully gated behind the token, and no caller that omits the token changes behavior | `plugins/my/skills/soundness-review/SKILL.md:34`, `:46-55`, `:69`, `:117` | Strong |
| The step references still hold after the fix round: the review stage cites plan stage step 4 for the finding test, and plan step 8 and review step 8 cite each other | `plugins/my/skills/handoff/SKILL.md:206`, `:299`, `:315` | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| The deferred fold rewrites other features' squash hashes that `done` marks cite | `plugins/my/skills/handoff/SKILL.md:315-317`; `docs/plans/2026-09-21-handoff-spec.md:3` | Medium |
| The spec's Out of scope and D5 contradict its own D4 step 8 on whether the review stage changes | `docs/plans/2026-09-30-soundness-plan-only-spec.md:54-56`, `:130-133` | Low |
| Fold text: a dangling "If one does", and a gate message that names the wrong cause | `plugins/my/skills/handoff/SKILL.md:201`, `:320` | Low |

## Not Applicable

None. Every dimension applied. The Risk & blast radius sweep was a text search (`grep -rn`), because this environment has no symbol tool and none applies to Markdown prompt files. It found no stale reference to the old step numbers or the old stop message outside dated history.

## Reasoning

The fix round closed the two earlier findings and most of the code review's findings, and the `--plan-only` design is still narrow and gated. The new review-stage fold keeps this feature's own `done` marks valid. But its stated reason ignores that the same rebase gives new hashes to every other commit after the spec commit. On the busy `main` that causes the deferral, those commits are likely to include other features' cited squash commits. That is a real gap with limited reach, not a reason to rework: it applies only when fixups were deferred and another feature merged in between. By the one-fix-round rule, it belongs in Risk. The other two rows are wording and consistency fixes.

## Verdict

**Assessment:** Mixed
**Confidence:** Medium. Every changed file was read in full. The hash-rewrite effect follows from how `rebase` works and from the repo's `done`-mark convention. How often it happens depends on how often features merge between a deferred spec commit and its fold, which only real parallel use shows.
**Recommendation:** Add the deferred-fold hash-rewrite as a known limit in the plan's **Risk**. Optionally apply the two wording fixes (the spec's Out of scope and D5 plus the handoff spec marker; the step 8 "If one does" and the gate message). Then merge.

What happened to the earlier findings:

- **Earlier soundness review.** The plans-index finding (Warning) is fixed at `plugins/my/skills/handoff/SKILL.md:178-179`, `README.md:100`, handoff spec `:278` and plan-only spec `:115-116`. The "never read" wording (Suggestion) is fixed at `plugins/my/skills/soundness-review/SKILL.md:117`.
- **Code review.** Fixed: 1 (the fold moves before the `done` marks), 2 (the review stage now owns the fold), 3 (index row), 4 (the post-commit check allows a path with no change and has a stop), 5 (fixups found by subject within `<spec commit>..<base>`) and 8 (wording). Half fixed: 6. The signal now names the review only "when step 3 wrote one", and the case of a second review went to Risk. Moved to Risk: 7 and 9. The code-review report's own status line still says "none fixed yet" (`docs/plans/2026-09-30-soundness-plan-only-code-review.md:3-4`). Update it when the `done` marks are set.
