# Review: main..feat/parallel-auto-runs

**Status:** review of main..feat/parallel-auto-runs, 2026-10-12. Mixed: the scripts and the stage text are sound, but the new rule text says a backtick in a commit message is safe in the locked commit form, and that is false for a double-quoted message.

## Change Summary

The branch adds `handoff-lock.py`, which runs one command under a named `flock` lock. That lock is shared by the main checkout and its worktrees. `handoff-state.py` gains `live`, `start` (a cap on live auto runs) and `merge` (a squash that refuses when the base gained code after `checked_base`), plus three fields and the `merge-retry` step. `git-fold-fixups.py` now refuses to give a new hash to a commit that a docs file cites. The rest is prompt text: the handoff `SKILL.md` stages, `global/CLAUDE.md`, `docs-layout.md`, `/my:commit`, `my:architect`, and the README and ROADMAP rows.

Caller sweeps were plain text searches (`grep -rn`). No symbol tool was available.

## Plan Alignment

The implementation matches the plan task by task. Tasks 1 to 9 are present, and the file map matches the diff. Task 10 was not run, by the user's choice, and the plan records why. Deviations:

- `plugins/my/commands/commit.md:11` uses `git rev-parse --path-format=absolute --git-dir` / `--git-common-dir`, where the plan's Task 8 Step 3 wrote the bare form. This is justified: without `--path-format=absolute`, the two outputs differ in form even in the main checkout.
- `plugins/my/tests/test_parallel_runs.py` finds the spec commit with `--diff-filter=M --grep …`, where the plan wrote `--diff-filter=A`. This is justified: the fixture's root commit adds both specs, so `A` would find the root commit.
- Plan Decision 10 adopts the `$1` form so that "an apostrophe … and a backtick" in a message are safe. The form fixes apostrophes only. See the first row below: the goal of the decision is only half met.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / High | The rule text says a backtick in the message is safe in the locked commit form. It is not. `"<message>"` is double-quoted, so the outer shell runs anything in backticks or `$(…)` before `handoff-lock.py` starts. That happens outside the lock, in the main checkout. Checked: `bash -c 'printf "%s\n" "msg with \`echo RAN\` here"'` prints `msg with RAN here`. `global/CLAUDE.md` gives no safe form at all. It says that a message with a body is "one quoted argument with real newlines", and bodies on `main` often hold backticks (40 lines in the last 300 commits). The same hazard applies to `handoff-state.py merge <slug> -m "<message>"` and to the supervised squash. This is plan Decision 10's stated goal, left half met (Soundness of approach; Plan alignment). | `global/CLAUDE.md:173`; `plugins/my/skills/handoff/SKILL.md:562-567`, `:800`, `:862`; `plugins/my/commands/commit.md:11`; `global/rules/docs-layout.md:173`; `plugins/my/skills/architect/SKILL.md:252` | Always pass the message as `"$(cat <<'EOF' … EOF)"`, one-line messages included, or as a single-quoted argument. Remove the claim that a backtick is safe. Name the quoted heredoc in `global/CLAUDE.md` and `docs-layout.md` too, because they are read alone. |
| Suggestion / High | The replacement reread `git diff -- <paths>` does not show untracked files. A new brief, review or plan that is committed with the locked form is never reread, but the Edit-tool reason for the reread applies to new files too. Only handoff `SKILL.md` says this, for the plan stage. The global rule says the replacement covers "every `git diff --cached` reread this file names". | `global/CLAUDE.md:172`; `global/rules/docs-layout.md:176`; `plugins/my/commands/commit.md:11`; contrast `plugins/my/skills/handoff/SKILL.md:557-559` | Add one clause: read each new file whole before the locked command (or run `git diff --no-index /dev/null <file>`). |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| The lock has the right scope and lifetime. It uses the git common dir, so the main checkout and every worktree share it. It is inherited across `exec`, so the kernel frees it when the command ends. A detached `gc` cannot keep it. Tests cover a timeout, a kill, worktree sharing and pass-through of exit codes. | `plugins/my/bin/handoff-lock.py:70-76`, `:91-102`, `:123-125`; `plugins/my/tests/test_handoff_lock.py` | Strong |
| The cap check and the state write happen in one locked step, so two starts cannot both pass the cap. A concurrency test runs 4 locked starts against `--max 2`. An unreadable state counts as live, which fails safe. | `plugins/my/bin/handoff-state.py:169-222`; `test_handoff_state.py` `test_concurrent_locked_starts_never_pass_the_cap` | Strong |
| `merge` does every check, the squash and the state writes inside one lock. It compares against `checked_base` (the code the checks saw), not the base's tip. It rolls back with `git reset --merge` inside the lock. A crash after the commit is still recovered by the existing `check` promotion from `merge` to `worktree-remove`. | `plugins/my/bin/handoff-state.py:356-397`, `:336-342` | Strong |
| The fold's citation refusal fixes a real hazard in every project. Before it, a fold could rehash a squash commit that another feature's `done` mark cites. `check` shares the rule, so the fixup-or-normal-commit choice in docs-layout steps 4 and 8 degrades gracefully. | `plugins/my/bin/git-fold-fixups.py:190-228`; `global/rules/docs-layout.md:149-157` | Strong |
| The cross-feature contract with `my:status` holds. `print_live` emits slug, slot, next, stopped and branch separated by tabs, with `unreadable` in the third field. That is exactly what `status-scan.py` splits and checks. | `plugins/my/bin/handoff-state.py:191-198`; `plugins/my/bin/status-scan.py:185-212` | Strong |
| No orphaned callers. The changed signatures (`refusal`, `range_refusal`, `check_refusal`) are module-internal. Every list of `next` values outside the tests now includes `merge-retry`. The existing callers of the fold pass no `--docs-paths` and get the default list. | text sweep for `range_refusal`, `check_refusal`, `worktree-remove`, `git-fold-fixups.py` | Moderate |
| Projects without the section are left almost unchanged. Only the locked start with `--max 1` and the fold refusal apply there. Every other change sits in a paragraph headed **With a "Parallel runs" section,**, which matches the file's existing **In auto mode,** pattern. | `plugins/my/skills/handoff/SKILL.md:150-153` region, `:540`, `:555`, `:589`, `:628`, `:665`, `:711`, `:751`, `:788`, `:849` | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| The message quoting claim is false for backticks and `$(…)`. A command can run in the main checkout outside the lock. | `global/CLAUDE.md:173`; `plugins/my/skills/handoff/SKILL.md:565` | Medium |
| The supervised squash runs `git reset --merge` as a separate step after the lock is released. A conflicted index can briefly sit outside the lock. Other runs' guards (`SQUASH_MSG` in `IN_PROGRESS`, and `git commit` refusing unmerged paths) turn this into a stop of the other run, not a corruption. | `plugins/my/skills/handoff/SKILL.md:800-803`; `plugins/my/bin/handoff-state.py:92` | Low |
| `SKILL.md` stage text has no automated test, and the rehearsal did not run. The Risk section already lists this. | plan Risk; plan Testing Strategy | Low |

## Not Applicable

None.

## Needs Investigation

- **The locked merge against the Bash tool's 120 s limit.** `handoff-lock.py` waits up to 90 s. The locked command's own run time comes on top, and that includes the project's commit hooks in the main checkout. No stage text raises the Bash `timeout` for the locked merge or commit. If the tool kills the command mid-commit, git can leave `index.lock` behind, and every later run then fails on it. I could not check this, because it depends on each project's hooks. To resolve it, give the locked `merge` and commit calls an explicit Bash `timeout`, or confirm that no target project has slow hooks.

## Reasoning

The scripts treat the root problem: one lock for every write to the main checkout, a cap check that is atomic with its write, and a merge that compares against the base the checks actually saw. The tests, including the two-run integration test, cover each of these. The one surfaced Warning is in the rule text that every session reads. The locked form's promise that a backtick is safe is wrong, and the global rule offers no safe form for bodies, which on `main` often hold backticks. The fix is a wording change in six places, not a rework, so the approach stands.

## Verdict

**Assessment:** Mixed
**Confidence:** High — the Warning was reproduced in a shell, and the affirmative rows were checked against the scripts and their one external consumer.
**Recommendation:** In this branch's one fix round, change every locked-form instruction to pass the message through the quoted heredoc (or single quotes), and delete the "a backtick in it is safe" claim. Add the new-file reread clause at the same time. Then merge.
