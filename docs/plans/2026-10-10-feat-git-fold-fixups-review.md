# Review: main..feat/git-fold-fixups

**Status:** review of main..feat/git-fold-fixups, 2026-10-10. Mixed: the script and the move are sound and match the spec, but `check <sha>` reports a fixup of an already pushed commit as safe, and that fixup then blocks every later fold on the branch, with no way out except a manual history edit.

## Change Summary

The branch adds `plugins/my/bin/git-fold-fixups.py`, which has two commands. `check <sha>` tells whether a fixup of a commit is safe. With no argument, it folds every waiting `fixup!` commit on the current branch, or refuses with one line and changes nothing. There are 19 subprocess tests for it. The fourteen "One feature, four commits on `main`" steps move from `global/CLAUDE.md` into `global/rules/docs-layout.md`, and steps 4, 8 and 9 now call the script. `my:handoff` (SKILL.md and README.md) and the repo README name the script in place of the old prose fold.

## Plan Alignment

The implementation matches the spec (D1 to D7, Tasks 1 to 6). I checked these points:

- D2 and `check`: `plugins/my/bin/git-fold-fixups.py:58-71` and `:213-218` do what D2 says. They use `for-each-ref --contains … %(worktreepath)`, skip the current worktree and rows with no worktree path, and exit 1 when a worktree holds a branch. The top finding below is a gap in D2 itself, not a deviation from it.
- D3, D4 and D5: `:89-105`, `:132-160` and `:163-194` match. The order of the refusals differs from the D4 numbering, but the spec's Risk section records that choice, together with `rebase.updateRefs=false` and exit `2` for a bad argument.
- D6: the new section in `global/rules/docs-layout.md:130-171` holds the steps. Steps 4, 8 and 9 have the text the spec gives. The bullets "Before every fixup" and "Before every rebase" are gone. "No commit only changes a status" and "Cite only commits on `main`" moved. `global/CLAUDE.md:168-174` has the pointer paragraph word for word, the paragraph "Before step 1" and the renumbered `docs:` bullet. `CLAUDE.md:61` and `:78` changed as D6 says. The Task 4 grep finds one heading in each file.
- D7: `plugins/my/skills/handoff/SKILL.md:217-231` and `:345-353` name both signals, for exit `1` and exit `3`. The Task 5 grep for `GIT_SEQUENCE_EDITOR\|rebase -i` in `plugins/my/skills/handoff/` finds nothing.
- Task 1: every test the spec lists exists in `plugins/my/tests/test_git_fold_fixups.py`.
- Task 6: the README paragraph is present. The ROADMAP rows are outside the range (Task 6 puts them in the spec commit). The `~/bin` symlink and the zitamu sentence are post-merge steps, so they are not missing.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / High | `check <sha>` only tests whether a worktree holds the commit. A target that is already on `@{upstream}` passes `check` (exit 0), so step 4 or 8 makes a fixup. The fold then refuses it (D4.5). The fold handles every waiting fixup at once, so that one refusal also blocks every other, safe fixup on the branch. The "Fold scope" risk does not cover this: a held-worktree refusal clears when the branch merges, but a pushed-target refusal never clears by itself. In zitamu the stuck fixup also cannot be pushed, because the `pre-push` hook refuses `fixup!` commits. Realistic path: the user pushes `main` after the spec commit ("pushes at their own pace"), then the `approved` status or a review edit is made as a fixup. Reproduced in a scratch repo: `check` on a pushed target exited 0. Then one fixup of the pushed target and one fixup of an unpushed commit made the fold exit 1 with `already pushed to origin/main`. | `plugins/my/bin/git-fold-fixups.py:213-218` (check calls only `held_branches`); `:150` (the fold's upstream refusal); `:94-97`; `global/rules/docs-layout.md:152-160`; `~/projects/zitamu/real-estate-webapp/.git/hooks/pre-push:9-11` | Make `check` also exit 1 when the target is an ancestor of `@{upstream}`, with an `already pushed` line. Steps 4 and 8 already say "exits 1 → normal commit", so the rule text needs no change. This changes the D2 contract, so it needs the user's decision. If the user declines, record the gap in the spec's **Risk** section. |
| Warning / Medium | The zitamu `pre-push` hook is outside the spec's blast-radius list. Its header names `~/.claude/CLAUDE.md`, Git Workflow, for the steps, which have now moved. Its refusal message tells the agent to run the bare `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash <oldest-target>^ (step 9)`, which skips every check the script adds. An agent that follows the hook bypasses D4. | `~/projects/zitamu/real-estate-webapp/.git/hooks/pre-push:2,11`; the spec's Risk section, "Blast radius" bullet | After the merge, together with the zitamu sentence of D6: point the hook's message at `git-fold-fixups.py` and its header at `~/.claude/rules/docs-layout.md`. Add the hook to the spec's blast-radius list. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| The fold refuses before it changes anything. Every D4 rule runs before the rebase, and a failed rebase is aborted only when one is in progress, so a `pre-rebase` hook refusal is handled. | `plugins/my/bin/git-fold-fixups.py:132-160`, `:170-176`; tests `test_conflict_aborts_and_restores_head`, `test_pre_rebase_hook_refusal_restores_nothing_to_abort` | Strong |
| The post-check catches a rebase that went wrong without failing: a fixup left in the range, or a tree that differs. It exits 3 and prints the full old HEAD, and never resets. | `:177-194` | Strong |
| The script is robust to user config: `GIT_SEQUENCE_EDITOR` overrides `sequence.editor`, and `rebase.updateRefs=false` keeps the kept merged branches from moving. The tests run with no global or system config. | `:167-168`; `plugins/my/tests/test_git_fold_fixups.py:20-25` | Moderate |
| The rebase starts at the oldest target's parent, with `--root` when the target is the root commit. A worktree branch that contains any rewritten commit also contains a target, so checking the targets covers the whole range. | `:126-129`, `:146-149`, `:166-169` | Strong |
| One copy of the logic replaces two prose copies (CLAUDE.md step 9 and the handoff fold). The script sits in the same `bin/` folder as its siblings, uses only the standard library and has a Usage docstring. That folder is already on the session PATH through the directory-source plugin. | `plugins/my/bin/md-expand-table.py:1-18`; `plugins/my/skills/handoff/SKILL.md:225-231` | Strong |
| The move keeps every reference working. The heading stays in `CLAUDE.md`, and the pointer names the rule file. Steps 12 and 13 are cited by file name, because a session that finishes a branch may not touch `docs/plans/`. | `global/CLAUDE.md:78`, `:168-170` | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| `check` and the fold disagree about a pushed target. A fixup that `check` approves can block every later fold. | `plugins/my/bin/git-fold-fixups.py:150`, `:213-218` | Medium |
| A hook outside the repo still tells the agent to run the unchecked rebase. | `~/projects/zitamu/real-estate-webapp/.git/hooks/pre-push:11` | Medium |

## Not Applicable

None.

## Needs Investigation

- **A user-level rule loading for a new file.** The spec's Risk section lists this as untested, so it is not a finding. It still matters, because steps 1 to 3 run before any file in `docs/plans/` exists or has been edited. The pointer in `global/CLAUDE.md:170` ("read it if it has not loaded") is the fallback. The first real spec written after the merge will show whether the rule loads on the `Write`.

## Reasoning

The script does what D1 to D5 describe, refuses before it changes anything, and its post-checks cover a rebase that went wrong without failing. The tests cover each refusal through the real command. The move of the steps keeps every reference working, and the handoff edits match D7. The one design gap is that `check` and the fold judge a pushed target differently. That turns a safe-looking fixup into a refusal that never clears and blocks other fixups. It is a spec-level contract choice, not a code error, and a one-condition change fixes it, so the approach stands and the verdict is Mixed, not Problematic.

## Verdict

**Assessment:** Mixed
**Confidence:** High — I reproduced the top finding in a scratch repo, and I checked plan alignment against the spec's own grep checks.
**Recommendation:** Ask the user whether `check` should also refuse a target already on `@{upstream}`. If yes, add the condition and a test such as `test_check_refuses_pushed_target` before the merge. If no, record the gap in **Risk**. After the merge, update the zitamu `pre-push` message along with the D6 sentence.
