# Review: main..feat/autonomous-run

**Status:** review of main..feat/autonomous-run, 2026-10-12. Mixed: the fix round answers all three earlier findings, but its new `history rewritten` check also refuses a resume after a fold that succeeded, so a crash between the fold and `set next=done` can no longer be resumed.

## Change Summary

The branch adds an auto mode to `my:handoff`:

- A `PreToolUse` hook blocks `git push` when `MY_AUTORUN` is set (`plugins/my/hooks/block-autorun-push.py`).
- A state helper keeps `<git common dir>/my-handoff/<slug>.json` and checks it against git (`plugins/my/bin/handoff-state.py`).
- Prompt text in `plugins/my/skills/handoff/SKILL.md` adds the auto forms, Delegation, the start checks, the 17-row stop table, the state writes and `resume`.
- The docs and the plan's Risk section and Testing Strategy are updated to match.

The fix round, the branch's last four commits, made these changes:

- `SQUASH_MSG` is added to the in-progress list, and the `merge` facts gained `staged changes in the main checkout`.
- A `history rewritten` check was added for `next=fold`.
- `merge done` now writes the state only after the `worktree-remove` facts pass.
- `resume` prints `stopped` before it clears it.
- The guard no longer treats `#` as a comment, and it skips shell keywords and value options such as `--git-dir`.

Method note: I had no symbol-reference tool, so every caller sweep was a text search (`grep -rn`). The branch only adds symbols and removes or renames none, so no caller can be left orphaned. I checked the fix round's behaviour in scratch repositories with the branch's own scripts.

## Plan Alignment

The implementation matches the plan task by task, as the first review found. Every fixed copy string from Global Constraints is present. The fix round adds behaviour that the plan's Task 2 Interfaces does not list. These are justified deviations: the first review asked for them.

- `plugins/my/bin/handoff-state.py:58`: `SQUASH_MSG` is added to the in-progress files. The plan's Task 2 step 3 lists five files without it.
- `plugins/my/bin/handoff-state.py:194` and `:211`: two new mismatch lines, `staged changes in the main checkout` and `history rewritten: …`. The plan's Interfaces says the mismatch lines are "exactly" the twelve it lists, and the spec's D6 `check` paragraph does not mention them either. The plan and the spec were not updated. This is below the surfacing bar, because the script's docstring and the handoff README (`plugins/my/skills/handoff/README.md:294-297`) describe the new behaviour.
- `plugins/my/skills/handoff/SKILL.md:262-263`: Resume prints the earlier stop but does not ask for a confirmation. The first review offered "print and confirm" or "have `check` refuse the exit-3 fold". The fix round chose the printing plus the check. That is sound for the concrete case: `git-fold-fixups.py:28-30` says exit 3 leaves history rewritten, so `check` now refuses it.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / High | The new `history rewritten` check cannot tell a fold that succeeded from one that failed after its rebase. Every successful fold rewrites `head_before_fold` out of `<base>`. So a crash, reboot or closed window between the fold's exit 0 and `set next=done` leaves `next=fold`, and every later `resume` is refused. I reproduced this in a scratch repo: `git-fold-fixups.py` printed `folded 1 fixups`, exit 0, then `check` printed `history rewritten: head_before_fold … is not on main`, exit 1. Before the fix round, the same crash resumed correctly: the review stage found no waiting fixups and set `done`. The refusal is safe, because nothing is corrupted. But no document says how to get out of it. The message, read next to the fold's own "`git reset --hard <old HEAD>` undoes it", steers the user towards undoing a good fold. The test fakes a rewrite with a reset and a new commit, and never runs a successful fold. | `plugins/my/bin/handoff-state.py:206-212`, `plugins/my/bin/handoff-state.py:26-27`, `plugins/my/skills/handoff/SKILL.md:664-667`, `plugins/my/skills/handoff/README.md:295-296`, `plugins/my/tests/test_handoff_state.py:279-289` | Use the same pattern as `merge done`. When `head_before_fold` is not an ancestor of `<base>`, accept the fold as done if `git diff <head_before_fold> <base>` is empty and no fixup of `spec` or `task_doc` waits. Then print `fold done` and set `next=done`. Refuse otherwise: exit 3 leaves either fixups or a changed tree. Base commits made after the fold by other sessions would make the diff non-empty and give a refusal, which is safe. If the user does not want a fix now, record it in Risk, together with the manual way out (`handoff-state.py set <slug> next=done head_before_fold=` after reading `git log`). |
| Suggestion / High | The fix round's `lexer.commenters = ""` turns a comment that contains an apostrophe into a parse failure. The fallback then blocks any text with the words `git` and `push`. `git status  # don't push yet` is valid bash, but the guard now blocks it (exit 2, checked). The first version of the guard kept shlex's default `#` comments and allowed it. This is a false block, in the safe direction, and it never lets a push through. But it makes the plan's Risk sentence "a parse failure that mentions `git` and `push` blocks a command that bash would refuse anyway" untrue. | `plugins/my/hooks/block-autorun-push.py:55`, `plugins/my/hooks/block-autorun-push.py:16-17`, plan Risk item 4 (`docs/plans/2026-10-12-autonomous-run.md:841-844`) | Correct the Risk sentence: a comment with an unbalanced quote is also blocked. Or, before tokenizing, strip a `#` comment that starts a word outside quotes. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| The staged-squash finding is answered at the right layer: `check` refuses `SQUASH_MSG` for every step and staged changes for `merge`, and a unit test runs the real `git merge --squash`. Row 15's `git reset --merge` removes `SQUASH_MSG` (checked), so the new in-progress entry does not block a resume after a conflict stop | `plugins/my/bin/handoff-state.py:58`, `:192-194`, `plugins/my/tests/test_handoff_state.py:272-277` | Strong |
| The exit-3 fold, the concrete case behind the earlier `stopped` finding, is now refused by `check`, and Resume prints the stop reason before it clears it | `plugins/my/bin/handoff-state.py:206-212`, `plugins/my/skills/handoff/SKILL.md:262-264`, `plugins/my/bin/git-fold-fixups.py:28-30` | Strong |
| `merge done` now writes the state only after the `worktree-remove` fields and facts pass, and a test proves that a refused check leaves `next` unchanged | `plugins/my/bin/handoff-state.py:236-241`, `plugins/my/tests/test_handoff_state.py:291-296` | Strong |
| The other stop rows recur after a resume, so a printed but unconfirmed stop is not passed over silently. Row 13 at `next=review` meets the "fix round already ran" stop, rows 15 and 16 check the tree again, and rows 4 and 6 meet the same decision again | `plugins/my/skills/handoff/SKILL.md:301-305`, `:661-663` | Moderate |
| The guard's new tests cover comments, keywords and `--git-dir` in both directions, and the no-`MY_AUTORUN` path still exits before it reads stdin | `plugins/my/tests/test_block_autorun_push.py:39-49` | Moderate |
| Resume after the merge works on the right facts: worktree steps are skipped when the worktree is gone | `plugins/my/skills/handoff/SKILL.md:283-285`, `:659-660` | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| A fold that succeeds and is then interrupted cannot be resumed, and the refusal message points towards undoing it | `plugins/my/bin/handoff-state.py:206-212` | Medium |
| The full-cycle rehearsal ran before the fix round, so the fix round's changes to `check`, Resume and the guard rest on unit tests only | plan Testing Strategy, "Rehearsal, 2026-10-12" | Low |
| The fix round's guard change adds a false block that the Risk text says cannot happen | `plugins/my/hooks/block-autorun-push.py:55` | Low |

## Not Applicable

None.

## Needs Investigation

- **The rehearsal does not cover the fix round.** The rehearsal results were committed before the four fix-round commits. So "Resume (`resw`): pass" tested Resume and `check` before the `SQUASH_MSG`, staged-changes, `history rewritten` and print-before-clear changes. The `resw` path is `next=fold` with a fold still to run, so `head_before_fold` is not yet set when `check` runs. The unit tests suggest it would still pass, but no full run shows it. One `resw`-style run on the branch head would settle it.

## Reasoning

The approach is still right, and the fix round answers each earlier finding at the right layer, with a test for each. One of those answers, the `history rewritten` refusal, is too broad. It catches the exit-3 fold it was meant for, and it also catches every successful fold whose next state write was lost. That turns a crash that used to be recoverable into a refusal with no documented way out. The refusal is safe, but it breaks the D7 promise that `resume` continues a run after a crash at any step. That is a Warning, not a Critical, so the verdict is Mixed. The guard change is a small regression in the safe direction.

## Verdict

**Assessment:** Mixed
**Confidence:** High — I reproduced both surfaced findings with the branch's own scripts in scratch repositories.
**Recommendation:** This re-review is final under the one-fix-round rule, and it found no new Critical. So both rows go into the plan's **Risk** section as known limits, unless the user chooses to fix the fold check now. For the fold, write the manual way out: read `git log`, then `handoff-state.py set <slug> next=done head_before_fold=`. For the guard, correct the Risk sentence. The API-stall decision in Open Questions is still open and must be answered before the squash-merge.
