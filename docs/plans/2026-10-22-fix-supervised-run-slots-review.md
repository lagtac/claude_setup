# Review: main..fix/supervised-run-slots

**Status:** review of main..fix/supervised-run-slots, 2026-10-22. Mixed: the slot fix is sound and matches the plan, but the new `resume` refusal for a supervised run at `code` sends the user to a command whose start checks refuse once the branch exists.

## Change Summary

`handoff-state.py` gains a `mode` field (`auto` or `supervised`), a second form `start <slug> --supervised`, one slot pool over every live run, and a cap that counts only auto runs (in `start --max` and in rule 5 of `pull`). `live` and the `runs` block of `status-scan.py` gain a sixth column, `mode`. The handoff `SKILL.md`, its README, the status `SKILL.md` and the top-level README now say that supervised code and review stages write, reuse and finish a state file. They also show supervised runs in `my:status`.

## Plan Alignment

The implementation matches the plan in `docs/plans/2026-10-22-supervised-run-slots.md` task for task.

- Tasks 1 to 6: every file and edit in the plan's "Files to Modify/Create" table is in the diff. The decisions the plan adds (1 to 8) are all implemented. Examples: `parse_pairs` rejects a bad `mode` (`plugins/my/bin/handoff-state.py:237-239`), `start_args` rejects `mode=` and mixed flags (`:335-345`), `start_run` keeps the slot of a live supervised run (`:315-316`), and `status-scan.py` pads to six fields (`plugins/my/bin/status-scan.py:195`).
- The six commits carry `Task: 1` to `Task: 6` and the planned subjects. Task 6 has no scope, as the plan says.
- Task 7 (the rehearsal) leaves nothing in the repo. I reran its table in a scratch repo against the branch's `plugins/my/bin`. Every row matched: `s1`→1, `s2`→2, `a1`→3, `s1` again→1, `s3`→1 after `s1` finished, `queue show`→`none`, and the `runs` block listed `a1 3 code - - auto`, `s2 2 code - - supervised` and `s3 1 code - - supervised`. A second auto start at `--max 1` refused with the unchanged auto wording.
- The mutation proofs of Task 2 step 6 and Task 3 step 5 also leave no trace. I reran all four breaks on a scratch copy of `plugins/my`, and each guard test failed. The breaks were: a missing `mode` read as supervised; rule 4 counting only auto runs; rule 3 hiding supervised blockers; and the rule 6 refusal raised with `exists=False`.
- The text checks of Tasks 5 and 6 pass: no `A supervised run has no state file`, no `frees its slot`, `refill their own slots`, `live auto run` or `free slot`, and a lint count of 0 for all four edited `.md` files.
- One sweep hit the plan missed: `plugins/my/skills/handoff/README.md:463-464` (see Issues).

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / Medium | `resume` refuses a supervised run with `run /my:handoff <stage> <doc>`, where `<stage>` is the state's `next`. For a supervised run at `next=code` whose window closed after code stage step 1, `branch` is set and the branch and `.claude/worktrees/<slug>` exist. The code-stage start checks then refuse ("no branch `*/<slug>`", "no directory `.claude/worktrees/<slug>`"), unless the plan names the worktree. So the advice this branch adds leads to a failed start check. The Risk section covers only a dropped run that "stays live" until it is ended, not this message. | `plugins/my/skills/handoff/SKILL.md:367-372`; `:627-629`; exception at `:630-635` | Needs design discussion, because D10 fixes the wording. One option: when `next` is `code` and `branch` is set, name the way forward that works (finish the tasks in the worktree, then `/my:handoff review <doc>`, or end the run). |
| Suggestion / High | "What you need" still says `python3` is needed "for auto mode". Under D2, every supervised code and review stage, in every project, now runs `handoff-lock.py` and `handoff-state.py` as a start check. A supervised hand-off that used to need no script now fails its start check without `python3`. The plan's sweep did not list this line. | `plugins/my/skills/handoff/README.md:463-464` | Say that `python3` is needed for the code and review stages in both modes. |
| Suggestion / High | The exit-code block lists "unknown field, unknown next" for exit 2, but not the new `unknown mode`, which also exits 2 (`parse_pairs`). | `plugins/my/bin/handoff-state.py:136`; `:237-239` | Add "unknown mode" to the exit 2 line. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Treats the root cause: a supervised run now has a state file, so `start_run` sees it, and the slot search covers every live run of both modes | `plugins/my/bin/handoff-state.py:322-324`; `plugins/my/skills/handoff/SKILL.md:645-659` | Strong |
| The cap counts only auto runs in both places, and an unreadable state still counts, through one predicate | `plugins/my/bin/handoff-state.py:295-297`, `:317-321`, `:830` | Strong |
| Every refusal about the slug's own run raises `exists=True`, so `pull` skips the row and goes on rather than stopping the walk (D5, rule 6) | `plugins/my/bin/handoff-state.py:308-314`, `:842-846`; test at `plugins/my/tests/test_handoff_state.py:838-844` | Strong |
| A refusal writes nothing, an unreadable own state is left alone, and a fresh supervised state drops the old `branch` and `stopped` | `plugins/my/bin/handoff-state.py:306-316`, `:324`; tests at `plugins/my/tests/test_handoff_state.py:737-774` | Strong |
| The auto output and refusal wording are kept byte for byte; old states without `mode` read as auto everywhere | `plugins/my/bin/handoff-state.py:282`, `:310`, `:320`; `plugins/my/bin/status-scan.py:210-213`; guard test at `plugins/my/tests/test_handoff_state.py:688-694` | Strong |
| Concurrency: four locked supervised starts get slots 1 to 4 | `plugins/my/tests/test_handoff_state.py:776-786` | Moderate |
| The four prose steps that the Risk section leaves to this review: start check 5 runs before `start` and names the supervised case (`SKILL.md:698-702`). Code stage step 4 stops the stage's servers, sets `finished`, prints the queue line, then signals (`:897-905`). The `my:status` "Needs you" bullet matches `queue show`'s `waits` output (`plugins/my/skills/status/SKILL.md:101-105`). `resume` checks the mode before `check`, so a mismatch cannot hide the refusal (`SKILL.md:367-372`). | as cited | Moderate (the `resume` wording is the Warning above) |
| Moving the `set branch= worktree=` line into code stage step 1 for both modes keeps "Restarted stages" true: it still points at step 1 | `plugins/my/skills/handoff/SKILL.md:416-417`, `:866-868` | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| The new `resume` advice for a supervised run at `code` with a branch points to a stage whose start checks refuse | `plugins/my/skills/handoff/SKILL.md:367-372`, `:627-629` | Medium |
| D2 now makes supervised hand-offs depend on `python3` and the `main` lock in every project, and the README's requirements line was not updated | `plugins/my/skills/handoff/README.md:463-464` | Low |

## Not Applicable

None.

## Reasoning

On dimensions 1, 3 and 4, the script layer removes the root cause ("a supervised run has no state file"). It does so at the right level, with a single `is_auto` predicate and no compatibility paths. Every reader of the changed `live` and `runs` outputs is handled. I verified this with text searches (no symbol tool was available) over `plugins/`, `global/`, `README.md` and `CLAUDE.md`. The only readers are `status-scan.py`, `my:status` and the two handoff `SKILL.md` lines. The suites pass (77 and 292), the rehearsal matches, and each guard test is proven able to fail. The one Warning is in new prose: the `resume` refusal can send a user to a command that refuses. That is a fix to one message, not a flaw in the approach, so the verdict is Mixed rather than Problematic.

## Verdict

**Assessment:** Mixed
**Confidence:** High. The script behaviour was checked by running it: the suites, the rehearsal and the mutation breaks. The Warning was checked against the start-check text it contradicts.
**Recommendation:** Bring the `resume` wording to the user as a design question, because D10 fixes that copy. Then fix the two Suggestions (the README's `python3` line and the exit-code docstring) in the fix round, and merge.
