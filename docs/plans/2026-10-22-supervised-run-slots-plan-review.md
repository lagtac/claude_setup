# Review: docs/plans/2026-10-22-supervised-run-slots.md

**Status:** review of docs/plans/2026-10-22-supervised-run-slots.md, 2026-10-22. Mixed: the plan is well grounded and its approach is right, but `test_supervised_run_does_not_count_toward_the_cap` (Task 2) passes before any code exists, against what Step 3 says, so the test that pins D5 never goes red.

## Change Summary

The plan implements row 56 in seven tasks. Tasks 1 to 3 add a `mode` field, a `start <slug> --supervised` form and one slot pool to `handoff-state.py`, with the cap counting only auto runs in `start --max` and `pull` rule 5. Task 4 adds a sixth `mode` column to the `runs` block of `status-scan.py`. Tasks 5 and 6 change the prose of the handoff `SKILL.md`, its `README.md` and the status `SKILL.md`. Task 7 is a rehearsal in a scratch repo.

## Grounding

I checked the plan against the repo with `Read`, `sed`, `grep` and `git grep`. I had no symbol-reference tool, so the caller sweep was text-only. Most claims hold:

- The test line numbers hold: `plugins/my/tests/test_handoff_state.py:349` and `:357` are the exact `live` lists, `:740-743` is the `PullTest` dict, and `plugins/my/tests/test_status_scan.py:277` is the fallback test's row.
- The plan says `test_runs_fallback_hides_finished` "runs the `live` path". This holds: the real `handoff-state.py` sits beside `status-scan.py` (`plugins/my/bin/status-scan.py:192-195`).
- `test_status_scan.py` does not import `shutil` (`plugins/my/tests/test_status_scan.py:11-17`), so the plan is right to add it.
- The `SKILL.md` lines hold: 185, 393, 512, 553, 570, 582, 660, 701, 856 and 939. So do the README lines 311, 364, 367, 368 and 415.
- On `main`, `plugins/my` has 273 tests, and the lint count is 0 for all three `.md` files. Both match the plan.
- `usage()` prints only up to the first blank line (`plugins/my/bin/handoff-state.py:842-845`). This holds, as the plan's Task 2 Step 4 warns.
- I ran the five new usage cases against the current script. All exit 2 before Task 1. With Task 1's `mode` field, `--max 2 mode=supervised` would exit 0. This matches Task 2 Step 3.
- **Wrong red claim, Task 2 Step 3.**
  - The step says the new supervised tests fail. `test_supervised_run_does_not_count_toward_the_cap` does not.
  - Today the supervised start exits 2 and writes nothing. `start b --max 1` then exits 0, and `start c --max 1` prints `refused: 1 auto runs are live (b); the most is 1`. I confirmed this in a scratch repo.
  - So the test passes before the change.
  - The code that makes it pass: `plugins/my/bin/handoff-state.py:296-299`.
- **Missed by the sweep.** The plan swept only `plugins/` and `global/`, so it missed two lines:
  - `README.md:192`, which says `handoff-state.py` "keeps the state of a `my:handoff auto` run";
  - `README.md:197`, which says `status-scan.py` prints "auto runs".
  
  The docstring line 2 of `plugins/my/bin/handoff-state.py` ("an autonomous my:handoff run") is in no task either. All three become untrue after the change.
- `test_parallel_runs.py` and `test_roadmap_queue.py` need no change. They write states without `mode` and check only auto refusal lines (`plugins/my/tests/test_parallel_runs.py:164`, `plugins/my/tests/test_roadmap_queue.py:96-97`). This matches the plan.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
| --- | --- | --- | --- |
| Warning / High | `test_supervised_run_does_not_count_toward_the_cap` passes before the change. It never checks the result of `self.supervised("a")`. So when the supervised start writes nothing, auto `b` starts, auto `c` is refused naming only `b`, and the test stays green. Task 2 Step 3 lists it among the tests that fail with exit 2. The Testing Strategy counts it among the "ten `StartTest` tests" that fail first, which should be nine. The project's test standard says an assertion that never went red needs a deliberate break, and the plan gives this test none. A smaller point: `test_auto_start_refuses_beside_a_live_supervised_run_of_its_slug` also goes red, but with a `FileNotFoundError` from `file_of("a")`, not exit 2. | Scratch run against `plugins/my/bin/handoff-state.py:296-299` (exit 2), then `:279-282` (cap refusal naming `b`) | Assert the supervised start first, for example `r = self.supervised("a")`, then `self.assertEqual((r.returncode, r.stdout.strip()), (0, "1"))`. The test then goes red on exit 2, for the right reason. Correct the Step 3 expectation and the Testing Strategy count. |
| Suggestion / High | The top-level `README.md` and the first docstring line of `handoff-state.py` still say the state belongs to auto runs only. The plan's sweep covered only `plugins/` and `global/`. Global Constraints also say every changed file is under `plugins/my/`. | `README.md:192`, `README.md:197`, `plugins/my/bin/handoff-state.py:2` | Add the two README sentences to Task 5 or Task 6, and the docstring line to Task 1. Change the scope sentence in Global Constraints to fit. |
| Suggestion / High | Task 5 Step 3 has a wrong cross-reference. The code-stage step 4 bullet says "then the queue line of Step 5 below". The queue line is defined in Step 4, the review stage; Step 5 is Resume. Step 4 also places the line "just before Finish's last line", but code stage step 4 signals and stops without running Finish. So the executor must guess where the line goes on that path. | `plugins/my/skills/handoff/SKILL.md:866-868` (code stage step 4 ends in a signal and a stop); plan Task 5 Steps 3 and 4 | Change it to "the queue line of Step 4". Say where the line goes in code stage step 4, for example "just before the signal". |
| Suggestion / High | The supervised refusal in "Resume" goes after the `finished` case of step 2. But step 1 runs `handoff-state.py check <slug>` first and stops on any mismatch. Take a supervised state at `next=review` without `branch` or `worktree`, for example one whose code stage ran before the change (the plan's Risk). Resume then refuses with `missing field: branch`, not with the supervised line. | `plugins/my/skills/handoff/SKILL.md:366-372`; `plugins/my/bin/handoff-state.py:142` (`review` needs `branch`, `worktree`) | Put the `mode` check before step 1, or say in Risk that a failing `check` can hide the supervised refusal. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
| --- | --- | --- |
| Grounded line references and current-behaviour claims | `plugins/my/tests/test_handoff_state.py:349,357,740-743`; `plugins/my/tests/test_status_scan.py:277`; `plugins/my/skills/handoff/SKILL.md:185,393,512` | Strong |
| The guard tests and their breaks are traced correctly. Rule 5 is red before Task 3. The rule 3, 4 and 6 guards pass after Task 2, and each fails under its named break. | `plugins/my/bin/handoff-state.py:729-736` (rule 4 `live`), `:712-728` (rule 3 blockers), `:789-795` (`exists` decides skip or stop) | Strong |
| Decision 5 keeps the slot search over every live run. A range over auto runs only would run out of numbers. | `plugins/my/bin/handoff-state.py:283-284` | Strong |
| The supervised "start again" test tells "keep the slot" apart from "lowest free slot". It frees slot 1 before the second call and expects `2`. | plan Task 2, `test_supervised_start_again_keeps_the_slot_and_writes_the_fields`; `plugins/my/bin/handoff-state.py:284` | Moderate |
| The fallback test reaches the real fallback path by copying the script beside a stub, so `HERE` points at the stub. | `plugins/my/bin/status-scan.py:59`, `:192-213` | Strong |
| Risk names rollback, blast radius from the sweep, stale states, slots above **Max runs** and lock waits | plan Risk section; `plugins/my/skills/handoff/SKILL.md:393,512` | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
| --- | --- | --- |
| A central D5 test never goes red, and the plan says it does | `plugins/my/bin/handoff-state.py:296-299` | Medium |
| The sweep missed the top-level README and the module docstring | `README.md:192,197`; `plugins/my/bin/handoff-state.py:2` | Low |
| The prose task cross-reference is wrong, and the queue line has no place in the step 4 stop path | `plugins/my/skills/handoff/SKILL.md:866-868` | Low |
| The resume ordering can hide the supervised refusal | `plugins/my/skills/handoff/SKILL.md:366-372` | Low |

## Not Applicable

None.

## Reasoning

The plan matches the repo almost everywhere I checked:

- the line numbers, the test helpers, the lint and test counts;
- the red and guard outcomes for Tasks 1, 3 and 4, and the usage cases in Task 2.

Its sequencing and risk notes are sound. One Task 2 test does not do what the plan says. It passes before the change, and it stays green whenever the supervised start fails silently. That breaks the project's red-step rule for the test that pins D5, so the verdict is Mixed. The fix is one assertion. The other findings are doc and prose gaps that do not affect the code.

## Verdict

**Assessment:** Mixed
**Confidence:** High. I confirmed the top finding by running the test's exact command sequence against the current script, and checked each other claim against a file I opened.
**Recommendation:** Before handing off the code stage, make three changes, then implement:

1. Add the supervised-start assertion to `test_supervised_run_does_not_count_toward_the_cap`.
2. Correct the Task 2 Step 3 expectation and the Testing Strategy count.
3. Fix the Task 5 Step 3 cross-reference.

Optionally, also add the top-level README and docstring lines to the file list.
