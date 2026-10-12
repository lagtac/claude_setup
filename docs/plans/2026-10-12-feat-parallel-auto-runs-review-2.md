# Review: main..feat/parallel-auto-runs

**Status:** review of main..feat/parallel-auto-runs, 2026-10-12. Mixed: both findings of the first review are fixed, but the three heredoc blocks in handoff `SKILL.md` that the fix round added keep the closing `EOF` indented inside a list item, and bash rejects that form when it is copied as written.

## Change Summary

This is the final re-review after one fix round. The branch adds `handoff-lock.py`, which runs one command under a named `flock` lock that the main checkout and its worktrees share. `handoff-state.py` gains `live`, `start` and `merge`, three fields and the `merge-retry` step. `git-fold-fixups.py` refuses to give a new hash to a commit that a docs file cites. The rest is prompt text: the handoff `SKILL.md` stages, `global/CLAUDE.md`, `docs-layout.md`, `/my:commit`, `my:architect`, the handoff README, README and ROADMAP. The fix round passes every locked-commit message through a quoted heredoc, lists the commit with `git show --stat` inside the lock, and asks the reader to read new files whole. It also has the fold read docs paths from the repo root, rejects non-finite lock timeouts, and makes the supervised squash refuse staged changes and reset inside the lock.

Caller sweeps were plain text searches (`grep -rn`, `git grep`). No symbol tool was available. The unit tests were run: 128 pass.

### The two earlier findings

- **Finding 1 (a backtick in a double-quoted message runs outside the lock): fixed.** Every locked form now passes the message as `"$(cat <<'EOF' … EOF)"`. See `global/CLAUDE.md:173`, `global/rules/docs-layout.md:174-177`, `plugins/my/commands/commit.md:11`, `plugins/my/skills/architect/SKILL.md:252-255`, and `plugins/my/skills/handoff/SKILL.md:565-568` (plan-stage commit), `:807-810` (supervised squash) and `:874-877` (auto `merge`). The false safety claim is gone: `SKILL.md:571-573` now says that the heredoc is used even for one line. `global/CLAUDE.md:173` explains why plain double quotes are unsafe. I checked this in bash 5.2: a message holding an apostrophe, a backtick, `$(echo …)`, an unbalanced `)` and a `"` comes through literally, and nothing runs.
- **Finding 2 (new files were not reread before a locked commit): fixed.** See `global/CLAUDE.md:172` ("and each new file whole … `git diff` does not show a file git does not track yet"), `global/rules/docs-layout.md:180`, `plugins/my/commands/commit.md:11`, `plugins/my/skills/architect/SKILL.md:258` ("Read the brief whole before the command") and `plugins/my/skills/handoff/SKILL.md:560-561`.

## Plan Alignment

The implementation matches the plan task by task. Tasks 0 to 9 are present, and the file map matches the diff. Task 10 was not run, by the user's choice. The plan records this in its Testing Strategy, so it is not a finding. Deviations:

- `plugins/my/skills/handoff/SKILL.md:565`, `global/CLAUDE.md:173` and the other locked forms use the quoted heredoc and `git show --stat --format= HEAD` inside the lock. Plan Decision 10 and Task 8's Interfaces line give the bare `sh "<message>" <paths>` form. The change is justified, because it is the fix for the first review's finding 1. But the plan text was not updated (see the Suggestion row).
- `plugins/my/skills/handoff/SKILL.md:807` changes the supervised squash. It refuses on staged changes and runs `git reset --merge` inside the lock. Plan Decision 7 gives a plainer command with a double-quoted message and the reset outside the lock. The change is justified and strengthens Decision 7, but the plan text is stale here too.
- `plugins/my/commands/commit.md:11` uses `--path-format=absolute`, and `plugins/my/tests/test_parallel_runs.py` uses `--diff-filter=M`. Both deviations are carried over from the first review and are justified there.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / Medium | New in the fix round. The three heredoc blocks in handoff `SKILL.md` are nested in list items, so in the raw file the closing `EOF` line starts with 2 to 5 spaces. A `<<'EOF'` heredoc ends only on a line that is exactly `EOF`. A session that copies the block as written gets a bash syntax error. I checked this: `here-document … delimited by end-of-file`, then `unexpected EOF while looking for matching ')'`, exit 2. That stops every locked plan commit, `done` mark, auto merge and supervised squash in a parallel-runs project. It fails safe, because nothing runs, but the run stops. If a session strips the indent from `EOF` and not from `<message>`, the commit message gets leading spaces. No skill on `main` uses an indented heredoc terminator (`git grep -nE '^ +EOF' main -- plugins global` finds nothing), so there is no earlier evidence that sessions strip it. `docs-layout.md` and `architect/SKILL.md` put the block at column 0 and are not affected. Medium confidence, because a model may treat list indentation the way CommonMark does and strip it. (Soundness of approach.) | `plugins/my/skills/handoff/SKILL.md:565-568`, `:807-810`, `:874-877` | Add one clause by each block: "the `<message>` and `EOF` lines start at column 0". Or move the three blocks out of the list indentation, as `docs-layout.md:173-178` does. |
| Suggestion / High | The plan still records the forms that the first review proved unsafe. Decision 10 says that passing the message as `"<message>"` in `$1` makes a backtick safe. Decision 7 shows the supervised squash with a double-quoted message and the reset outside the lock. Task 8's Interfaces line repeats the Decision 10 form. The plan stays on `main` as the record, and a reader who copies from it gets the unsafe form. (Plan alignment.) | plan copy, Decision 10 (lines 139-147), Decision 7 (lines 122-125), Task 8 Interfaces (lines 962-964) | In the `done` commit, or in a plan edit before the merge, change those three places to the heredoc forms that the rule files now use. Or add one line under Decision 10 that says the fix round replaced it, and points to `global/CLAUDE.md:173`. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| The fix round treats the root cause of finding 1, not a symptom. The message never passes through shell parsing outside the quoted heredoc, and the safety claim was corrected. A shell test confirms that nothing in the message runs. | `global/CLAUDE.md:173`; `plugins/my/skills/handoff/SKILL.md:571-573` | Strong |
| `git show --stat --format= HEAD` runs inside the lock, after `&&`. The listed commit is the one this command made, even when another run commits right after. This closes a race that a separate `git show` after the lock would leave open. | `plugins/my/skills/handoff/SKILL.md:565`, `:574-576` | Strong |
| The supervised squash now refuses staged changes and resets inside the lock. This removes the first review's Low "conflicted index outside the lock" problem. | `plugins/my/skills/handoff/SKILL.md:807`, `:813-815` | Strong |
| The lock's scope and lifetime are right: the git common dir, an fd inherited across `exec`, gc detaching turned off, and non-finite timeouts rejected. Tests cover a timeout, a kill, worktree sharing, exit-code pass-through and bad timeouts. | `plugins/my/bin/handoff-lock.py:70-76`, `:93-103`, `:123-125`; `plugins/my/tests/test_handoff_lock.py` | Strong |
| The cap check and the state write run in one locked step. `merge` does its checks, the squash and the state writes under one lock, against `checked_base`. A concurrency test and a two-run integration test, in both orders, use the real scripts. | `plugins/my/bin/handoff-state.py:169-222`, `:356-397`; `plugins/my/tests/test_parallel_runs.py` | Strong |
| The fold's citation search now uses `:(top)` pathspecs, so it works from any folder. A test pins this. | `plugins/my/bin/git-fold-fixups.py:192-193`; `test_git_fold_fixups.py` `test_fold_from_a_subfolder_still_refuses` | Strong |
| The cross-feature contract with `my:status` holds. `print_live` emits five fields separated by tabs, with `unreadable` in the third field, which is what `status-scan.py` splits and checks. | `plugins/my/bin/handoff-state.py:191-198`; `plugins/my/bin/status-scan.py:185-212` | Strong |
| There are no orphaned callers. The changed signatures (`refusal`, `range_refusal`, `check_refusal`) are module-internal. Every list of `next` values outside the tests includes `merge-retry`. The existing callers of the fold get the default docs paths. | text sweep of the map file and the repo | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| A block copied as written fails, because its indented `EOF` is not a terminator. This is the auto path's only commit and merge form. | `plugins/my/skills/handoff/SKILL.md:567`, `:809`, `:876` | Medium |
| The plan's Decisions 7 and 10 still show the unsafe forms. | plan copy lines 122-125, 139-147 | Low |
| `SKILL.md` stage text has no automated test, and the rehearsal did not run. The plan's Risk section and Testing Strategy already record this. | plan Risk; plan Testing Strategy | Low |

## Not Applicable

None.

## Reasoning

The scripts treat the root problem, and the tests cover them. The fix round fixes both of the first review's findings at the cause: the heredoc quoting, the commit listed inside the lock, and new files read whole. It also tightens the supervised squash. What is left is a small text defect that the fix round itself introduced. The new heredoc form is safe in the two files that place it at column 0, but in handoff `SKILL.md`, the file the auto runs follow, it sits inside list items. Copied as written, it is a syntax error. It fails safe, and the fix is one clause or a change of indent, so the approach stands. Because of that Warning, the verdict is Mixed.

## Verdict

**Assessment:** Mixed
**Confidence:** Medium. The syntax error was reproduced in bash, but whether sessions keep the list indentation when they copy a block is uncertain.
**Recommendation:** Before the merge, put the `<message>` and `EOF` lines of the three handoff `SKILL.md` heredoc blocks at column 0, or say so beside each block. This is a text fix, not a code change. Under the one-fix-round rule, the user can also take it as a known limit in the plan's Risk section. Update plan Decisions 7 and 10 to the heredoc forms when the `done` marks are written.
