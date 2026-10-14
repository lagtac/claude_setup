# Review: main..feat/roadmap-auto-runs

**Status:** review of main..feat/roadmap-auto-runs, 2026-10-14. Sound: the fix round is correct and fixes the first round's findings, and only two Suggestions remain, both about how the docs describe the fix (the "exclusive row rerun by hand" case is closed only when a `pull` runs between the finish and the rerun). Answered by the plan's Risk section (the rerun-by-hand gap) and the first code review's status line (finding 8 fixed in part).

## Change Summary

This is the final re-review after one fix round. The branch adds the queue of roadmap rows for auto runs: `handoff-state.py queue add/drop/show`, `pull --max <n>`, the refill that a finishing auto run starts, and the `queue` block in `status-scan.py`. The fix round changes only `plugins/my/bin/handoff-state.py` and its tests, plus the docs commit (the two first-round reports, and notes in the spec and plan). The code changes are:

- `in_loop`, which labels a new entry that only waits behind a loop `behind a gate cycle`;
- `not_fresh`, a fresh-start check in `pull` that mirrors D2;
- `functools.cache` on `common_dir`;
- one read of each blocker's state per walk step;
- a step at the start of `pull` that drops `started` entries whose run finished.

Method: I read the fix-round diff, the review map, both first-round reports, the queue code of `handoff-state.py` in full (lines 130–330 and 490–900), the "From roadmap rows", "Refill", "Restarted stages" and "Start checks" sections of `handoff/SKILL.md`, the plan copy's Review Focus and Risk sections, the fix-round docs commit, and the `status-scan.py` part of the payload. I had no symbol-reference tool, so every caller sweep was a text search (`grep -rn` for `common_dir`, `chdir`, `os.environ`, `importlib`, `handoff-state`, and the skip-reason strings). The `my` suite ran 203 tests, all OK. Three mutation runs on scratch copies each removed one fix. Each turned its new test red: `test_add_labels_a_row_behind_a_gate_cycle`, the three subtests of `test_rule6_a_row_that_cannot_start_fresh_is_skipped_and_the_walk_goes_on`, and `test_pull_drops_a_finished_started_entry_before_its_walk`.

## Plan Alignment

The fix round matches what the docs commit says it does, and that commit records the user's choices in the spec (`docs/plans/2026-10-13-roadmap-auto-runs-spec.md:188-190`, `:214-218`, `:243-250`) and in the plan's Risk section (`docs/plans/2026-10-13-roadmap-auto-runs.md:1066-1094`). First-round findings, one by one:

- **Soundness review, Warning (fresh start not rechecked):** fixed. `not_fresh` (`plugins/my/bin/handoff-state.py:750-761`) runs D2's three checks: the anchored plan file, `git branch --list '*/<slug>'`, and `.claude/worktrees/<slug>`. It runs from the main checkout's root, so it gives the same answer from a worktree. It applies to every stage, which matches the D2 row in `plugins/my/skills/handoff/SKILL.md:460`. It runs only when the slug has no live run (`:782`), so "a run for `<slug>` exists" still wins, in D2's order. The reason text, `<plan, branch or worktree> for <slug> exists`, is D2's text word for word. A probe showed the expected chain: `a` is skipped as `plan for a exists`, `b` (after `a`) as `blocker a did not finish`, and `c` starts.
- **Soundness review, `my:status` gap and the Decision 3 wording:** the first is in Risk as a known limit (`docs/plans/2026-10-13-roadmap-auto-runs.md:1076-1079`). The second is answered by the docstring at `handoff-state.py:74-75`.
- **Code review 1 (wrong `gate cycle` label):** fixed. `in_loop` (`:595-608`) searches only the stuck entries. Every member of a loop is stuck, so this is enough. The slugs are unique by then, so `stuck_entries.index(new[i])` (`:660`) cannot match the wrong entry, even though it compares dicts by equality. An entry behind a loop is still left out of the queue, now with an accurate label. That is the same end state that `pull`'s rule 2 would reach, so leaving it out is reasonable.
- **Code review 2 (an old exclusive entry blocks a hand rerun):** fixed on the normal path, with a narrow window left. See Issues.
- **Code reviews 3 to 6:** recorded in Risk (`docs/plans/2026-10-13-roadmap-auto-runs.md:1072-1094`). The fix round does not touch them and does not make them worse. One exception: rule 6 now has a second skip reason that `queue show` does not mirror. The Risk entry at `docs/plans/2026-10-13-roadmap-auto-runs.md:1072-1075` already names "a plan, branch or worktree", so that is covered.
- **Code review 7 (many `git` calls under lock `main`):** fixed. `common_dir` is cached (`:170-172`), so `run_state`, `live_states` and `queue_path` no longer start `git`. `live_states()` is still called up to three times per walk step (`:729`, `:776`, `:276`), but each call is now only a folder listing.
- **Code review 8 (duplicate cap check and blocker reads):** partly done. The blocker states are now read once per step (`:712`, reused at `:724`). The duplicate cap check stays, and the comment at `:777-778` gives the reason. The reason holds: without the early check, at the cap an entry with a stale branch would be skipped by rule 6 rather than the walk stopping by rule 5.

The prompt's three questions:

- **Is caching `common_dir` safe?** Yes. The script never calls `os.chdir` and never changes the environment. Every caller starts it as a new subprocess: all tests through `run()` (`plugins/my/tests/test_handoff_state.py:52`), and `status-scan.py:192`, `:222`. No test or script imports the module in-process. The cache lives for one process, which runs from one directory, and `functools.cache` does not cache a `GitError`.
- **Does the drop before `walk` change order or blocker rules?** No. The kept entries keep their order. A finished slug is not in `live_states()`, so rule 4 (`:729-734`) could never fire on it. Rule 2 still reads the blocker's state file when its entry is gone. A finished run with an empty `stopped` passes rules 2 and 3, and one with a stop line fails rule 2, as before. `before` (`:768`) is taken before the drop, so the drop is written. `status-scan.py`'s `queue` block lists only `waiting` and `skipped` entries, so it does not change.
- **Are `in_loop` and `not_fresh` consistent between `queue_add` and `pull`?** Each has one caller: `in_loop` in `queue_add` (`:660`), `not_fresh` in `pull.ready` (`:782`). `queue_add` does not need `not_fresh`, because D2 runs the same check in the skill text at call time (`SKILL.md:460`). The two checks use the same three tests and the same reason text.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
| --- | --- | --- | --- |
| Suggestion / High | **Code review finding 2 is closed only when a `pull` or `queue add` runs between the exclusive run's finish and the hand rerun.** The drop at the start of `pull` removes a `started` entry only while its state says `finished`. `prune` in `queue add` checks the same thing. A probe (exclusive `a` pulled, finished, no `pull` after it, then rerun by hand, then `b` added) gave `pull` no output and `queue show` `waits b exclusive a`. With a `pull` after the finish, `b` started. The refill runs that `pull` at once, so the window is open only when the refill's `pull` fails, for example on a lock timeout. Even then it closes at the user's next `/my:handoff auto rows`, which is what the refill's failure signal tells them to run. The spec sentence states the fix with no such condition, and Risk does not name this window. | `plugins/my/bin/handoff-state.py:769-771`, `:618-620`, `:729-734`; `docs/plans/2026-10-13-roadmap-auto-runs-spec.md:215-218`; `plugins/my/skills/handoff/SKILL.md:560-561` | Add one Risk line in the plan: the case stays open when the refill's `pull` failed and the user reran the slug by hand before any `pull` or `queue add`. Do not change the code (one fix round). |
| Suggestion / High | **The code review's status line says findings 7 and 8 are "fixed in code". Finding 8 is only partly fixed, on purpose.** The duplicate cap check is kept, for the reason in the comment, and `live_states()` still runs three times per step. | `docs/plans/2026-10-14-roadmap-auto-runs-code-review.md:4`; `plugins/my/bin/handoff-state.py:276`, `:729`, `:776-780` | Reword the status line: "7 fixed; 8 fixed for the blocker reads, with the cap check kept on purpose (comment in `pull`)." |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
| --- | --- | --- |
| Each fix has a test that went red when the fix was removed (three mutation runs) | `plugins/my/tests/test_handoff_state.py` `test_add_labels_a_row_behind_a_gate_cycle`, `test_rule6_a_row_that_cannot_start_fresh_is_skipped_and_the_walk_goes_on`, `test_pull_drops_a_finished_started_entry_before_its_walk` | Strong |
| `not_fresh` uses D2's three checks, its order and its reason text, so call time and pull time judge a row the same way | `plugins/my/bin/handoff-state.py:750-761`, `:782-785`; `plugins/my/skills/handoff/SKILL.md:458-460` | Strong |
| A skip by `not_fresh` returns True, so rule 2 skips the rows behind it and the walk goes on to rows that do not depend on it (probe: `a` skipped, `b` after `a` skipped, `c` started) | `plugins/my/bin/handoff-state.py:783-785`, `:714-722` | Strong |
| Caching `common_dir` is safe: no `chdir` or environment change in the script, and every caller is a new subprocess | `plugins/my/bin/handoff-state.py:170-172`; `plugins/my/tests/test_handoff_state.py:52`; `plugins/my/bin/status-scan.py:192`, `:222` | Strong |
| The drop before `walk` changes no decision: a finished slug is never live, and rule 2 reads the state file when its entry is gone | `plugins/my/bin/handoff-state.py:712-734`, `:769-771` | Strong |
| The anchored plan pattern does not match a longer slug, and a test pins it | `plugins/my/bin/handoff-state.py:754`; `test_rule6_a_longer_slug_with_a_plan_does_not_block` | Moderate |
| The spec and plan record the new D5 rule and the known limits with the user's decision and date | `docs/plans/2026-10-13-roadmap-auto-runs-spec.md:243-250`; `docs/plans/2026-10-13-roadmap-auto-runs.md:1066-1094` | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
| --- | --- | --- |
| The exclusive hand-rerun case is still open when the refill's `pull` failed, and the docs present it as closed | `plugins/my/bin/handoff-state.py:769-771`; `docs/plans/2026-10-13-roadmap-auto-runs-spec.md:215-218` | Low |
| `queue show` still does not apply rule 6, and the fix round gives rule 6 one more skip reason. This is a known limit in Risk | `plugins/my/bin/handoff-state.py:810-825`; `docs/plans/2026-10-13-roadmap-auto-runs.md:1072-1075` | Low |

## Not Applicable

None.

## Needs Investigation

- **Uneven coverage of the 2071-line payload.** I read in depth the parts the fix round touched: `handoff-state.py` (the whole queue section and the shared helpers), the fix-round tests, and the spec and plan notes. I read the `status-scan.py` diff and the skill's "From roadmap rows", "Refill" and "Start checks" sections. I covered these only shallowly, relying on the first round's full read: the `status/SKILL.md` diff, both README diffs, `test_roadmap_queue.py`, `test_status_scan.py`, and the rest of the `handoff/SKILL.md` diff. The fix round does not touch them (the diff stat of the last two commits lists only `handoff-state.py`, its test file and four docs). If they changed after the first round, a full read of those parts would settle it.

## Reasoning

The fix round fixes each finding it claims at the root. The fresh-start check reuses D2's own checks instead of adding a new rule. The loop label is computed from the reachability graph. The stale exclusive entry is dropped at the point of decision. The mutation runs show the tests hold each fix in place. Caching `common_dir` and dropping entries before the walk are safe, because the script is always a new process, and a finished slug affects no rule except through its state file, which rule 2 still reads. What remains is one narrow window of finding 2, which needs a refill failure plus a hand rerun, plus a status line that claims a bit more than the code does. Both are documentation items under the one-fix-round rule.

## Verdict

**Assessment:** Sound
**Confidence:** High. Every fix was checked against the code, the tests, mutation runs and two probes. Only the files the fix round did not touch were read shallowly.
**Recommendation:** Add the Risk line for the narrow exclusive-rerun window, reword the code review's status line for finding 8, then squash-merge.
