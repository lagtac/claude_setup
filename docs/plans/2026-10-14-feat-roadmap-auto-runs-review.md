# Review: main..feat/roadmap-auto-runs

**Status:** review of main..feat/roadmap-auto-runs, 2026-10-14. Mixed: the queue, the walk and the refill are sound and follow the plan. One gap remains: `pull` does not recheck the fresh-start conditions, so a row the user starts by hand while it waits can take a slot and stall the queue without a stop line. Answered by the fix round: the fresh-start gap by a new D5 rule (the user's choice), the `my:status` gap as a known limit in the plan's Risk, and the Decision 3 wording in the docstring.

## Change Summary

The branch adds a queue of roadmap rows to `handoff-state.py`. It is one JSON file under `<git common dir>/my-handoff/queue/`, with four subcommands: `queue add`, `queue drop`, `queue show` and `pull`. `pull` and `queue show` share one walk over D5's rules. `start` is split into `start_run` so that `pull` can start runs in the same process, under the caller's `handoff-lock.py main`. `status-scan.py` gains a `queue` block. The prompt text adds the `/my:handoff auto rows` forms (D1 to D3) and the refill (D6) to `my:handoff`, and the report lines (D7) to `my:status`. The tests are unit tests, an end-to-end test under the real lock, and a recorded rehearsal.

Method: I read every touched file in full or in its relevant sections: `handoff-state.py`, `status-scan.py`, and in `handoff/SKILL.md` "Parallel runs", "Signal", "Launch", "Resume", "Restarted stages", "From roadmap rows", "Start checks", "Start checks in auto mode" and Review stage step 8. I also read `status/SKILL.md` steps 1 to 6 and the report, and the spec and plan in full. I had no symbol-reference tool, so every caller sweep was a text search (`grep -rn` for `write_state`, `start_run`, `handoff-state.py start`, `rows.json`, `queue show`). The `my` suite ran 199 tests and the `kit` suite 28, all OK. The markdownlint count (without MD013) is 0 for all five edited Markdown files. Every task commit carries its `Task: <N>` trailer.

## Plan Alignment

The implementation matches the plan. All 16 "Decisions this plan adds" are present, and Tasks 1 to 8 are each done. Deviations:

- `plugins/my/bin/handoff-state.py:609`, `:612`: Decision 3 says an unreadable or non-list input file exits 2 with `invalid entry <i>: <why>`. The code exits 2 but prints `invalid entries: cannot read …` or `invalid entries: … is not a JSON list`. This is justified: there is no entry index to cite, and the skill only prints the message (`handoff/SKILL.md` step 5). No caller parses the text.
- Additions beyond the plan, all harmless: `test_add_refuses_a_file_that_is_not_a_list_of_objects`, `test_add_reports_a_duplicate_in_the_same_file`, `test_add_from_a_worktree_writes_the_common_queue`, `ShowTest.test_none_when_nothing_waits` and `test_unreadable_queue_refuses`, and `QueueTest.test_queue_block_comes_after_runs_and_before_branches`. The `pull()` and `show()` helpers assert exit 0, which answers the plan review's vacuous-test finding.
- Missing: nothing. The review map lists a `ROADMAP.md` change, but it comes from `main` moving on (row 54 commits). The branch has no `ROADMAP.md` commit, and the plan leaves row 9 to the `done` marks.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
| --- | --- | --- | --- |
| Warning / Medium | **`pull` starts a row whose fresh start became impossible after the call, and the run then holds a slot with no stop line.** D2 checks "plan, branch or worktree for `<slug>` exists" once, at call time. `pull` checks only the spec hash, gates, exclusivity, the cap and the slug's own state file. Suppose the user starts a queued row by hand while it waits, in a supervised run (which has no state file) or by writing its plan. `start_run` then succeeds and writes `next=<stage>` with an empty `stopped`. The new `run auto` session fails the start check "no branch `*/<slug>`" (or "no plan yet"). A failed start check writes nothing, so the state stays live. At Max runs 1, every later row waits behind it. `my:status` lists it only as "in progress", because it has no stop line. The plan's Risk item on hand-started rows covers only an auto hand start, which has a state file, so `start_run` refuses. The spec's "Frozen judgment" Risk covers gates and `exclusive`, not branches or plans. | `plugins/my/bin/handoff-state.py:724-756` (`pull`, no fresh-start check before `start_run` at `:739`); `plugins/my/skills/handoff/SKILL.md:383-386`, `:593`, `:618-620`; `plugins/my/skills/handoff/SKILL.md:460` (D2 checks it only at call time); plan Risk `docs/plans/2026-10-13-roadmap-auto-runs.md:1066-1069` | In `pull`'s `ready`, before `start_run`, rerun D2's fresh-start test against the main checkout: the anchored plan path for a `plan` stage, `git branch --list '*/<slug>'`, and `.claude/worktrees/<slug>`. Skip the entry with D2's reason `<plan, branch or worktree> for <slug> exists`. Rule 2 then skips the rows behind it, as for an ended blocker. Or record the gap as a known limit in Risk. Either way it needs the user's choice, because it adds a rule to D5. |
| Suggestion / High | **`my:status` says nothing about `waiting` rows that the next `pull` will skip.** `queue show` passes over entries that rules 1 and 2 would skip, as D7 says. So when every waiting row is stale, the first line is `none` while the block still lists `waiting` rows. The report rules fire only on a `ready` or `waits` line, so these rows drop out of the report until some `pull` runs. During a stall with no live run, no `pull` runs. The `<k>` in `<k> rows wait for <what>` also counts rows that will be skipped. A probe showed it: one queued row, its spec edited, gave `== queue` / `none` / `waiting 1 a - -`. | `plugins/my/skills/status/SKILL.md:101-114`; `plugins/my/bin/handoff-state.py:759-774` (`queue_show`); `plugins/my/bin/status-scan.py:234-239` | Add a report line to `status/SKILL.md` for a `none` first line with `waiting` rows, such as "`<k>` rows will be skipped at the next start: run /my:handoff auto rows". Or have `queue show` print its skip lines, so that `queue_facts` can show the would-be reason. |
| Suggestion / High | **Plan Decision 3 wording deviation.** An unreadable or non-list input file prints `invalid entries: …`, not `invalid entry <i>: <why>`. The exit code (2) and "nothing written" match. | `plugins/my/bin/handoff-state.py:609`, `:612` | Accept as justified, or align the docstring at `:74` so it names both forms. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
| --- | --- | --- |
| One walk serves both `pull` and `queue show`, so D7's "as `pull` would decide" cannot drift | `plugins/my/bin/handoff-state.py:664-716`, `:731-747`, `:763-765` | Strong |
| `start_run` keeps the CLI `start` output byte for byte. `pull` calls it in the same process and never takes lock `main` itself, so a nested `flock` cannot deadlock | `plugins/my/bin/handoff-state.py:266-303`; `plugins/my/tests/test_roadmap_queue.py` `test_pull_inside_lock_main_does_not_wait_on_its_own_lock` | Strong |
| The cap holds under contention: four concurrent locked `pull`s start exactly two runs, in slots 1 and 2 | `plugins/my/tests/test_roadmap_queue.py` `test_concurrent_pulls_never_pass_the_cap` | Strong |
| The queue lives in a subfolder that `live_states` never lists, and tests at both levels guard this | `plugins/my/bin/handoff-state.py:233`, `:502`; `test_live_ignores_the_queue_folder`; `QueueTest.test_queue_folder_is_not_a_run` | Strong |
| Hashes and paths come from the main checkout, so `pull` from a worktree and a missing spec behave as specified (rule 1, not a `GitError`) | `plugins/my/bin/handoff-state.py:526-530`; `test_pull_from_a_worktree_reads_the_main_checkout`, `test_rule1_changed_or_missing_spec_is_skipped` | Moderate |
| The refill never writes `stopped` on the finished run. Launch step 4 gets an explicit exception, so rule 2 cannot misread a refill failure as "ended by the user" | `plugins/my/skills/handoff/SKILL.md:311-313`, `:536-570` | Moderate |
| The refill applies in projects with a "Parallel runs" section too: that variant only adds to sub-step 4 and does not replace it | `plugins/my/skills/handoff/SKILL.md:1041-1045`, `:1081-1082` | Moderate |
| The rehearsal ran end to end through the real skill: fold, one window, refill, both `done`, `origin` unchanged | `docs/plans/2026-10-13-roadmap-auto-runs.md:1101-1120` | Moderate |
| No orphaned callers: `write_state` stays as a thin wrapper, `start` keeps its interface, and the one prose caller (`SKILL.md:657`) is unchanged | text sweep above; `plugins/my/bin/handoff-state.py:196-197` | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
| --- | --- | --- |
| A fresh-start conflict that appears while a row waits is not rechecked by `pull`. The run then fails its own start check and silently holds a slot | `plugins/my/bin/handoff-state.py:731-747`; `plugins/my/skills/handoff/SKILL.md:383-386`, `:618-620` | Medium |
| `my:status` has no line for `waiting` rows that the walk passes over (first line `none`) | `plugins/my/skills/status/SKILL.md:101-114`; probe output | Low |
| The D3 fold and the queue rely on prompt prose (about 150 lines of new skill text) that no automated test drives; only the one rehearsal covers it | `plugins/my/skills/handoff/SKILL.md:420-570` | Low |

## Not Applicable

None.

## Reasoning

The script is the core of the design, and it holds up. The walk is shared, the start goes through one function under one lock, the cap holds under contention, and every D5 rule has a test that fails for the right reason. The prose matches the spec's D1 to D7 and the plan's Decisions 14 to 16, and the rehearsal shows the whole chain working. One soundness gap remains: D2's fresh-start judgment is frozen at call time, and `pull` trusts it hours later. That gap can leave a live run that holds a slot with no stop line, which is the silent stall the design tries to avoid. It is a Warning, not Critical, because it needs the user to act on a queued row by hand and because the failed start check still shows ⚠ in its window.

## Verdict

**Assessment:** Mixed
**Confidence:** Medium. The code paths and tests are verified directly. The Warning's trigger, a hand start of a queued row, is plausible but its frequency is unknown.
**Recommendation:** Ask the user whether `pull` should recheck the fresh-start conditions (plan, `*/<slug>` branch, worktree) before `start_run`, or whether the gap goes into the plan's **Risk** section as a known limit. Then add the `my:status` line for passed-over `waiting` rows, and merge.
