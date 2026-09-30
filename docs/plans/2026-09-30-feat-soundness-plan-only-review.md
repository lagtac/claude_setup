# Review: main..feat/soundness-plan-only

**Status:** review of main..feat/soundness-plan-only, 2026-09-30. Mixed: the approach is sound and matches the plan and spec, but the rewritten handoff plan stage never says when the plans-index row is written, so step 6 can check the index before the row exists.

## Change Summary

The branch adds a `--plan-only` token to `my:soundness-review`. The token forces `plan-review` mode, skips the diff capture and the dirty-tree question, and stops on mixed arguments (range, missing plan, spec). It also rewrites the `my:handoff` plan stage: review the uncommitted plan first, check the stage's paths for foreign hunks, make one path-limited commit, and fold spec fixups only on a clean base. Five documents (handoff README, handoff spec D9, `global/CLAUDE.md`, `README.md`, `ROADMAP.md`) are updated to match, and the plan's Risk section gets a note from the code stage.

## Plan Alignment

The implementation matches the plan task by task. Task 2's text lands in `plugins/my/skills/soundness-review/SKILL.md:13`, `:34`, `:46-55`, `:69`, `:117` and `:288-296`. Task 3's plan-stage steps 1 to 9 land word for word in `plugins/my/skills/handoff/SKILL.md:152-203`, and the review-stage reference moves to step 4 at `:291`. Task 4's edits land in the handoff spec, `global/CLAUDE.md:58`, `README.md:65-68` and `ROADMAP.md:66-68`. The text sweep for `plan review would ask` and `Plan stage, step` finds no stale reference outside dated history (`docs/plans/2026-09-21-handoff.md:357` is the old plan and stays as a record).

Deviations, all documented in the plan's Risk section and so not findings:

- `plugins/my/skills/soundness-review/SKILL.md:46`: the D3 paragraph adds "A stop prints its message word for word", beyond the plan's Task 2 step 1 text. Documented in the Risk bullet "The headless tests depend on the model's reading" (`docs/plans/2026-09-30-soundness-plan-only.md:814-824`).
- The same Risk bullet relaxes the plan's test validity rule from `denials: 0` (plan, "How tests run") to "no `Write` or `Agent` call was denied", and adds an `r-missing` run. This changes how the tests were judged, not what shipped.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / Medium | The plan stage names the plans index as one of its committed paths, but no step writes the index row. The old step 3 said "following the project's rules for docs commits and the plans index"; new step 7 drops "and the plans index". Step 6 checks the index before step 7, and step 9 ("Finish the project's other docs steps") runs after the commit. A session that follows the steps in order either commits without the row or adds it in step 9, where it stays uncommitted on `<base>`. That is the state the rewrite exists to avoid. The spec's D4 has the same gap, so this is inherited, not a deviation. | `plugins/my/skills/handoff/SKILL.md:176-190`, `:199`; old text on `main` at `plugins/my/skills/handoff/SKILL.md:162-163`; `docs/plans/2026-09-30-soundness-plan-only-spec.md:114-121` | Say in step 6 (or a line before it) that the stage first adds its own plans-index row when the project's rules require one, so step 6 checks it and step 7 commits it. Mirror the sentence in the handoff README step 5 and handoff spec D9 step 6. |
| Suggestion / High | Step 1a says "The working tree is never read". The plan-review reviewer does read the working tree when it grounds the plan, which the plan's Risk bullet "Grounding reads other sessions' edits" states. What the skill skips is capturing the tree's changes. | `plugins/my/skills/soundness-review/SKILL.md:117`; `docs/plans/2026-09-30-soundness-plan-only.md:792-794` | Reword to "The working tree's changes are never captured, so a dirty tree changes nothing", which is the spec's own wording in D2. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Behavior without the token is unchanged: the new token row, the D3 table, the step 1 early exit and the step 1a override are all gated on `PLAN_ONLY` | `plugins/my/skills/soundness-review/SKILL.md:34`, `:46`, `:69`, `:117` | Strong |
| The early exit in step 1 keeps `WORK_DIR` (needed by the plan copy in step 2) and skips the size guard, so `wc -l < "$PAYLOAD"` never runs on a missing file | `plugins/my/skills/soundness-review/SKILL.md:69`, `:108`, `:157` | Strong |
| Root cause is treated: the stage no longer needs a clean tree for the review, and the review-before-commit order removes the fixup that would have needed a rebase on a clean tree | `plugins/my/skills/handoff/SKILL.md:163-198` | Strong |
| The path-limited commit (`git commit -- <paths>`) leaves other sessions' staged files alone, and step 7 checks the result with `git show --stat` | `plugins/my/skills/handoff/SKILL.md:185-190` | Strong |
| Step 3 takes the review path from the printed pointer line, which covers the collision rule's `-2` suffix | `plugins/my/skills/handoff/SKILL.md:166-168`; `plugins/my/skills/soundness-review/SKILL.md:180`, `:248` | Moderate |
| Cross-references follow the renumbering: step 7 is the commit (`:155`), step 8 is the fold (`:200`), the review stage cites step 4 for the finding test (`:291`), and the handoff spec says "plan stage step 7 commits it" | `plugins/my/skills/handoff/SKILL.md:155`, `:200`, `:291`; `docs/plans/2026-09-21-handoff-spec.md:262` | Strong |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| No step writes the plans-index row that step 6 checks and step 7 commits | `plugins/my/skills/handoff/SKILL.md:176-199` | Medium |
| The mixed-argument behavior depends on the model following prose tables; the code stage found the old skill already guessing `--plan-only`, and the model paraphrased a stop once. The "word for word" clause is the only guard. Documented in Risk. | `plugins/my/skills/soundness-review/SKILL.md:46`; `docs/plans/2026-09-30-soundness-plan-only.md:814-824` | Low |

## Not Applicable

None. Risk & blast radius applied: the step renumbering is a cross-file reference change. A text sweep with `grep -rn` (no symbol tool applies to Markdown prompt files) found no stale reference to the old step numbers, the old stop message or the removed "busy `main`" limit outside dated history, and handoff spec D3 still holds the finding test that D9 step 4 cites (`docs/plans/2026-09-21-handoff-spec.md:96-106`).

## Reasoning

The token design is narrow and fully gated, so the existing caller paths (routing lines, the review stage's range-based call) are untouched, and the step 1 early exit correctly keeps the one piece of step 1 that later steps need. The handoff rewrite fixes the stated problem at its cause, and it follows the spec's D4 closely, including the renumbered references. The one real gap is that the plans-index row, which the stage commits, has no step that writes it before the check. That can leave the index uncommitted on a busy base. It is a wording fix, not a rework, so the verdict is Mixed rather than Problematic.

## Verdict

**Assessment:** Mixed
**Confidence:** Medium: every changed file was read in full and the references were swept by text search, but the plans-index gap depends on how a session reads "the project's other docs steps", which only a real plan-stage run in a project with an index (such as zitamu) would show.
**Recommendation:** Add one sentence to handoff plan stage step 6 (and its copies in the handoff README and handoff spec D9) saying the stage writes its plans-index row, when the project has one, before the hunk check. Reword the "never read" sentence in soundness-review step 1a. Then merge.
