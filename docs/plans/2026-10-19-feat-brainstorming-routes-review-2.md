# Review: main..feat/brainstorming-routes

**Status:** review of main..feat/brainstorming-routes, 2026-10-19. Mixed: the fix round answers all three first-round findings and the code review's ten, but the green rehearsal ran on the rule text from before the fix round, and the new roadmap row 73 can collide with a row another session adds on `main`.

## Change Summary

This is the re-review after one fix round, of the range `main..feat/brainstorming-routes` (merge-base diff against local `main`). The branch replaces `my`'s size table in `global/methods/my.md` with a "Pick the route" section (spike, bounded, architectural, architectural with plan, bug), and renames the sizes in `docs-layout.md`, four skills, the `my` README, zitamu's local file and the open roadmap rows. The fix round adds a fourth bug-escalation case, a spike-worktree removal step, an own-slug rule for a spike before a spec, a `spike` value in roadmap rule 11, the `spike` kind in `clean-plans`, the "without a plan" wording in the hand-off README, and Risk notes in the plan for the five gates, row 73 and the checker change.

All caller sweeps in this review were plain text searches (`grep`), because this reviewer has no symbol-reference tool.

## Plan Alignment

The implementation matches the plan. Tasks 1 to 5 were checked in the first round. The fix round's edits each match a line in the plan's **Risk** section ("Review stage, 2026-10-19: the user's answers to five gates", "Known limit: `my:status` lists spike branches", "The rehearsal checker changed after the red run"), and the spec's D6, D7, D9 and Files table were edited to say the same (`docs/plans/2026-10-18-brainstorming-routes-spec.md:125-132`, `:140-157`, `:184-185`).

First-round findings, all addressed:

- The hand-off README now says "with a plan" or "without a plan" (`plugins/my/skills/handoff/README.md:54`, `:225`, `:228`, `:275-276`). A grep for "architectural change" finds no unqualified use outside `my.md`'s definition.
- `global/methods/my.md:24-25` now reads "A bug states no route, even when its fix may touch the risk line". This settles which sentence wins.
- The checker change is recorded in the plan's Risk section.

Deviations:

- **(missing from the plan)** The plan says the green run passed 12 of 12 (Task 1, step 12, and Testing Strategy 2). That run used the rule text from before the fix round. The plan does not say this. See the Issues table.
- The spec's D1 still lacks the risk-line timing sentence that `my.md:23-24` carries. The first round listed this as an approved deviation recorded in the plan's Risk section, so it is not a finding.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / Medium | **New.** The green rehearsal ran on the rule text from before the fix round, and the plan does not say so. I compared the `green3` fixture's `.claude/method/my.md` with the branch head's `global/methods/my.md`, ignoring line wrapping. They differ in seven places, all from the fix round. Two touch rehearsed behaviour. (1) The Superpowers Integration lead lost "once the route below is picked, the corresponding skill must run first". It now says "'Pick the route' says when the route line comes." This is on the `deleted_at` timing path, which already failed 2 of 6 runs before the timing sentence was added. (2) The Bounded bullet lost "A bug still starts with `superpowers:systematic-debugging`". The Bug bullet and the trigger table still say it. Both edits most likely keep the result. But the 12-of-12 count that the `done` mark will cite was measured on other text. | rehearsal `green3/fx-deleted_at-2/.claude/method/my.md` against `global/methods/my.md:12`, `:70-80` | Add one Risk line to the plan: green ran before the fix round, and these are the fix round's changes to the rehearsed text. Do not make a second fix round. |
| Warning / Medium | **New.** Row 73 can merge as a duplicate number with no conflict. Committed `main` says `Next number: 71`. The main checkout has uncommitted rows 71 and 72 and `Next number: 73`. The branch adds row 73 and sets `74`. If another session on `main` adds its own row 73 before the merge, it also writes `74`. Both sides then make the same edit to that line, so git raises no conflict, and two different rows 73 land. The plan's Risk covers conflicts on the same rows, not a reused number. This is not a code change. | `ROADMAP.md:13`, `:440` on the branch; `/home/dchris/projects/claude-setup/ROADMAP.md:13`, `:249`, `:453` (uncommitted) | At the squash-merge, check that no row 73 exists on `main`. If one does, renumber this row and raise the next number. A Risk line in the plan is enough to carry the check. |
| Suggestion / High | **New.** Rule 11 says a row routed to a spike gets `spike` "in the edit that links the spike file". But no rule defines that edit. The decision table has no row for a spike file that has landed, and rules 3 to 6 do not say which status icon such a row gets. Rule 2 says not to edit until the situation matches a row, so a session falls back to "ask the user". This is safe, but the rule names an edit that does not exist. | `plugins/my/skills/roadmap-management/SKILL.md:176`, `:43-61` (decision table), `:77-134` (rules 3 to 6) | Record it in Risk, or later give the decision table a row for "spike file landed" that names the status. |
| Suggestion / High | **New, a gap left by the fix to code-review finding 1.** The own-slug sentence sits only in the paragraph about a spike that runs inside an architectural route. But every spike leaves a `spike/<slug>` branch that is never deleted. A standalone spike whose follow-up ("Keeping the spike's code is a new task") gets a spec with the same slug is refused by `my:handoff`, because `git branch --list '*/<slug>'` matches `spike/<slug>`. The refusal is loud and easy to fix by renaming, so the harm is small. | `global/methods/my.md:47-49`, `:63-67`; `plugins/my/skills/handoff/SKILL.md:620-622`, `:487` | Record it in Risk. Moving the own-slug sentence to the branch bullet (`my.md:47`) would cover both cases. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Every first-round finding is fixed | `plugins/my/skills/handoff/README.md:54`, `:225-229`, `:275-276`; `global/methods/my.md:24-25`; plan Risk, "The rehearsal checker changed after the red run" | Strong |
| The fix round's claims about other tools are true | `global/git-hooks/pre-commit:12-13` extracts hashes only from spans in backticks, so "catches such a hash only when it is written in backticks" (`my.md:53-54`) is exact. `plugins/my/skills/handoff/SKILL.md:620-622` refuses a branch `*/<slug>` and a worktree `.claude/worktrees/<slug>`, as `my.md:65-67` says. | Strong |
| No orphaned references | grep on the branch head for `Small`, `Medium`, `Large` as words, and for "size table", "size the process", "size not set", "sizes its work", "by size", "pick a size", across `global/`, `plugins/` and `projects/`. The only hits are the README's mapping (`plugins/my/README.md:93-94`) and the confidence labels in the two reviewer prompts. | Strong |
| `clean-plans` learns `spike` in all three places | `plugins/my/skills/clean-plans/SKILL.md:20`, `:58-61`, `:84`, `:93`. No other file lists document kinds (a grep for `action-plan` outside this skill and `docs-layout.md` finds none). | Strong |
| The fourth bug case keeps the old Small limit and agrees with Bounded | `global/methods/my.md:81-93` against `:70-71` ("one or two files") | Moderate |
| Tests pass on the branch head | `plugins/kit`: OK; `plugins/my`: OK (both suites run in this review) | Moderate |
| No branch commit IDs in docs | Each `main..HEAD` short hash searched in `docs/` and `ROADMAP.md`: none found | Moderate |
| The rehearsal red-to-green gap (first round) | The first round confirmed it with the current checker. **Caveat:** green ran on the text from before the fix round (Issues, row 1). | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| The rehearsal evidence predates the fix round's edits to the rehearsed text | `global/methods/my.md:12`, `:74` against the `green3` fixture | Medium |
| A reused roadmap number can merge silently | `ROADMAP.md:13`, `:440` | Medium |
| Rule 11's spike edit has no lifecycle rule behind it | `plugins/my/skills/roadmap-management/SKILL.md:176` | Low |
| The own-slug rule covers only a spike before a spec | `global/methods/my.md:63-67` | Low |

## Not Applicable

None.

## Reasoning

The approach is unchanged from the first round and still right. One route section replaces the size table, every live reference is renamed, and the fix round closes each gap that the two first-round reviews found. The claims it makes about the hook and the hand-off checks hold against the code. The two Warnings are not flaws in the rules. One is evidence that is now a step out of date. The other is a merge-time hazard in the roadmap. Each needs a Risk line or a check, not a rework. With Warnings and no Critical, the verdict is Mixed.

## Verdict

**Assessment:** Mixed
**Confidence:** High — I checked each fix against the files on the branch head, the hook and the hand-off checks, and compared the rehearsal fixture's text directly. Whether the fix-round wording changes rehearsal outcomes is the one thing I did not test.
**Recommendation:** This re-review is final under "One fix round per review", and it has no Critical finding. Add one Risk line to the plan for each of the four findings. Then, at the squash-merge, check that row 73 is still free on `main` (renumber it if not), and merge.
