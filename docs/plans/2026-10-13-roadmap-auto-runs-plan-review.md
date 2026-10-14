# Review: docs/plans/2026-10-13-roadmap-auto-runs.md

**Status:** review of docs/plans/2026-10-13-roadmap-auto-runs.md, 2026-10-14. Mixed: the approach and grounding are sound, but a re-queued slug can be skipped because of its own old `skipped` entry, and three `pull` unit tests pass before any code exists. Answered in the plan before its commit: six findings fixed; the re-queued slug and the D3 clean-tree reading decided by the user on 2026-10-14 (Decisions 14 and 16).

## Change Summary

The plan builds the spec's roadmap queue in eight tasks. Tasks 1 to 4 are code. They add a queue file and four subcommands to `handoff-state.py` (`queue add`, `queue drop`, `pull`, `queue show`), plus an end-to-end test under the real lock and a `queue` block in `status-scan.py`. Tasks 5 to 7 are prompt and doc text: the `auto rows` forms, the D3 commit, the refill in `my:handoff`, and the report lines in `my:status`. Task 8 is a rehearsal that the user starts. The plan also adds 15 decisions of its own, such as argument forms, exit codes and the `start_run` split.

## Grounding

The plan's references hold against the repo. The caller sweep was text search only (`git grep`, `grep -rn`), because this reviewer has no symbol-reference tool.

- Every line reference checks out:
  - `handoff-state.py`: `write_state` at :128, `start` at :201, `main` at :418. `usage()` prints only up to the first blank line (:412-415), as Decision 1 says.
  - `status-scan.py`: `blocks` at :307.
  - `plugins/my/skills/handoff/SKILL.md`: Forms :26, usage line :69, Signal :177, "To end an abandoned run" :349, `## Run` :403, sub-step 4 :871, the Finish line :876.
  - `plugins/my/skills/handoff/README.md`: `### Known problems` :381.
  - `README.md:157-165`.
- The baselines hold. `python3 -m unittest discover tests` in `plugins/my` runs 146 tests, OK. The lint count is 0 for all four Markdown files the plan edits. The tools are git 2.43.0 and Python 3.12.3.
- The empty fields in Decision 10 match the auto launch's `start` command (`SKILL.md:487-491`). The `task_doc` rule matches `SKILL.md:493-495`.
- `live` skips the `queue/` folder: `handoff-state.py:177` skips names that do not end in `.json`. So does the fallback glob in `status-scan.py:197`. The plan's Review Focus item holds.
- The helpers that Task 3 says it copies exist: `clean_env`, `sh` and `git` in `test_parallel_runs.py:25-43`.
- Reference sweep: `git grep -n 'handoff-state.py\|status-scan.py'` outside `docs/` finds exactly the files the plan lists. One small gap: `ROADMAP.md` also matches rows 42 and 43, and a line in the Order of work (`ROADMAP.md:42`, `:243`), not only row 34. These rows plan to extend `handoff-state.py` later. None needs an edit in this branch.
- False assumption: Task 1 step 2 says "the new tests FAIL". `test_live_ignores_the_queue_folder` passes before any code is written (`handoff-state.py:177`). Three `pull` tests also pass then (see Issues).

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
| --- | --- | --- | --- |
| Warning / High | **A slug can have two queue entries, and an old `skipped` entry wrongly blocks the rows behind it.** Decision 4 refuses a duplicate only when the slug is `waiting`. The prune in Decision 6 keeps a `skipped` entry whenever a `waiting` entry names its slug in `after`. Rule 2 skips an entry when a blocker "belongs to a `skipped` entry". Trace: the user drops row `a` (or `a` is skipped as `spec changed since the call`), fixes it, then calls `auto rows a b` with `b` gated behind `a`. The queue becomes [a skipped, a waiting, b waiting after a]. `pull` starts the new `a`, then skips `b` as `blocker a did not finish`. | Plan :102-106, :113-116; spec :186-189, :206-211 | `queue add` removes every earlier `skipped` entry for a slug that it adds. Or rule 2 reads only the last entry per slug. Add one test: drop `a`, re-add `a` and `b` after `a`, pull, finish `a`, and check that `b` starts. |
| Warning / High | **Three `pull` unit tests pass before `pull` exists, and also when it crashes.** `test_rule3_waiting_entry_stops_the_walk`, `test_rule4_exclusive_entry_waits_for_no_live_run` and `test_rule4_nothing_starts_beside_a_live_exclusive_run` check only that stdout is empty, plus queue states that `queue add` (Task 1) already writes. Without `pull`, the script prints its usage on stderr and exits 2 with empty stdout. Step 2's claim that the new tests fail with exit 2 is wrong for these three. | Plan :431-435, :443-452, :525-527; `handoff-state.py:412-415`, `:428-429` | Make the `pull()` helper assert `returncode == 0`, as `scan()` does in `test_status_scan.py:98-101`. Or assert the exit code in each test. Also assert something positive that only a working walk produces, for example `queue show`'s `waits` line, or that `c` stays `waiting` after a later `finish`. |
| Warning / High | **Decision 14 changes an approved spec decision without the user's sign-off.** D3's fold test says "`git status --porcelain` prints nothing". Decision 14 reads it as "lists only the queued specs". The plan itself says the test "can never hold as written". Yet the plan says "None changes a D1 to D7 decision". The reading is probably what the spec meant: D3 applies Code stage sub-steps a and b, and its trade-off rejects "always one normal commit". But the method's "No silent reinterpretation" rule asks for the user's answer before the plan is committed. Recording the change under **Risk** is a breadcrumb for the executor, not sign-off. The spec's Delegation sets **Design-changing findings** to `stop`. | Plan :76-77, :162-171, :1005-1007; spec :137-145, :295 | Needs user sign-off. Ask in the form "D3 says X for reason Y; Y cannot hold; keep the fold on the reading Z?" On yes, fix D3's wording in the spec, so the spec and the plan agree. |
| Warning / Medium | **The refill's failure path conflicts with Launch step 4, which Task 6 does not edit.** Launch step 4 says that when a `run auto` stage falls back "while it launches the next stage, that is a stop (row 2)". In auto mode, a stop first runs `handoff-state.py set <slug> stopped="…"` on the session's own slug. If the review session follows that text during a refill, it writes `stopped` on its own state, which already has `next=finished`. That is exactly rule 2's "ended by the user" pattern, so `pull` would skip every row gated behind the finished run. Task 6 edits only Signal, "To end an abandoned run", sub-step 4 and Finish. It also never says whether the refill goes on to the next printed line after a failed launch. A failed launch is a signal, and "After a signal, stop" would leave the other started runs with no window and no stop line. That can only happen with **Max runs** above 1. | Plan :827-860; `SKILL.md:203-209`, `:293-297`, `:937`; spec :209-210 | Task 6 should also edit Launch step 4: a refill launch is not a stop of this run, and the refill writes nothing to this run's own state. Say whether the refill launches the rest of `pull`'s lines before it signals, and if so, write `stopped` on each failed one. |
| Warning / Medium | **Task 4 takes D7's Max runs from the wrong place.** Task 4 step 4 says to print "first can start now" only when the live runs are fewer than **Max runs** "(step 3)". `status/SKILL.md` step 3 gives **Max runs** a default of 2. But in a project with no "Parallel runs" section, such as this repo, `<n>` is 1 (`handoff/SKILL.md:140-142`). Read literally, `my:status` prints "first can start now" while one run is live, and the `/my:handoff auto rows` it names starts nothing. D7 forbids exactly that. | Plan :702-708; `plugins/my/skills/status/SKILL.md:61-64`; `plugins/my/skills/handoff/SKILL.md:140-142`; spec :284-286 | In Task 4 step 4, define the cap as the `<n>` of `my:handoff` "Parallel runs": 1 without the section. Add the same rule to the status skill's step 3. |
| Warning / Medium | **Nothing tests D3, the one step that rewrites `<base>`.** The fixup, fold and normal-commit paths of D3 (Task 5 step 5, with Decision 14) are prose only. Task 8 step 1 says the fixture specs are "approved". It does not say whether their `approved` edits stay uncommitted. If they are committed, the call has nothing to commit, and neither the fixup path nor the fold ever runs. Spec review 2 gave its Critical finding to this exact area. | Plan :771-789, :918-923; spec :126-153 | In Task 8 step 1, leave both specs' `approved` edits uncommitted, with no upstream set (as now). Add a check in step 3: the call made one fixup per spec and folded them, `git log` on `main` shows no `fixup!`, and the two spec commits hold the `approved` status. |
| Suggestion / High | Task 1 step 2 expects every new test to fail first. `test_live_ignores_the_queue_folder` passes already. Task 4 step 2 labels its matching test a regression guard; Task 1 does not. | Plan :337-344; `handoff-state.py:177` | In Task 1 step 2, mark that test as a guard that passes already, as Task 4 step 2 does. |
| Suggestion / High | The spec says `queue drop` must refuse an unreadable queue file and change nothing. Decision 7 does not say this, and no test covers it. | Plan :117-122; spec :236-237 | Add the refusal line and exit 1 to Decision 7, and one `QueueDropTest` case. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
| --- | --- | --- |
| Grounding is accurate: every line reference, test count and lint count checks out | `handoff-state.py:128`, `:201`, `:418`; `status-scan.py:307`; `SKILL.md:69`, `:871`, `:876`; 146 tests OK | Strong |
| The reference sweep matches `git grep` exactly, and the plan correctly says no existing subcommand changes its interface | `git grep -n 'handoff-state.py\|status-scan.py'` outside `docs/` | Strong |
| The queue lives in a subfolder that `live` and the status-scan fallback already ignore, so the risk that a waiting row counts as a live run is closed by today's code | `handoff-state.py:177`; `status-scan.py:197` | Strong |
| The `start_run` split keeps the CLI output; `StartTest` pins every refusal line, and the concurrent-start test pins the cap under the real lock | `test_handoff_state.py:357-422` | Moderate |
| One walk serves both `pull` and `queue show`, so D7's "as `pull` would decide" cannot drift. The `ShowTest` cases assert exact stdout | Plan :128-137, :480-519 | Moderate |
| The end-to-end test runs the real scripts under the real `handoff-lock.py main`, as `test_parallel_runs.py` does, and covers all seven cases of the spec's Testing section | Plan :557-626; `test_parallel_runs.py:82-85`; spec :397-407 | Moderate |
| Hashing the spec in the main checkout, and returning `None` for a missing file, closes two Review Focus cases with tests (a deleted spec, a pull from a worktree) | Plan :153-157, :411-418, :472-474 | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
| --- | --- | --- |
| A slug's old `skipped` entry outlives a new `waiting` entry for the same slug, and rule 2 then skips a row behind a blocker that is running | Plan :102-116; spec :206-211 | Medium |
| Three D5 rule tests can never go red, which the project's "no vacuous tests" standard forbids | Plan :431-452; `handoff-state.py:428-429` | Medium |
| A reinterpretation of an approved decision is recorded as a plan decision, not asked | Plan :76-77, :162-171 | Medium |
| The prose leaves two readings of a refill failure, and one of them falsely marks a finished run as ended | `SKILL.md:293-297`, `:203-209` | Medium |
| The riskiest prose path, the fold in D3, has no automated test and may not run in the rehearsal | Plan :918-923 | Medium |

## Not Applicable

None.

## Reasoning

The plan is well grounded. Its decisions fill the spec's gaps with testable contracts, its tasks are ordered so that each depends only on earlier ones, and its Risk section names the hard-to-reverse format. No finding is Critical. Each one has a local fix: one queue rule plus a test, a stricter test helper, two prose edits, a fixture detail, and one question to the user. Two findings sit on the queue contract that the spec's Risk section calls hard to reverse: the duplicate entry and Decision 14. They should be settled before code is written, which gives Mixed.

## Verdict

**Assessment:** Mixed
**Confidence:** High. Every surfaced finding was traced against the repo files or the spec text cited.
**Recommendation:** Ask the user about Decision 14 first. Then amend the plan: add the rule that a re-added slug replaces its old `skipped` entry, with a test; make the `pull()` test helper assert exit 0; extend Task 6 to Launch step 4; fix the Max runs source in Task 4; and leave the fixture's `approved` edits uncommitted in Task 8. Then hand off the code stage.
