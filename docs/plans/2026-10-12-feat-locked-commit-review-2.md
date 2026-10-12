# Review: main..feat/locked-commit

**Status:** review of main..feat/locked-commit, 2026-10-12. Sound: the fix round closes the earlier finding and the unstage gap, and two Suggestions remain: the spec's D2 does not name the new unstage step, and Risk 7 calls `docs-layout.md` a plain copy when it is reached through a symlinked folder. Answered in the spec's Risk section: Risk 7 is corrected, and Risk 9 records the D2 gap.

## Change Summary

The branch adds `plugins/my/bin/locked-commit.py`. The script checks its input, then runs `handoff-lock.py main` in its own place. Under the lock, a `sh -c` stages the paths, commits them with `git commit -F <message file>`, prints `git show --stat` and deletes the message file. Five instruction files replace their copy of the heredoc command with one `locked-commit.py -F <message file> <paths>` line. The fix round added three things. When the commit fails, the paths are unstaged with `git reset -q -- <paths>` under the lock, and a pre-commit-hook test proves it. The parallel-runs integration test now makes its `done` commit through the script. The spec gained Risk items 7 and 8.

## Plan Alignment

The implementation matches the spec (`docs/plans/2026-10-12-locked-commit-spec.md`), D1 to D7 and Tasks 1 to 5. The earlier review checked those in detail, so this pass rechecked only what the fix round changed, against the live files:

- The earlier review's only finding is closed. `plugins/my/tests/test_parallel_runs.py:127-129` writes the message to `self.tmp`, which is outside `self.repo` (`:54-55`). It then runs `locked-commit.py` from `PATH`, which `clean_env` sets to `BIN` (`:30`). The old `LOCKED_COMMIT` constant is gone, and no reference to it is left. The map's note that the test "still uses its own LOCKED_COMMIT constant" is out of date.
- Unstage on failure: `plugins/my/bin/locked-commit.py:43-45`. `git add` failing exits with its own code (`|| exit`). `git commit` failing saves `rc`, runs `git reset -q -- "$@"` and exits `rc`, so D4's "git's own code" still holds. The new test is `plugins/my/tests/test_locked_commit.py` `test_paths_unstaged_when_hook_rejects_commit`. It checks exit 1, that HEAD did not move, that the index is empty and that the message file is kept. The docstring (`locked-commit.py:13-15`) describes the new step.
- Deviation: spec D2 still lists four steps, and D4 says nothing about the unstage. The fix round changed the script's behaviour under the lock but not the design text. This is a justified addition, not a departure, but the spec no longer describes the whole contract. It is the Suggestion row below.
- Risk items 7 and 8 are in the spec (`docs/plans/2026-10-12-locked-commit-spec.md:223-237`). Item 8 lists the parser and symlink limits, so those are not findings here. Item 7's second half rests on a wrong fact; see the second Suggestion row.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Suggestion / High | Spec D2 lists four steps under the lock, and D4 does not say that a failed commit unstages its paths. The script now does a fifth thing on failure, so the spec no longer matches it. The behaviour change is sound. Only the design record lags. | `docs/plans/2026-10-12-locked-commit-spec.md:82-87`, `:123`; `plugins/my/bin/locked-commit.py:13-15`, `:44` | Add one line to D2, or to D4's "other" row: "when the commit fails, `git reset -q -- <paths>` runs under the lock, and the exit is git's code". |
| Suggestion / High | Risk 7 says `~/.claude/rules/docs-layout.md` is "a plain copy, not a symlink", and asks for a manual "copy or relink" after the merge. The file itself is a regular file, but the folder `~/.claude/rules` is a symlink to `/home/dchris/projects/claude-setup/global/rules`. So the file resolves to the main checkout's `global/rules/docs-layout.md` and goes live at the squash-merge, the same as `CLAUDE.md`. The manual step is not needed. The first half of Risk 7 (the plugin update) still holds, and it now covers `docs-layout.md` too. | `ls -la ~/.claude/rules` shows `-> /home/dchris/projects/claude-setup/global/rules`; `readlink -f ~/.claude/rules/docs-layout.md` shows the repo path; spec `:226-228` | Reword Risk 7: both files go live at the merge; the only manual step is updating the `my` plugin. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| One lock implementation, reused through `os.execv` and not copied | `plugins/my/bin/locked-commit.py:42`, `:105-107`; `plugins/my/bin/handoff-lock.py:71-77`, `:92-103` | Strong |
| A failed commit no longer leaves paths staged in the shared main checkout. This root cause matters in a parallel project, where the next run's squash-merge refuses when anything is staged (`SKILL.md` squash command) | `locked-commit.py:44`; `test_locked_commit.py` hook-rejection test | Strong |
| The exit code is kept through the unstage step (`rc=$?` ... `exit $rc`), so D4 and stop rows 18 and 23 still read the right code | `locked-commit.py:44` | Strong |
| The integration test now exercises the prescribed path: two runs share one `main` and commit their `done` marks through the script | `plugins/my/tests/test_parallel_runs.py:121-130` | Moderate |
| The whole suite passes, 145 tests, run in this review | `python3 -m unittest discover plugins/my/tests` | Moderate |
| The main rollout risk is recorded: global rules go live before the installed plugin has the script | spec Risk 7, first half | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| The spec's design text (D2/D4) lags the fix round's unstage step | `docs/plans/2026-10-12-locked-commit-spec.md:82-87` | Low |
| Risk 7 prescribes a manual relink that the symlinked `~/.claude/rules` folder makes unneeded | spec `:226-228` | Low |

## Not Applicable

None.

## Reasoning

The approach is unchanged and still right: one script, one lock implementation, and no shell reads the message. The fix round treats a real cause: a failed commit no longer leaves staged paths in the checkout other runs share, and git's exit code is kept. The earlier finding is closed by a test that runs the real script, and callers were found by text search only, since this review had no symbol tool. What remains are two wording gaps in the spec, not flaws in the code.

## Verdict

**Assessment:** Sound
**Confidence:** High. I read the live script, the lock it runs, both test files and the changed `SKILL.md` step, and the full suite passes.
**Recommendation:** Squash-merge. If you want the spec to match the script, first add the unstage step to D2 or D4 as one line, and reword Risk 7 so its only manual step is the plugin update. Per the one-fix-round rule, both are optional. After the merge, update the `my` plugin.
