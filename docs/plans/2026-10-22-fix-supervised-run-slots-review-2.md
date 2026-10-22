# Review: main..fix/supervised-run-slots

**Status:** review of main..fix/supervised-run-slots, 2026-10-22. Mixed: the fix round resolves every finding of the first round, but D18 now keeps a batch plan live while it waits for its batch, and `my:status` tells the user to "finish it or end it", where ending it removes the batch's shared worktree and skips every row gated behind it.

## Change Summary

`handoff-state.py` gains a `mode` field, a `start <slug> --supervised` form, one slot pool over every live run, and a cap that counts only auto runs. `live` and the `runs` block of `status-scan.py` gain a sixth column, `mode`. The handoff and status `SKILL.md` files make supervised code and review stages write, reuse and finish a state, and show supervised runs in `my:status`. The fix round adds decisions D17 to D19: the code stage sets `next=review` before Launch in both modes, and `resume` sends a supervised run that has its branch to the review. A supervised batch plan stays live after code stage step 4 until the batch's review finishes it. `my:status` names a supervised run for a `live runs` wait only when no auto run is live.

## Plan Alignment

The implementation matches the plan task for task. The fix round's changes match D17 to D19 in the spec and the new Risk lines in the plan.

- First-round soundness findings, all fixed:
  - The `resume` advice that led to a refused code stage now sends a run with a branch to the review (`plugins/my/skills/handoff/SKILL.md:367-378`).
  - The README `python3` line now names the supervised code and review stages (`plugins/my/skills/handoff/README.md:463-465`).
  - The exit-code docstring now lists `unknown mode` (`plugins/my/bin/handoff-state.py:136-137`).
- First-round code-review findings:
  - Fixed: 1 and 3 (D17, `SKILL.md:367-378`, `:911-914`), 2 (D18, `SKILL.md:903-910`, `:1060-1062`) and 8 (D19, `plugins/my/skills/status/SKILL.md:101-107`).
  - Now known limits in the plan's Risk section: 4, 5 and 7. Finding 6 falls under the existing "Slots above Max runs" Risk line.
- Code stage step 5 sets `next=review` in both modes. The auto bullet for step 5 now only names the window Launch opens (`SKILL.md:951`), so auto mode reads the same as before.
- Review stage step 8, sub-step 4, without auto, finishes the batch's other live plans (`SKILL.md:1060-1062`). It finds them through step 1's plan list (`:965-966`), as D18 says.
- I reran the suite (292 tests OK) and rehearsed the supervised flow against the branch's scripts in a scratch repo:
  - `start --supervised` printed slot 1;
  - `set branch= worktree=` and `set next=review` succeeded;
  - a second `start --supervised ... next=review` kept slot 1 and kept `branch`;
  - a second run took slot 2;
  - `set next=finished` dropped the first run from `live`.
- `markdownlint-cli2` reports 0 errors on the four edited skill and README files.
- Deviation: the spec's `resume` paragraph says "After step 2 of 'Resume'", but the SKILL runs the supervised check as step 1, before `check` (see Issues).
- Deviation: the "Judgement steps" Risk lines of the spec and the plan still say code stage step 4 is "finishing a batch run", which D18 reversed (see Issues).

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / Medium | (new in the fix round) Under D18, a supervised batch plan that ended at code stage step 4 stays live while it waits for the batch: `next=code`, `branch` and `worktree` set to the batch's shared worktree, empty `stopped`. When a queued row has `after=[<that slug>]`, `queue show` prints `waits <row> <slug>` (the `open_blocker` branch of `walk()`). The same happens for `live runs` when no auto run is live. `my:status` then says "Needs you: the queue waits for supervised run `<slug>`; finish it or end it with the steps in 'To end an abandoned run'". The user cannot finish this run: only the batch's review stage finishes it. Ending it runs `git worktree remove` on the shared batch worktree, and asks first only when `--force` is needed. It also writes `stopped="ended by the user"`, so rule 2 skips every row gated behind the plan ("blocker did not finish"). That is the outcome D18 was chosen to prevent. The new Risk line covers the held slot and the waiting exclusive rows, not this advice. | `plugins/my/skills/status/SKILL.md:101-107`; `plugins/my/skills/handoff/SKILL.md:403-414`, `:903-910`, `:1060-1062`; `plugins/my/bin/handoff-state.py` `walk()` (`open_blocker`) and docstring rule 2 | Needs design discussion, because D15 and D18 fix this behaviour. One option: when another live supervised run has the same `branch` (the `runs` block shows it), report the earlier run as "waits for its batch's review" rather than "Needs you", and never suggest ending it. |
| Suggestion / High | (new in the fix round, partly present before it) The spec and the plan are stale in two places. (a) The spec's `resume` paragraph, which the fix round rewrote, still says the supervised check runs "After step 2 of 'Resume'". The SKILL runs it as step 1, before `check`, and gives the reason. (b) The "Judgement steps are not tested by a command" Risk line in both the spec and the plan still lists "code stage step 4 … finishing a batch run", which D18 reversed. | `docs/plans/2026-10-22-supervised-run-slots-spec.md:165`, `:290-291`; plan Risk, "Judgement steps" bullet; `plugins/my/skills/handoff/SKILL.md:367-378`, `:903-910` | Say "before `check`, as step 1" in the spec. Change "finishing a batch run" to "leaving a batch run live (D18)" in both Risk lines. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| D17 closes the first round's Warning. `next=review` is written before Launch in both modes, so a printed-command fallback leaves the state at review. `resume` sends a run at `code` that has a branch to the review stage, whose start checks expect the branch and the worktree. | `plugins/my/skills/handoff/SKILL.md:367-378`, `:642-649`, `:911-914` | Strong |
| The script's real behaviour fits the new prose. A second `start --supervised ... next=review` overwrites `next`, keeps `slot` and `branch`, and refuses beside an auto run of the same slug. Checked by a scratch-repo rehearsal and the suite. | `plugins/my/bin/handoff-state.py:300-325`; `plugins/my/tests/test_handoff_state.py` (`test_supervised_start_again_keeps_the_slot_and_writes_the_fields`) | Strong |
| D18 removes the first round's premature finish. A gated row no longer starts before the batch's code is on `<base>`, because rule 3 waits until the blocker has a finished state with an empty `stopped`. | `plugins/my/skills/handoff/SKILL.md:903-910`, `:1060-1062`; `handoff-state.py` `walk()` rule 3 | Strong |
| D19 matches the queue logic. `live runs` is printed when any run is live, so naming the supervised run only when no auto run is live avoids advice that would not start the entry. The `runs` block's `mode` column gives `my:status` what it needs. | `plugins/my/skills/status/SKILL.md:101-107`; `handoff-state.py` `walk()` (`if entry.get("exclusive") and live`) | Moderate |
| The auto path is unchanged in effect. Step 5's `set next=review` moved from the auto bullets into the numbered step, and step 1's `set branch= worktree=` did the same. "Restarted stages" still points at step 1. | `plugins/my/skills/handoff/SKILL.md:418-426`, `:872-874`, `:911-914`, `:951` | Moderate |
| The first-round Suggestions are fixed in place, and the rest of the code review is either fixed by D17 to D19 or recorded as a known limit in Risk. | `plugins/my/skills/handoff/README.md:463-465`; `handoff-state.py:136-137`; plan Risk, last four bullets | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| D18 creates a supervised run that is live on purpose while it waits. The "Needs you" rule from D15 cannot tell it from a dropped run, and its "end it" advice is destructive for a batch plan. | `plugins/my/skills/status/SKILL.md:101-107`; `plugins/my/skills/handoff/SKILL.md:403-414` | Medium |
| The spec and plan texts that the review relies on still describe the pre-D18 batch behaviour and the old position of the `resume` check. | `docs/plans/2026-10-22-supervised-run-slots-spec.md:165`, `:290-291` | Low |

## Not Applicable

None.

## Needs Investigation

- **Does D18 hold in auto mode?** Code stage step 4 says "The run stays live: the batch's review stage finishes it after the merge (Review stage, step 8, sub-step 4)". That sentence reads as if it applies in both modes. But in auto mode, sub-step 4 is replaced by the auto sub-steps (`SKILL.md:1119-1143`). The auto sub-step 4 finishes only the run's own slug, so an auto batch plan would never be finished. This was so before the fix round too (auto step 4 already left the state at `next=code`). I could not tell whether auto runs ever form batches: an auto run writes one plan or uses a spec's Tasks. One of two things would settle it: a project rule or plan that gives an auto run a batch, or a sentence in step 4 that scopes "stays live" to supervised runs.

## Reasoning

On dimensions 1, 3 and 5, the fix round does what the first round asked. D17 and D19 fix the two wrong pieces of advice at their source. D18 fixes the premature finish at the state level rather than by adding a field. The suite and a CLI rehearsal confirm that the scripts behave as the new prose assumes. All caller sweeps were text searches (`grep`), because no symbol tool was available. The fix round removed or renamed no symbol: it moved two `set` lines into the numbered steps and edited prose. On dimension 4, D18 adds a new kind of live supervised run, one that waits on purpose. The D15 "Needs you" rule, written before D18, gives it advice that undoes D18. That is one Warning, which needs a design answer rather than a rework of the approach, so the verdict is Mixed.

## Verdict

**Assessment:** Mixed
**Confidence:** Medium. I traced the batch scenario through the queue code and the skill text, but I did not run it end to end, and it needs a batch of supervised plans plus a queued row gated behind one.
**Recommendation:** Bring the "Needs you" wording for a parked batch plan to the user as a design question, since D15 and D18 fix it. For example: do not name a supervised run that shares its `branch` with a later live run, or name the batch's review instead of "end it". Then fix the two stale lines in the spec and the plan, and merge. Under the one-fix-round rule, the Warning may also go into the plan's Risk section as a known limit if the user prefers.
