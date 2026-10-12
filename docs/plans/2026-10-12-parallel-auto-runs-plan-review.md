# Review: docs/plans/2026-10-12-parallel-auto-runs.md

**Status:** review of docs/plans/2026-10-12-parallel-auto-runs.md, 2026-10-12. Mixed: the plan is well grounded and follows the spec, but several snippets cannot work as written; the top one is the Task 1 lock test, which a correct lock script fails because `dash` forks `sleep` and the child keeps the lock. Answered in the plan: every snippet finding is fixed, Decision 10 passes the commit message as an argument, and the user chose a stateless base-moved check for supervised merges (Decision 7).

## Change Summary

The plan builds the approved parallel-auto-runs spec in eleven tasks. Tasks 1 to 4 add `handoff-lock.py`, the citation refusal in `git-fold-fixups.py`, and the `live`, `start` and `merge` subcommands of `handoff-state.py`, each test first. Task 5 is an integration test, Tasks 6 to 9 change prose (`SKILL.md`, the global rules, `/my:commit`, `my:architect`, the READMEs, `ROADMAP.md`), and Task 10 is a rehearsal that the user starts. The plan adds nine decisions that the spec left open, among them exit codes, the `live` format, the `merge` order of work, and limiting D7 to auto runs.

Scope note: every caller sweep in this review was a plain text search (`git grep`) through Bash. No symbol-reference tool was available.

## Grounding

Most references hold. I checked them against the repo:

- **Line references in the scripts hold:** `range_refusal` at `plugins/my/bin/git-fold-fixups.py:182`, `main` at `:270`, docstring at `:9-24`. `FIELDS`, `STEPS`, `NEEDS`, `facts` and `main` sit at `plugins/my/bin/handoff-state.py:43,45,47,173,256`.
- **Line references in the skill hold:** in `plugins/my/skills/handoff/SKILL.md`, `### Delegation` and its table are at `:85-108`, the stop table at `:141-165`, start check 6 at `:377`, the state block at `:393-395`, and "Never poll" at `:698`.
- **Line references in the rules and docs hold:** `global/CLAUDE.md:60-62,122,170,178`, `global/rules/docs-layout.md:166` (step 14), `plugins/my/commands/commit.md:9`, `plugins/my/skills/architect/SKILL.md:246`, `README.md:107-115`, `ROADMAP.md:35`, and handoff `README.md:331` ("Known problems").
- **The lint counts are as stated:** 16 for `global/CLAUDE.md` and for `architect/SKILL.md`, and 0 for the other six files.
- **The reference sweep matches the file map.** `git grep` for `git-fold-fixups`, `handoff-state`, `never poll` and `git diff --cached` outside `docs/` and `CHANGELOG.md` found no other caller. A second sweep for `git commit` and `--fixup` in `plugins` and `global` found only `git-squasher`. That skill works on a branch and guards `main` (`plugins/my/skills/git-squasher/SKILL.md:49`), so it is not a missing caller.
- **The test fixtures exist:** `StateTestCase.full`, `state`, `get`, `check` and `assertCheck`, plus `SUBJECT` and `commit` (`plugins/my/tests/test_handoff_state.py:23,70-112`). In the fold tests, `FoldTestCase`, `assertRefused`, `head`, `subjects`, `commit` and `run` exist too (`plugins/my/tests/test_git_fold_fixups.py:42-106`).
- **`git reset --merge` behaves as Decision 5 and Task 4 assume.** A probe in the scratchpad (git 2.43.0) ran it after an add/add squash conflict. It removed `SQUASH_MSG`, and `git status --porcelain` then printed nothing.
- **False assumption, Task 2 Step 3:** `git grep -h -o …` prints only the hex words, with no file names. The probe printed `abcdef1`, but without `-h` it printed `HEAD:ROADMAP.md:abcdef1`. The refusal line and `test_fold_refuses_a_cited_commit_after_the_target` need the file name.
- **False assumption, Task 1 Step 1:** the holder `sh -c 'touch "$0"; sleep 30'` runs under `/bin/sh`, which is `/usr/bin/dash` here. Dash forks `sleep` as a child, and the child inherits the lock file descriptor. The probe killed the holder, and the lock was still held.
- **False assumption, Task 10 Step 2:** `tmux -L <socket> new-window …` fails when no server runs on that socket. The probe printed `error connecting to /tmp/tmux-1000/…`.
- **The review-3 open items are settled.** Decision 7 says which merge path applies where. Decision 5 says who sets `next=worktree-remove` after a merge. Decision 6 gives `NEEDS` and the facts for `merge-retry`.

## Issues Surfaced

| Severity / Confidence | Issue | Evidence | Fix |
|---|---|---|---|
| Warning / High | `test_killed_holder_frees_the_lock` fails even when the lock script is correct. The holder is `sh -c 'touch "$0"; sleep 30'`. Dash forks `sleep`, and `sleep` inherits the lock descriptor that the script makes inheritable on purpose. `holder.kill()` kills only `sh`, so the lock stays held for 30 s and the test gets 75. The executor has to redesign the fixture during the green step. | plan Task 1 Step 1 (holder prose, `test_killed_holder_frees_the_lock`); `readlink -f /bin/sh` → `/usr/bin/dash`; the scratchpad probe printed `lock STILL HELD after kill`, and `sleep`'s parent was `sh` | Use `sh -c 'touch "$0"; exec sleep 30'` for the holder. Or start it with `start_new_session=True` and kill it with `os.killpg`. Do the same in the copy in Task 3. |
| Warning / High | Task 2 Step 3 collects cited words with `git grep -h -o -w …`. The `-h` flag drops the file name, but the refusal line of Decision 8 names the file (`is cited in <file>`), and two tests assert `is cited in ROADMAP.md` and `is cited in NOTES.md`. | plan Task 2 Step 3 and Decision 8; scratchpad probe on git 2.43.0: `-h` prints `abcdef1`, and without it `HEAD:ROADMAP.md:abcdef1` | Drop `-h` and split each line `HEAD:<file>:<word>` at the first two colons. |
| Warning / High | Task 5's helpers never write `branch` (or `worktree`) into the state. `start` passes only `spec`, `task_doc` and `next`. `build` creates the worktree but sets nothing, and `checks_pass` sets only `checked_base` and `next`. Decision 5 refuses with exit 1 when `branch` is empty, so the first `finish("a")` fails. The executor would have to invent the missing `set`. | plan Task 5 helpers and Decision 5; `plugins/my/bin/handoff-state.py:50-51` (`branch` is needed from `review` on) | In `build(slug, func)`, add `set <slug> branch=feat/<slug> worktree=<path>`, as the code stage does (`plugins/my/skills/handoff/SKILL.md:533`). |
| Warning / High | Task 10 Step 2 tells the user to type `tmux -L parallel new-window -c <fixture> "…"` for the first run. No server runs on the `parallel` socket yet, so the command fails and the rehearsal cannot start as printed. | plan Task 10 Step 2; probe: `tmux -L <new socket> new-window …` → `error connecting to /tmp/tmux-1000/…`, rc=1 | Print `tmux -L parallel new-session -d -s rehearsal -c <fixture>` first, or make the first run `new-session`, and give the `attach` line. |
| Warning / High | D4's locked form puts the message inside a single-quoted `sh -c` script: `sh -c 'git add -- "$@" && git commit -m "<message>" -- "$@"'`. An apostrophe in the message ends the quote. A backtick or `$(…)` in the message runs as a command under `sh`. Messages here often hold both: in the last 200 messages, 88 lines contain `'` and 39 contain a backtick. Every message also needs a multi-line `Co-Authored-By` trailer, and `/my:commit` writes messages with a heredoc. Decision 7 already passes the message as `"$2"`, so the plan disagrees with itself. Task 8 copies the fragile form into four files that every session reads. | plan Task 8 Interfaces and Decision 7; spec D4 (`docs/plans/2026-10-12-parallel-auto-runs-spec.md:154`); `plugins/my/commands/commit.md:15` (heredoc); `git log --format=%B -200` counts | Pass the message as an argument, for example `sh -c 'm=$1; shift; git add -- "$@" && git commit -m "$m" -- "$@"' sh "<message>" <paths>`, or use `git commit -F <file>`. The form is spec text, so ask the user before changing it. |
| Warning / Medium | Decision 7 limits D7 to auto runs, and a supervised squash-merge "runs no base-moved check". Spec D7 states the guarantee for "the merge" without limiting it to auto mode. In a project with the section, an auto run can merge code between a supervised run's checks and the user's yes, and the untested combination then lands. The plan still says "None changes a D1 to D8 decision", and its Risk section names only that the rehearsal does not cover this merge, not the lost guarantee. | plan Decision 7 and "Decisions this plan adds"; spec D7 (`docs/plans/2026-10-12-parallel-auto-runs-spec.md:204-207`) | Ask the user in the "no silent reinterpretation" form. Either keep the narrowing and add a Risk entry, or run `handoff-state.py merge` for supervised runs too, with `checked_base` set at step 2. |
| Warning / Medium | No test checks that `merge` itself writes `squash_subject`. `ready()` calls `full()`, which already sets `squash_subject=SUBJECT`, so `test_merge_lands_the_squash_and_moves_next` and `test_squash_conflict_resets_and_keeps_next_merge` pass even if `merge` never writes it. Task 7 Step 3 removes the skill's own `set squash_subject`, so a missing write would break the `done` sub-step's lookup by subject, and no test would catch it. | `plugins/my/tests/test_handoff_state.py:99-103` (`full` sets `squash_subject`); plan Task 4 `ready()` and Review Focus item 4; plan Task 7 Step 3 | In `ready()`, pass `squash_subject=` (empty), so the assertions prove that `merge` wrote the first line. |
| Suggestion / High | Three new tests pass before their code exists, which contradicts the Step 2 expectations, and no deliberate break covers them. `test_docs_paths_without_a_path_is_a_usage_error` already gets exit 2, because today's `main` rejects any single argument. `test_usage_errors_write_nothing` already gets exit 2, because an unknown command falls through to `usage()`. `test_lock_timeout_writes_nothing` passes as soon as Task 1 exists. | `plugins/my/bin/git-fold-fixups.py:274-275`; `plugins/my/bin/handoff-state.py:282`; plan Task 2 Step 2, Task 3 Step 2 | Name these three in Step 2 as "pass before and after", and give each a deliberate break. For example, make `start` accept `--max 0`, or run `start` before the lock is taken. |

## Dual-Perspective Analysis

**Arguments this is sound:**

| Aspect | Evidence | Strength |
|---|---|---|
| Grounding | Every line reference, lint count and fixture helper checked above holds. The reference sweep matches the file map (`git grep` output; `plugins/my/tests/test_handoff_state.py:70-112`). | Strong |
| Spec coverage | Each D1 to D8 decision, the six stop rows (numbered 18 to 23 in spec order) and every Files row map to a task. The review-3 open items are settled in Decisions 5, 6 and 7 (spec `:62-259`, `docs/plans/2026-10-12-parallel-auto-runs-spec-review-3.md:82-83`). | Strong |
| Test-first order | Tasks 1 to 4 each state a red step with its expected failure. Tasks 2 and 5 name a deliberate break for the tests that never go red. The Task 5 break, comparing against the base tip, does make `merge("b")` succeed, so the assertion would fail. | Strong |
| Merge safety | The `merge` order of work refuses on staged changes, a missing `checked_base` or a moved base before it writes anything. `git reset --merge` cleans a conflicted squash fully (probe). Task 4 pins each case, including a failing pre-commit hook (`plugins/my/tests/test_handoff_state.py:84-90`: hooks are not overridden in the fixture). | Strong |
| Scope | It adds one script and extends two. The prose changes are all conditioned on "With a Parallel runs section", so a project without the section reads as before (Task 7 preamble). | Moderate |

**Arguments this has problems:**

| Aspect | Evidence | Severity |
|---|---|---|
| Snippet logic | The lock test's holder leaks the lock to a forked child under dash (probe). | Medium |
| Snippet logic | `git grep -h` cannot produce the file name the refusal must print (probe). | Medium |
| Completeness | The integration test never sets `branch`, so `merge` refuses (plan Task 5 vs Decision 5). | Medium |
| Runbook | The rehearsal's first tmux command fails without a server (probe). | Medium |
| Contracts | The locked commit form breaks on ordinary commit messages (spec `:154`, `commit.md:15`). | Medium |
| Spec fidelity | Decision 7 drops D7's guarantee for supervised merges without asking (spec `:204-207`). | Medium |
| Test strength | `squash_subject` written by `merge` is not pinned (`test_handoff_state.py:99-103`). | Low |

## Not Applicable

None.

## Needs Investigation

- **D2's claim that "the kernel frees the lock when the command ends or dies"** holds only when no child outlives the command. The Task 1 probe shows that killing a shell leaves its forked child holding the lock. The spec's Risk names background processes, but not a killed parent whose foreground child is still running, for example a test runner under `sh -c`. A one-paragraph note in the Risk section, or a process-group kill in the shared-resource guidance, would settle it. I did not check how Claude Code's Bash tool ends a timed-out command: whether it kills the whole process group.
- **What the user does when D6 refuses a waiting fixup's fold** in a project without the section. The run stops at row 17. The `done` facts then report `fixup waits` for as long as the fixup stays (`plugins/my/bin/handoff-state.py:213-215`), and neither the spec nor the plan names a way out, such as reverting the fixup and making a normal commit. This does not affect this branch: no commit after this spec's target is cited in the docs today (a scratchpad scan of `docs/`, `ROADMAP.md` and `CHANGELOG.md` at `HEAD`). The general way out needs a line from the author.
- **Decision 2's version claim** ("Git 2.43 reads only the first key; newer git reads the second"). I could check only git 2.43.0 here. Setting both keys is harmless either way.

## Reasoning

The plan is complete in structure. It covers every spec decision, settles the third spec review's open items, and its references hold against the repo. The test-first sequence is sound. The surfaced Warnings all sit inside snippets and runbook lines, and three of them are confirmed by probes in the scratchpad. A cold executor would hit each one and have to redesign on the spot: the lock test's holder, the `git grep -h` file name, the unset `branch` in the integration test, and the tmux command. Two Warnings need the user. One is D4's quoting, which is spec text. The other is Decision 7's narrowing of D7, which the plan presents as not changing a decision. No finding questions the approach itself.

## Verdict

**Assessment:** Mixed
**Confidence:** High. The four snippet and runbook failures were reproduced in the scratchpad or read directly from the repo, and the spec-fidelity finding rests on spec D7's own wording.
**Recommendation:** Fix the four snippet and runbook findings in the plan: the holder `exec`, dropping `-h`, `set branch=` in `build`, and the tmux `new-session`. Pin `squash_subject` with an empty value in `ready()`. Then ask the user two questions before the code stage: (1) keep D4's form, or pass the message as an argument; (2) keep Decision 7's auto-only D7, with a Risk entry, or run `merge` for supervised runs too.
