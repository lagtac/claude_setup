# Review: main..feat/autonomous-run

**Status:** review of main..feat/autonomous-run, 2026-10-12. Mixed: the design is sound and matches the plan, but `resume` can relaunch onto a half-finished squash-merge that `check` does not see, and it clears a stop reason without showing it.

## Change Summary

The branch adds an auto mode to `my:handoff`. It has two new standard-library scripts: a `PreToolUse` hook that blocks `git push` when `MY_AUTORUN` is set (`plugins/my/hooks/block-autorun-push.py`), and a state helper that keeps `<git common dir>/my-handoff/<slug>.json` and checks it against git (`plugins/my/bin/handoff-state.py`). Both have unit tests. The rest is prompt text in `plugins/my/skills/handoff/SKILL.md`: the auto forms, the Delegation format, the start checks, the 17-row stop table, the state writes, and `resume`. Docs changes are in the handoff README, the root README and `global/CLAUDE.md`. The plan's Risk section and Testing Strategy record the rehearsal.

Method note: I had no symbol-reference tool, so every caller sweep was a text search (`grep -rn`). The branch adds symbols and removes or renames none, so no caller can be left orphaned. The new names (`handoff-state`, `MY_AUTORUN`) appear only in the files the payload touches.

## Plan Alignment

The implementation matches the plan task by task:

- Task 1: the guard, its tests and the `hooks.json` entry.
- Task 2: the helper, with every listed test plus a few extra.
- Tasks 3 to 5: the `SKILL.md` sections for forms, Delegation, start checks, Launch, Signal, the stop table, the stage changes and Resume.
- Task 6: the docs.
- Task 7: the rehearsal record.

Every fixed copy string in Global Constraints is present word for word. Deviations:

- `plugins/my/skills/handoff/SKILL.md:385-391`: the launch's `set` also clears `branch`, `worktree`, `squash_subject` and `head_before_fold`. The plan asked only for `stopped=`. The change is justified: the plan's own rule lets a launch start over after a `finished` run, and without the clearing that run's leftover fields would remain.
- `plugins/my/tests/test_block_autorun_push.py:1048-1055`: the tests run the guard only as a subprocess. Task 1's Interfaces promised `pushes()` "for the tests to import with `importlib`". Harmless: the subprocess tests cover the same function end to end.
- `plugins/my/hooks/block-autorun-push.py:408`: the guard also splits at a single `&` and at parentheses. The spec's D4 lists a smaller set. This is stricter in the safe direction and justified.
- (missing from the repo) Task 1 step 6, the end-to-end guard run, and the headless runs a1 to a9 and r1 to r3 have no recorded result in the plan. The Testing Strategy records only Task 7. I found the session's scratchpad logs: the Monitor run `e2e/g3.jsonl` shows `"name":"Monitor","input":{"command":"git push origin main",…}` and the block message. So this is a gap in the record, not in the testing. It is below the surfacing bar.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / Medium | A crash after `git merge --squash` but before its commit leaves the squash staged in the main checkout. `check` does not see it: `IN_PROGRESS` omits `SQUASH_MSG`, and the `merge` facts only check that the branch exists. A restarted review stage checks for uncommitted files only in the worktree, never in the main checkout. Sub-step 1 then runs `git merge --squash` again. I reproduced this in a scratch repo where `<base>` had moved after the fork: the second squash fails with "Your local changes … would be overwritten by merge" and exit 2. That is not a conflict, so row 15 does not cover it, and no stop row does. The plan's Review Focus covers only a crash after the commit. | `plugins/my/bin/handoff-state.py:160-161`, `plugins/my/bin/handoff-state.py:292-295`, `plugins/my/skills/handoff/SKILL.md:280-286`, `plugins/my/skills/handoff/SKILL.md:645-649` | For `next=merge`, have `check` report a mismatch when `SQUASH_MSG` exists or the main checkout's index differs from `HEAD`, for example `squash in progress` or `<base> not clean`. Also add the main checkout to the review restart's uncommitted-files check from sub-step 1 onward. |
| Warning / Medium | `resume` runs `set <slug> stopped=` and launches without ever printing the earlier stop reason, so a stop meant for the user can be passed over without anyone reading it. Concrete case: row 17, fold exit 3 with "the tree after the rebase differs" (`git-fold-fixups.py:256-259`). History is already rewritten and the fixups are gone. For `next=fold`, `check` passes, because the squash commit exists and the worktree is not listed. The relaunched review stage finds no waiting fixups, sets `next=done`, and writes the `done` marks on a tree whose post-fold check failed. The README presents `resume` as the way to continue any stopped run whose window is gone. | `plugins/my/skills/handoff/SKILL.md:250-264`, `plugins/my/bin/handoff-state.py:302-306`, `plugins/my/skills/handoff/README.md:288-296` | In Resume step 2, print `stopped` when it is not empty, and have the user confirm before step 4 clears it. Or have `check` refuse `next=fold` when `head_before_fold` is set and `HEAD` differs from it while a `stopped` reason is recorded. |
| Suggestion / High | `check` writes `next=worktree-remove` as soon as it finds a squash commit, before it checks that step's facts. If those facts then fail, for example `squash subject matches 2 commits`, `check` exits 1 but has already changed the state file. Resume step 1 says a refused resume writes nothing. | `plugins/my/bin/handoff-state.py:328-332`, `plugins/my/skills/handoff/SKILL.md:246-247` | Run `facts(repo, state, "worktree-remove")` first, and write the new `next` only when it returns no lines. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| The parts that must be exact are tested code, not prose: the push guard and the state checks, including the "merge happened before a crash" detection and the older-commit-with-same-subject case | `plugins/my/bin/handoff-state.py:257-263`, `plugins/my/tests/test_handoff_state.py:1332-1344` | Strong |
| Plain handoff is unchanged: every auto rule is fenced under "In auto mode", and a8 plus the plain rehearsal run confirm it | `plugins/my/skills/handoff/SKILL.md:42-46`, plan Testing Strategy (`plainw`) | Strong |
| The guard costs almost nothing in the user's own sessions: it exits before reading stdin when the variable is unset or empty, and a test covers bad JSON | `plugins/my/hooks/block-autorun-push.py:466-467`, `plugins/my/tests/test_block_autorun_push.py:1095-1096` | Strong |
| Every stop point of the existing skill gets a fixed outcome in one table that mirrors the spec's D5 row for row. Each stage step names its row | `plugins/my/skills/handoff/SKILL.md:147-165`, `:463-473`, `:522-536`, `:629-665` | Strong |
| The state file sits in the git common dir, so it never shows in `git status` and never blocks a fold. The write is atomic: a temporary file, then `os.replace` | `plugins/my/bin/handoff-state.py:183-208` | Strong |
| It follows the sibling script's patterns: `git()` helper, `usage()` from the docstring, exit-code contract, tests copied from the fold tests | `plugins/my/bin/git-fold-fixups.py:1-33`, `plugins/my/bin/handoff-state.py:170-176`, `:338-341` | Moderate |
| The full cycle was rehearsed on real tmux windows with a bare `origin`: four runs, all passing | plan Testing Strategy "Rehearsal, 2026-10-12" | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| The crash window between the squash and its commit is not covered by `check` or by the restart rules | `plugins/my/bin/handoff-state.py:160-161`, `plugins/my/skills/handoff/SKILL.md:280-286` | Medium |
| `resume` drops the `stopped` reason without showing it, so a stop meant for the user can be passed over | `plugins/my/skills/handoff/SKILL.md:262` | Medium |
| Most of the 17 stop rows are prompt text checked only for presence. That is a known limit in Risk, so it is not a finding, but it is why the two items above were not caught | plan Risk, third item | Low |
| `check` writes the state file during a refused check | `plugins/my/bin/handoff-state.py:328-332` | Low |

## Not Applicable

None.

## Needs Investigation

- **The base branch the helper uses can differ from the skill's `<base>`.** `Repo.base` is always the branch checked out in the main checkout (`plugins/my/bin/handoff-state.py:234`). `SKILL.md:77-80` first takes `<base>` from the project's rules when they name one. Plan decision 6 accepts the checked-out branch. I could not find a project in this setup whose rules name a base other than the main checkout's branch. If one exists, `check` would test the wrong branch. Answering it takes a look at the projects' `CLAUDE.md` files.

## Reasoning

The approach is right. It keeps one copy of the stages, puts the exact parts in tested scripts, and ties every existing stop point to a fixed outcome. The diff matches the plan, and its deviations are justified. Both Warning rows are about `resume` after a crash or a stop. In each, the state checks pass while the main checkout or the earlier stop needs a human, and the relaunched stage then fails in a way no stop row covers, or passes over the earlier stop. These are holes in the crash-safety contract the spec's D7 promises, not flaws in the approach, so the verdict is Mixed rather than Problematic.

## Verdict

**Assessment:** Mixed
**Confidence:** Medium — I reproduced the first Warning in a scratch repo; the second follows from reading `SKILL.md` and `git-fold-fixups.py` together but was not run.
**Recommendation:** Fix the two Warning rows in one fix round:

- Have `check` see a staged squash.
- Have Resume show `stopped` before it clears it.

Separately, the merge waits on one decision of the user's. The plan's Risk section says the silent API stall "breaks the spec's Goal, end state 2 … whether to accept it is the user's decision", while Open Questions says "None". Get that decision before the squash-merge.
